"""
Shared utility functions for database models
Prevents circular import issues between model files
"""
import uuid
import os
from sqlalchemy import String


def get_uuid_column():
    """Get appropriate UUID column type based on database"""
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url.startswith("sqlite") or not database_url:
        return String(36)
    else:
        from sqlalchemy.dialects.postgresql import UUID
        return UUID(as_uuid=True)


def default_uuid():
    """Generate default UUID as string for compatibility"""
    return str(uuid.uuid4())


def ensure_uuid_string():
    """Helper function to ensure UUID values are strings for SQLite"""
    return lambda: str(uuid.uuid4())
