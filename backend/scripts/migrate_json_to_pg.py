"""
Migração única: JSON files → PostgreSQL

Execução:
    python scripts/migrate_json_to_pg.py

Pré-requisitos:
    DATABASE_URL configurado no .env
    Tabelas criadas: alembic upgrade head
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv("../.env")

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def migrate_users():
    from db.engine import AsyncSessionLocal
    from db.models import UserModel
    from sqlalchemy import select

    users_file = Path("../dados/users.json")
    if not users_file.exists():
        logger.info("dados/users.json not found — skipping users migration")
        return

    try:
        data = json.loads(users_file.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            logger.warning("users.json format unexpected — skipping")
            return
    except Exception as e:
        logger.warning(f"Could not read users.json: {e}")
        return

    async with AsyncSessionLocal() as session:
        migrated = 0
        for u in data:
            username = u.get("username")
            if not username:
                continue
            existing = await session.execute(
                select(UserModel).where(UserModel.username == username)
            )
            if existing.scalar_one_or_none():
                logger.info(f"  User '{username}' already exists — skipping")
                continue
            user = UserModel(
                id=u.get("id", str(__import__("uuid").uuid4())),
                username=username,
                email=u.get("email"),
                hashed_password=u.get("hashed_password", u.get("password", "")),
                role=u.get("role", "user"),
                is_active=u.get("is_active", True),
            )
            session.add(user)
            migrated += 1
        await session.commit()
        logger.info(f"✅ Users migrated: {migrated}")


async def migrate_registry():
    from db.engine import AsyncSessionLocal
    from db.models import DataSourceModel
    from sqlalchemy import select

    registry_file = Path("../dados/catalog/registry.json")
    if not registry_file.exists():
        logger.info("catalog/registry.json not found — skipping sources migration")
        return

    try:
        data = json.loads(registry_file.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"Could not read registry.json: {e}")
        return

    async with AsyncSessionLocal() as session:
        migrated = 0
        for source_id, record in data.items():
            existing = await session.execute(
                select(DataSourceModel).where(DataSourceModel.id == source_id)
            )
            if existing.scalar_one_or_none():
                logger.info(f"  Source '{record.get('name')}' already exists — skipping")
                continue

            # Serialize config (without passwords)
            cfg = {
                k: "***" if any(s in k.lower() for s in ("password", "secret", "token", "key"))
                else v
                for k, v in (record.get("config") or {}).items()
            }

            source = DataSourceModel(
                id=source_id,
                name=record.get("name", "Unknown"),
                connector_type=record.get("connector_type", "csv"),
                config_encrypted=json.dumps(cfg),
                owner_id=None,
                description=record.get("description"),
                status=record.get("status", "registered"),
                datasets_json=record.get("datasets", []),
                domain_summary_json=record.get("domain_summary", {}),
                error_message=record.get("error_message"),
                tags=record.get("tags", []),
            )
            session.add(source)
            migrated += 1
        await session.commit()
        logger.info(f"✅ Data sources migrated: {migrated}")


async def migrate_alerts():
    from db.engine import AsyncSessionLocal
    from db.models import AlertModel

    alerts_file = Path("../dados/alerts/alerts.jsonl")
    if not alerts_file.exists():
        logger.info("alerts/alerts.jsonl not found — skipping alerts migration")
        return

    lines = alerts_file.read_text(encoding="utf-8").strip().splitlines()
    async with AsyncSessionLocal() as session:
        migrated = 0
        for line in lines:
            try:
                a = json.loads(line)
            except Exception:
                continue
            alert = AlertModel(
                source_id=a.get("source_id"),
                source_name=a.get("source_name", "Unknown"),
                severity=a.get("severity", "info"),
                title=a.get("title", "Alert"),
                message=a.get("message", ""),
                details_json=a.get("details", {}),
                trigger=a.get("trigger", "system"),
            )
            session.add(alert)
            migrated += 1
        await session.commit()
        logger.info(f"✅ Alerts migrated: {migrated}")


async def main():
    logger.info("🚀 Starting JSON → PostgreSQL migration...")
    await migrate_users()
    await migrate_registry()
    await migrate_alerts()
    logger.info("✅ Migration complete.")


if __name__ == "__main__":
    asyncio.run(main())
