"""Add daily sheet attendance reporting models

Revision ID: 002_daily_sheet_models
Revises: 001_initial_schema
Create Date: 2025-08-18 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_daily_sheet_models'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None

def get_uuid_column():
    """Helper to determine UUID column type based on database"""
    import os
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url.startswith("sqlite") or not database_url:
        return sa.String(36)
    else:
        return postgresql.UUID(as_uuid=True)

def upgrade():
    """Add the daily sheet attendance reporting models"""
    
    # Create project_attendance_reporting table
    op.create_table('project_attendance_reporting',
        sa.Column('id', get_uuid_column(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('project_id', get_uuid_column(), nullable=False),
        sa.Column('shift_id', get_uuid_column(), nullable=True),
        sa.Column('group_no', sa.Integer(), nullable=False, default=1),
        sa.Column('seq_no', sa.Integer(), nullable=False, default=1),
        sa.Column('employee_id', get_uuid_column(), nullable=True),
        sa.Column('substitute_employee_id', get_uuid_column(), nullable=True),
        sa.Column('dog_id', get_uuid_column(), nullable=True),
        sa.Column('check_in_time', sa.Time(), nullable=True),
        sa.Column('check_out_time', sa.Time(), nullable=True),
        sa.Column('status', sa.Enum('PRESENT', 'ABSENT', 'LATE', 'SICK', 'LEAVE', 'REMOTE', 'OVERTIME', name='attendancestatus'), nullable=False, default='PRESENT'),
        sa.Column('is_project_controlled', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dog_id'], ['dog.id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employee.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.ForeignKeyConstraint(['shift_id'], ['project_shift.id'], ),
        sa.ForeignKeyConstraint(['substitute_employee_id'], ['employee.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'date', 'group_no', 'seq_no', name='uq_attendance_print_slot')
    )
    
    # Create indexes for project_attendance_reporting
    op.create_index('ix_attendance_date', 'project_attendance_reporting', ['date'])
    op.create_index('ix_attendance_project_date', 'project_attendance_reporting', ['project_id', 'date'])
    op.create_index('ix_attendance_group_seq', 'project_attendance_reporting', ['project_id', 'date', 'group_no', 'seq_no'])
    
    # Create attendance_day_leave table
    op.create_table('attendance_day_leave',
        sa.Column('id', get_uuid_column(), nullable=False),
        sa.Column('project_id', get_uuid_column(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('seq_no', sa.Integer(), nullable=False, default=1),
        sa.Column('employee_id', get_uuid_column(), nullable=True),
        sa.Column('leave_type', sa.Enum('ANNUAL', 'SICK', 'EMERGENCY', 'OTHER', name='leavetype'), nullable=False),
        sa.Column('note', sa.String(length=250), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employee.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'date', 'seq_no', name='uq_dayleave_print_slot')
    )
    
    # Create indexes for attendance_day_leave
    op.create_index('ix_dayleave_date', 'attendance_day_leave', ['date'])
    op.create_index('ix_dayleave_project_date', 'attendance_day_leave', ['project_id', 'date'])


def downgrade():
    """Remove the daily sheet attendance reporting models"""
    
    # Drop indexes for attendance_day_leave
    op.drop_index('ix_dayleave_project_date', table_name='attendance_day_leave')
    op.drop_index('ix_dayleave_date', table_name='attendance_day_leave')
    
    # Drop attendance_day_leave table
    op.drop_table('attendance_day_leave')
    
    # Drop indexes for project_attendance_reporting
    op.drop_index('ix_attendance_group_seq', table_name='project_attendance_reporting')
    op.drop_index('ix_attendance_project_date', table_name='project_attendance_reporting')
    op.drop_index('ix_attendance_date', table_name='project_attendance_reporting')
    
    # Drop project_attendance_reporting table
    op.drop_table('project_attendance_reporting')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS leavetype')
    op.execute('DROP TYPE IF EXISTS attendancestatus')