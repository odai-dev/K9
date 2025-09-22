"""Add SECURITY_EVENT to AuditAction enum

Revision ID: 5a09bed29e63
Revises: b16faad59eea
Create Date: 2025-09-22 14:31:35.983058

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a09bed29e63'
down_revision = 'b16faad59eea'
branch_labels = None
depends_on = None


def upgrade():
    # Add SECURITY_EVENT to the auditaction enum
    op.execute("ALTER TYPE auditaction ADD VALUE 'SECURITY_EVENT'")


def downgrade():
    # Note: PostgreSQL doesn't support removing enum values
    # If rollback is needed, the enum would need to be recreated
    pass
