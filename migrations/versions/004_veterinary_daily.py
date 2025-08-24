"""Add veterinary daily report fields

Revision ID: 004_veterinary_daily
Revises: 003_trainer_daily_indexes
Create Date: 2025-08-24 22:08:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_veterinary_daily'
down_revision = '003_trainer_daily_indexes'
branch_labels = None
depends_on = None

def upgrade():
    # Add new fields to veterinary_visit table
    op.add_column('veterinary_visit', sa.Column('location', sa.String(120), nullable=True))
    op.add_column('veterinary_visit', sa.Column('weather', sa.String(80), nullable=True))
    op.add_column('veterinary_visit', sa.Column('vital_signs', sa.JSON(), nullable=True))
    
    # Add indexes for better query performance
    op.create_index('ix_veterinary_visit_project_date', 'veterinary_visit', ['project_id', 'visit_date'])
    op.create_index('ix_veterinary_visit_dog_date', 'veterinary_visit', ['dog_id', 'visit_date'])

def downgrade():
    # Remove indexes
    op.drop_index('ix_veterinary_visit_dog_date', table_name='veterinary_visit')
    op.drop_index('ix_veterinary_visit_project_date', table_name='veterinary_visit')
    
    # Remove columns
    op.drop_column('veterinary_visit', 'vital_signs')
    op.drop_column('veterinary_visit', 'weather')
    op.drop_column('veterinary_visit', 'location')