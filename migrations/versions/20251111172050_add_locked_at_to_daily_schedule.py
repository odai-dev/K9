"""add locked_at to daily_schedule

Revision ID: 20251111172050
Revises: 20251111165022
Create Date: 2025-11-11 17:20:50.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '20251111172050'
down_revision = '20251111165022'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('daily_schedule', 
                  sa.Column('locked_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('daily_schedule', 'locked_at')
