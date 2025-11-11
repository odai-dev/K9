"""add location_id to daily_schedule_item

Revision ID: 20251111165022
Revises: 20251110200957
Create Date: 2025-11-11 16:50:22.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251111165022'
down_revision = '20251110200957'
branch_labels = None
depends_on = None


def upgrade():
    # Add location_id column (nullable FK to project_location)
    op.add_column('daily_schedule_item', 
                  sa.Column('location_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_daily_schedule_item_location_id', 
                         'daily_schedule_item', 'project_location',
                         ['location_id'], ['id'])


def downgrade():
    # Remove foreign key and column
    op.drop_constraint('fk_daily_schedule_item_location_id', 'daily_schedule_item', type_='foreignkey')
    op.drop_column('daily_schedule_item', 'location_id')
