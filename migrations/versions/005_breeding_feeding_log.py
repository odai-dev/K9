"""Add breeding feeding log models

Revision ID: 005_breeding_feeding_log
Revises: 20250818_pm_daily
Create Date: 2025-08-25 15:41:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os

# revision identifiers, used by Alembic.
revision = '005_breeding_feeding_log'
down_revision = '20250818_pm_daily'
branch_labels = None
depends_on = None

def is_sqlite():
    """Check if we're using SQLite"""
    database_url = os.environ.get("DATABASE_URL", "")
    return not database_url or database_url.startswith("sqlite")

def upgrade():
    # Create enums for PostgreSQL or handle as VARCHAR for SQLite
    if not is_sqlite():
        # PostgreSQL enums with Arabic values
        prep_method_enum = postgresql.ENUM(
            'غليان', 'تبخير', 'نقع', 'أخرى',
            name='prepmethod',
            create_type=False
        )
        op.execute('CREATE TYPE prepmethod AS ENUM (\'غليان\', \'تبخير\', \'نقع\', \'أخرى\')')
        
        body_condition_enum = postgresql.ENUM(
            'نحيف جدًا (1)', 'نحيف (2)', 'أقل من المثالي (3)', 'قريب من المثالي (4)', 
            'مثالي (5)', 'فوق المثالي (6)', 'ممتلئ (7)', 'سمين (8)', 'سمين جدًا (9)',
            name='bodyconditionscale',
            create_type=False
        )
        op.execute('''CREATE TYPE bodyconditionscale AS ENUM (
            'نحيف جدًا (1)', 'نحيف (2)', 'أقل من المثالي (3)', 'قريب من المثالي (4)', 
            'مثالي (5)', 'فوق المثالي (6)', 'ممتلئ (7)', 'سمين (8)', 'سمين جدًا (9)'
        )''')
    
    # Determine UUID column type
    if is_sqlite():
        uuid_column = sa.String(36)
    else:
        uuid_column = postgresql.UUID(as_uuid=True)
    
    # Create feeding_log table
    op.create_table('feeding_log',
        sa.Column('id', uuid_column, nullable=False),
        sa.Column('project_id', uuid_column, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('time', sa.Time(), nullable=False),
        sa.Column('dog_id', uuid_column, nullable=False),
        sa.Column('recorder_employee_id', uuid_column, nullable=True),
        sa.Column('meal_type_fresh', sa.Boolean(), nullable=False, default=False),
        sa.Column('meal_type_dry', sa.Boolean(), nullable=False, default=False),
        sa.Column('meal_name', sa.String(length=120), nullable=True),
        sa.Column('prep_method', 
                  prep_method_enum if not is_sqlite() else sa.String(50), 
                  nullable=True),
        sa.Column('grams', sa.Integer(), nullable=True),
        sa.Column('water_ml', sa.Integer(), nullable=True),
        sa.Column('supplements', sa.JSON(), nullable=True),
        sa.Column('body_condition', 
                  body_condition_enum if not is_sqlite() else sa.String(50), 
                  nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add foreign key constraints
    op.create_foreign_key(None, 'feeding_log', 'project', ['project_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'feeding_log', 'dog', ['dog_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'feeding_log', 'employee', ['recorder_employee_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(None, 'feeding_log', 'user', ['created_by_user_id'], ['id'], ondelete='SET NULL')
    
    # Create indexes for better query performance
    op.create_index('ix_feeding_log_project_date', 'feeding_log', ['project_id', 'date'])
    op.create_index('ix_feeding_log_dog_datetime', 'feeding_log', ['dog_id', 'date', 'time'])

def downgrade():
    # Remove indexes
    op.drop_index('ix_feeding_log_dog_datetime', table_name='feeding_log')
    op.drop_index('ix_feeding_log_project_date', table_name='feeding_log')
    
    # Drop table
    op.drop_table('feeding_log')
    
    # Drop enums for PostgreSQL
    if not is_sqlite():
        op.execute('DROP TYPE IF EXISTS bodyconditionscale')
        op.execute('DROP TYPE IF EXISTS prepmethod')