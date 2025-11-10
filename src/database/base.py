"""
SQLAlchemy base configuration and utilities.

Provides:
- Base declarative class for all models
- Naming conventions for database constraints
- Mixin classes for common functionality (timestamps, soft deletes, audit)
"""

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Integer, MetaData
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base


# Naming convention for database constraints
# This ensures consistent naming across migrations and makes debugging easier
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)


class TimestampMixin:
    """
    Mixin to add created_at and updated_at timestamps to models.

    Automatically tracks when records are created and last modified.
    All timestamps are stored in UTC.
    """

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class SoftDeleteMixin:
    """
    Mixin to add soft delete functionality.

    Instead of actually deleting records, we mark them as deleted.
    This preserves data lineage and allows for audit trails.
    """

    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)

    def soft_delete(self) -> None:
        """Mark this record as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin(TimestampMixin, SoftDeleteMixin):
    """
    Combines timestamp and soft delete functionality for complete audit trail.

    Use this mixin for tables where you need:
    - Creation timestamp
    - Last update timestamp
    - Soft delete capability
    - Deletion timestamp
    """

    pass
