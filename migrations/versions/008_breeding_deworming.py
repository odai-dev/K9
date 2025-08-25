"""Add DewormingLog model with Arabic enums for breeding deworming feature

Revision ID: 008_breeding_deworming
Revises: 007_breeding_grooming
Create Date: 2025-08-25 20:02:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import os


# revision identifiers
revision = '008_breeding_deworming'
down_revision = '007_breeding_grooming'
depends_on = None


def is_sqlite():
    """Check if we're using SQLite"""
    database_url = os.environ.get('DATABASE_URL', '')
    return not database_url or database_url.startswith('sqlite')


def upgrade():
    """Create deworming_log table"""
    
    # Use String for all databases for simplicity and SQLite compatibility
    if not is_sqlite():
        uuid_col = UUID(as_uuid=True)
    else:
        uuid_col = sa.String(36)
    
    # Use String for enum fields for SQLite compatibility  
    route_type = sa.String(20)
    unit_type = sa.String(20)
    reaction_type = sa.String(20)
    
    # Create deworming_log table
    op.create_table('deworming_log',
        sa.Column('id', uuid_col, nullable=False),
        sa.Column('project_id', uuid_col, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('time', sa.Time(), nullable=False),
        sa.Column('dog_id', uuid_col, nullable=False),
        sa.Column('specialist_employee_id', uuid_col, nullable=True),
        sa.Column('dog_weight_kg', sa.Float(), nullable=True),
        sa.Column('product_name', sa.String(length=120), nullable=True),
        sa.Column('active_ingredient', sa.String(length=120), nullable=True),
        sa.Column('standard_dose_mg_per_kg', sa.Float(), nullable=True),
        sa.Column('calculated_dose_mg', sa.Float(), nullable=True),
        sa.Column('administered_amount', sa.Float(), nullable=True),
        sa.Column('amount_unit', unit_type, nullable=True),
        sa.Column('administration_route', route_type, nullable=True),
        sa.Column('batch_number', sa.String(length=60), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('adverse_reaction', reaction_type, nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('next_due_date', sa.Date(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['dog_id'], ['dog.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['specialist_employee_id'], ['employee.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'dog_id', 'date', 'time', name='uq_deworming_project_dog_dt')
    )
    
    # Create indexes
    op.create_index('ix_deworming_project_date', 'deworming_log', ['project_id', 'date'])
    op.create_index('ix_deworming_dog_datetime', 'deworming_log', ['dog_id', 'date', 'time'])


def downgrade():
    """Drop deworming_log table"""
    
    # Drop indexes
    op.drop_index('ix_deworming_dog_datetime', table_name='deworming_log')
    op.drop_index('ix_deworming_project_date', table_name='deworming_log')
    
    # Drop table
    op.drop_table('deworming_log')