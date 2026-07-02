"""
SQLAlchemy ORM models — replaces JSON file persistence.

Tables:
  users           — auth (replaces dados/users.json)
  data_sources    — catalog registry (replaces dados/catalog/registry.json)
  alerts          — agent actions log (replaces dados/alerts/alerts.jsonl)
"""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.types import JSON


def _json_col():
    """Use JSONB on PostgreSQL, JSON on SQLite."""
    try:
        from sqlalchemy.dialects.postgresql import JSONB as _JSONB
        return _JSONB
    except ImportError:
        return JSON


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Any = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Users
# ──────────────────────────────────────────────────────────────────────────────

class UserModel(TimestampMixin, Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(256), unique=True, nullable=True)
    hashed_password = Column(String(256), nullable=False)
    role = Column(String(32), default="user", nullable=False)  # admin | user | viewer
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    # ── Plan / Quota ──────────────────────────────────────────
    plan = Column(String(32), default="free", nullable=False)  # free | premium | enterprise
    plan_expires_at = Column(DateTime(timezone=True), nullable=True)
    llm_quota_monthly = Column(Integer, default=100, nullable=False)
    llm_quota_used = Column(Integer, default=0, nullable=False)
    quota_reset_at = Column(DateTime(timezone=True), nullable=True)


# ──────────────────────────────────────────────────────────────────────────────
# Data Sources
# ──────────────────────────────────────────────────────────────────────────────

class DataSourceModel(TimestampMixin, Base):
    __tablename__ = "data_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(256), nullable=False)
    connector_type = Column(String(64), nullable=False)
    # Config stored encrypted (passwords never plain text)
    config_encrypted = Column(Text, nullable=False, default="{}")
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(32), default="registered", nullable=False)
    # Discovered schema + domain classification
    datasets_json = Column(JSON, default=list, nullable=False)
    domain_summary_json = Column(JSON, default=dict, nullable=False)
    error_message = Column(Text, nullable=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    tags = Column(JSON, default=list, nullable=False)

    owner = relationship("UserModel", backref="data_sources", lazy="select")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "connector_type": self.connector_type,
            "owner_id": self.owner_id,
            "description": self.description,
            "status": self.status,
            "datasets": self.datasets_json or [],
            "domain_summary": self.domain_summary_json or {},
            "error_message": self.error_message,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": self.tags or [],
            "config": {},  # Never expose config in API responses
        }


# ──────────────────────────────────────────────────────────────────────────────
# Alerts
# ──────────────────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────────────────
# User Preferences (per-user LLM settings)
# ──────────────────────────────────────────────────────────────────────────────

class UserPreferenceModel(Base):
    __tablename__ = "user_preferences"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    active_provider = Column(String(32), default="auto", nullable=False)  # auto|anthropic|openai|opencode|zai
    active_model = Column(String(128), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("UserModel", backref="preference", lazy="select")


# ──────────────────────────────────────────────────────────────────────────────
# Alerts
# ──────────────────────────────────────────────────────────────────────────────

class AlertModel(TimestampMixin, Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True)
    source_name = Column(String(256), nullable=False)
    severity = Column(String(32), default="info", nullable=False)  # info | warning | critical
    title = Column(String(512), nullable=False)
    message = Column(Text, nullable=False)
    details_json = Column(JSON, default=dict, nullable=False)
    trigger = Column(String(64), default="system", nullable=False)  # system | user | anomaly
    acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by = Column(String(64), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "details": self.details_json or {},
            "trigger": self.trigger,
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
