"""
Quota tracking — increments LLM usage counter per user.

In production with PostgreSQL, uses the database.
In dev with SQLite, also uses the database (auto-created).
Falls back to JSON file if DB is unavailable.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


async def check_and_increment_quota(user_id: str, plan: str = "free") -> bool:
    """
    Checks if user has remaining quota and increments the counter.
    Returns True if quota is available, False if exhausted.
    """
    if not user_id:
        return True  # No user context, allow

    try:
        from db.engine import AsyncSessionLocal
        from db.models import UserModel
        from sqlalchemy import select, update
        from core.plan_config import get_quota

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return True  # User not in DB, allow

            # Reset quota if it's a new month
            now = datetime.now(timezone.utc)
            if user.quota_reset_at:
                # If quota_reset_at is from a previous month, reset
                if user.quota_reset_at.month != now.month or user.quota_reset_at.year != now.year:
                    user.llm_quota_used = 0
                    user.quota_reset_at = now
            else:
                user.quota_reset_at = now

            monthly_quota = user.llm_quota_monthly or get_quota(plan)
            if user.llm_quota_used >= monthly_quota:
                logger.warning(f"Quota exhausted for user {user_id}: {user.llm_quota_used}/{monthly_quota}")
                return False

            user.llm_quota_used += 1
            await session.commit()
            return True

    except Exception as e:
        logger.debug(f"Quota check failed (non-fatal, allowing): {e}")
        return True  # Fail open — don't block on quota errors


async def get_quota_status(user_id: str) -> dict:
    """Returns current quota status for a user."""
    try:
        from db.engine import AsyncSessionLocal
        from db.models import UserModel
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return {"used": 0, "monthly": 100, "remaining": 100}

            return {
                "used": user.llm_quota_used or 0,
                "monthly": user.llm_quota_monthly or 100,
                "remaining": max(0, (user.llm_quota_monthly or 100) - (user.llm_quota_used or 0)),
            }
    except Exception as e:
        logger.debug(f"Could not get quota status: {e}")
        return {"used": 0, "monthly": 100, "remaining": 100}
