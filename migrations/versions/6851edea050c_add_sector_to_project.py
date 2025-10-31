"""add_sector_to_project

Revision ID: 6851edea050c
Revises: ed019aa6ac52
Create Date: 2025-10-31 03:43:57.182107

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6851edea050c'
down_revision = 'ed019aa6ac52'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('project', sa.Column('sector', sa.String(length=100), nullable=True))


def downgrade():
    op.drop_column('project', 'sector')
