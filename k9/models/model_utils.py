"""
Shared utility functions for database models
Prevents circular import issues between model files
"""
import uuid
from sqlalchemy.dialects.postgresql import UUID


def get_uuid_column():
    """Get PostgreSQL native UUID column type."""
    return UUID(as_uuid=True)


def default_uuid():
    """Generate default UUID as string for compatibility"""
    return str(uuid.uuid4())


def ensure_uuid_string():
    """Helper function to ensure UUID values are strings for SQLite"""
    return lambda: str(uuid.uuid4())
