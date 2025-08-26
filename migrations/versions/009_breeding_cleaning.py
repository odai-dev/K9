"""Add cleaning log table for breeding hygiene tracking

Revision ID: 009_breeding_cleaning  
Revises: 008_breeding_deworming
Create Date: 2025-08-26 14:54:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os

# revision identifiers, used by Alembic.
revision = '009_breeding_cleaning'
down_revision = '008_breeding_deworming'
branch_labels = None
depends_on = None

def get_uuid_column():
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url.startswith("sqlite") or not database_url:
        return sa.String(36)
    else:
        return postgresql.UUID(as_uuid=True)

def upgrade():
    # Create cleaning_log table
    op.create_table('cleaning_log',
        sa.Column('id', get_uuid_column(), nullable=False),
        sa.Column('project_id', get_uuid_column(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('time', sa.Time(), nullable=False),
        sa.Column('dog_id', get_uuid_column(), nullable=False),
        sa.Column('recorder_employee_id', get_uuid_column(), nullable=True),
        
        # Target area info (using ASCII column names)
        sa.Column('area_type', sa.String(50), nullable=True),
        sa.Column('cage_house_number', sa.String(60), nullable=True),
        sa.Column('alternate_place', sa.String(120), nullable=True),
        
        # Actions (using ASCII column names)
        sa.Column('cleaned_house', sa.String(10), nullable=True),
        sa.Column('washed_house', sa.String(10), nullable=True),
        sa.Column('disinfected_house', sa.String(10), nullable=True),
        sa.Column('group_disinfection', sa.String(10), nullable=True),
        sa.Column('group_description', sa.String(120), nullable=True),
        
        # Materials and notes
        sa.Column('materials_used', postgresql.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        
        # Audit fields
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['dog_id'], ['dog.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recorder_employee_id'], ['employee.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['user.id'], ondelete='SET NULL'),
        
        # Indexes
        sa.Index('ix_cleaning_project_date', 'project_id', 'date'),
        sa.Index('ix_cleaning_dog_datetime', 'dog_id', 'date', 'time'),
        
        # Unique constraint
        sa.UniqueConstraint('project_id', 'dog_id', 'date', 'time', name='uq_cleaning_project_dog_dt')
    )

def downgrade():
    # Drop the cleaning_log table and its indexes/constraints
    op.drop_table('cleaning_log')