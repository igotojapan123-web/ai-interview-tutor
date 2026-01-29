"""
Base model classes with common functionality.
"""

from datetime import datetime
from typing import Optional, Any, Dict
from uuid import uuid4

from pydantic import BaseModel as PydanticBaseModel, Field, ConfigDict


def generate_uuid() -> str:
    """Generate a unique identifier."""
    return str(uuid4())


def get_current_timestamp() -> datetime:
    """Get current UTC timestamp."""
    return datetime.utcnow()


class BaseModel(PydanticBaseModel):
    """
    Base model with common configuration.

    All domain models should inherit from this class.
    """

    model_config = ConfigDict(
        from_attributes=True,  # Allow ORM mode
        populate_by_name=True,  # Allow population by field name or alias
        validate_assignment=True,  # Validate on assignment
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
        }
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump(mode="json", exclude_none=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """Create model from dictionary."""
        return cls.model_validate(data)


class TimestampMixin(BaseModel):
    """Mixin for models that need timestamp tracking."""

    created_at: datetime = Field(default_factory=get_current_timestamp)
    updated_at: datetime = Field(default_factory=get_current_timestamp)

    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = get_current_timestamp()


class IdentifiableMixin(BaseModel):
    """Mixin for models that need unique identification."""

    id: str = Field(default_factory=generate_uuid)


class AuditMixin(TimestampMixin):
    """Mixin for models that need audit tracking."""

    created_by: Optional[str] = Field(default=None, description="User ID who created")
    updated_by: Optional[str] = Field(default=None, description="User ID who last updated")


class SoftDeleteMixin(BaseModel):
    """Mixin for models that support soft delete."""

    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = Field(default=None)
    deleted_by: Optional[str] = Field(default=None)

    def soft_delete(self, deleted_by: Optional[str] = None) -> None:
        """Mark the record as deleted."""
        self.is_deleted = True
        self.deleted_at = get_current_timestamp()
        self.deleted_by = deleted_by

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None


class Entity(IdentifiableMixin, TimestampMixin):
    """
    Base entity class with ID and timestamps.

    Use this as the base for all domain entities.
    """
    pass


class AggregateRoot(Entity, AuditMixin):
    """
    Base class for aggregate roots.

    Aggregate roots are the main entry points for domain operations
    and ensure consistency within the aggregate boundary.
    """

    version: int = Field(default=1, description="Optimistic locking version")

    def increment_version(self) -> None:
        """Increment version for optimistic locking."""
        self.version += 1
