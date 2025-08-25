"""Add breeding daily checkup models

Revision ID: 006_breeding_daily_checkup
Revises: 005_breeding_feeding_log
Create Date: 2025-08-25 16:27:30.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os

# revision identifiers, used by Alembic.
revision = '006_breeding_daily_checkup'
down_revision = '005_breeding_feeding_log'
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
        part_status_enum = postgresql.ENUM(
            'سليم', 'احمرار', 'التهاب', 'إفرازات', 'تورم', 'جرح', 'ألم', 'أخرى',
            name='partstatus',
            create_type=False
        )
        op.execute('CREATE TYPE partstatus AS ENUM (\'سليم\', \'احمرار\', \'التهاب\', \'إفرازات\', \'تورم\', \'جرح\', \'ألم\', \'أخرى\')')
        
        severity_enum = postgresql.ENUM(
            'خفيف', 'متوسط', 'شديد',
            name='severity',
            create_type=False
        )
        op.execute('CREATE TYPE severity AS ENUM (\'خفيف\', \'متوسط\', \'شديد\')')
    
    # Determine UUID column type
    if is_sqlite():
        uuid_column = sa.String(36)
    else:
        uuid_column = postgresql.UUID(as_uuid=True)
    
    # Create daily_checkup_log table
    op.create_table('daily_checkup_log',
        sa.Column('id', uuid_column, nullable=False),
        sa.Column('project_id', uuid_column, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('time', sa.Time(), nullable=False),
        sa.Column('dog_id', uuid_column, nullable=False),
        sa.Column('examiner_employee_id', uuid_column, nullable=True),
        
        # Body parts with PartStatus enum
        sa.Column('العين', 
                  part_status_enum if not is_sqlite() else sa.String(50), 
                  nullable=True),
        sa.Column('الأذن', 
                  part_status_enum if not is_sqlite() else sa.String(50), 
                  nullable=True),
        sa.Column('الأنف', 
                  part_status_enum if not is_sqlite() else sa.String(50), 
                  nullable=True),
        sa.Column('الأطراف_الأمامية', 
                  part_status_enum if not is_sqlite() else sa.String(50), 
                  nullable=True),
        sa.Column('الأطراف_الخلفية', 
                  part_status_enum if not is_sqlite() else sa.String(50), 
                  nullable=True),
        sa.Column('الشعر', 
                  part_status_enum if not is_sqlite() else sa.String(50), 
                  nullable=True),
        sa.Column('الذيل', 
                  part_status_enum if not is_sqlite() else sa.String(50), 
                  nullable=True),
        
        sa.Column('شدة_الحالة', 
                  severity_enum if not is_sqlite() else sa.String(50), 
                  nullable=True),
        sa.Column('أعراض', sa.Text(), nullable=True),
        sa.Column('تشخيص_أولي', sa.Text(), nullable=True),
        sa.Column('علاج_مقترح', sa.Text(), nullable=True),
        sa.Column('ملاحظات', sa.Text(), nullable=True),
        
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add foreign key constraints
    op.create_foreign_key(None, 'daily_checkup_log', 'project', ['project_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'daily_checkup_log', 'dog', ['dog_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'daily_checkup_log', 'employee', ['examiner_employee_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(None, 'daily_checkup_log', 'user', ['created_by_user_id'], ['id'], ondelete='SET NULL')
    
    # Create indexes for better query performance
    op.create_index('ix_checkup_project_date', 'daily_checkup_log', ['project_id', 'date'])
    op.create_index('ix_checkup_dog_datetime', 'daily_checkup_log', ['dog_id', 'date', 'time'])
    
    # Create unique constraint
    op.create_unique_constraint('uq_checkup_project_dog_dt', 'daily_checkup_log', ['project_id', 'dog_id', 'date', 'time'])

def downgrade():
    # Remove unique constraint
    op.drop_constraint('uq_checkup_project_dog_dt', 'daily_checkup_log', type_='unique')
    
    # Remove indexes
    op.drop_index('ix_checkup_dog_datetime', table_name='daily_checkup_log')
    op.drop_index('ix_checkup_project_date', table_name='daily_checkup_log')
    
    # Drop table
    op.drop_table('daily_checkup_log')
    
    # Drop enums for PostgreSQL
    if not is_sqlite():
        op.execute('DROP TYPE IF EXISTS severity')
        op.execute('DROP TYPE IF EXISTS partstatus')