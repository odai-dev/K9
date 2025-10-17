"""add_duration_days_to_breeding_training_activity

Revision ID: d358706479f9
Revises: 5a793c6878a3
Create Date: 2025-10-17 18:16:44.524267

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd358706479f9'
down_revision = '5a793c6878a3'
branch_labels = None
depends_on = None


def upgrade():
    # Add duration_days column to breeding_training_activity table
    op.add_column('breeding_training_activity', sa.Column('duration_days', sa.Integer(), nullable=True))


def downgrade():
    # Remove duration_days column from breeding_training_activity table
    op.drop_column('breeding_training_activity', 'duration_days')
