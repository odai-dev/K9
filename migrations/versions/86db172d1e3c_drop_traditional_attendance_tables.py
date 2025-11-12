"""drop traditional attendance tables

Revision ID: 86db172d1e3c
Revises: 20251111230000
Create Date: 2025-11-12 02:48:49.755336

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '86db172d1e3c'
down_revision = '20251111230000'
branch_labels = None
depends_on = None


def upgrade():
    """
    Drop all traditional attendance system tables and enum types.
    
    Tables being dropped:
    - shift_assignment (standalone shift assignments)
    - attendance (standalone attendance records)
    - project_shift_assignment (project-specific shift assignments)
    - project_attendance (project-specific attendance records)
    - attendance_day (global daily attendance)
    - project_shift (project shifts)
    - attendance_record (legacy attendance records)
    
    Enum types being dropped:
    - entitytype
    - attendancestatus  
    - absencereason
    """
    # Drop tables in reverse dependency order (children first, then parents)
    
    # Drop standalone attendance tables
    op.execute('DROP TABLE IF EXISTS shift_assignment CASCADE')
    op.execute('DROP TABLE IF EXISTS attendance CASCADE')
    
    # Drop project-specific attendance tables
    op.execute('DROP TABLE IF EXISTS project_shift_assignment CASCADE')
    op.execute('DROP TABLE IF EXISTS project_attendance CASCADE')
    
    # Drop global attendance table
    op.execute('DROP TABLE IF EXISTS attendance_day CASCADE')
    
    # Drop shift tables
    op.execute('DROP TABLE IF EXISTS project_shift CASCADE')
    
    # Drop legacy attendance record table
    op.execute('DROP TABLE IF EXISTS attendance_record CASCADE')
    
    # Drop enum types (only if they exist and are not used by other tables)
    # Note: These enums were only used by the deleted attendance tables
    op.execute('DROP TYPE IF EXISTS entitytype CASCADE')
    op.execute('DROP TYPE IF EXISTS attendancestatus CASCADE')
    op.execute('DROP TYPE IF EXISTS absencereason CASCADE')


def downgrade():
    """
    Recreate the attendance tables and enum types.
    Note: This is for rollback support only. Data will not be restored.
    """
    # Recreate enum types
    op.execute("CREATE TYPE entitytype AS ENUM ('EMPLOYEE', 'DOG')")
    op.execute("CREATE TYPE attendancestatus AS ENUM ('PRESENT', 'ABSENT', 'LATE', 'SICK', 'LEAVE', 'REMOTE', 'OVERTIME')")
    op.execute("CREATE TYPE absencereason AS ENUM ('ANNUAL', 'SICK', 'EMERGENCY', 'TRAINING', 'MISSION', 'NO_REASON', 'OTHER')")
    
    # Recreate attendance_record table
    op.create_table(
        'attendance_record',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('shift', sa.String(length=20), nullable=False),
        sa.Column('scheduled_start', sa.Time(), nullable=True),
        sa.Column('actual_start', sa.Time(), nullable=True),
        sa.Column('scheduled_end', sa.Time(), nullable=True),
        sa.Column('actual_end', sa.Time(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('leave_type', sa.String(length=50), nullable=True),
        sa.Column('substitute_employee_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employee.id'], ),
        sa.ForeignKeyConstraint(['substitute_employee_id'], ['employee.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_id', 'date', 'shift', name='unique_attendance')
    )
    
    # Recreate project_shift table
    op.create_table(
        'project_shift',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Recreate attendance_day table
    op.create_table(
        'attendance_day',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('status', sa.Enum('PRESENT', 'ABSENT', 'LATE', 'SICK', 'LEAVE', 'REMOTE', 'OVERTIME', name='attendancestatus'), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=16), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('locked', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employee.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_id', 'date', name='unique_employee_date')
    )
    op.create_index('ix_attendance_day_date', 'attendance_day', ['date'], unique=False)
    op.create_index('ix_attendance_day_employee_date', 'attendance_day', ['employee_id', 'date'], unique=False)
    
    # Recreate project_attendance table
    op.create_table(
        'project_attendance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shift_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('entity_type', sa.Enum('EMPLOYEE', 'DOG', name='entitytype'), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('PRESENT', 'ABSENT', 'LATE', 'SICK', 'LEAVE', 'REMOTE', 'OVERTIME', name='attendancestatus'), nullable=False),
        sa.Column('absence_reason', sa.Enum('ANNUAL', 'SICK', 'EMERGENCY', 'TRAINING', 'MISSION', 'NO_REASON', 'OTHER', name='absencereason'), nullable=True),
        sa.Column('late_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('check_in_time', sa.Time(), nullable=True),
        sa.Column('check_out_time', sa.Time(), nullable=True),
        sa.Column('recorded_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.ForeignKeyConstraint(['recorded_by_user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['shift_id'], ['project_shift.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'shift_id', 'date', 'entity_type', 'entity_id', name='unique_attendance_record')
    )
    
    # Recreate project_shift_assignment table
    op.create_table(
        'project_shift_assignment',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shift_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.Enum('EMPLOYEE', 'DOG', name='entitytype'), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('assigned_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shift_id'], ['project_shift.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('shift_id', 'entity_type', 'entity_id', name='unique_shift_entity_assignment')
    )
    
    # Recreate attendance table (standalone)
    op.create_table(
        'attendance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shift_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('entity_type', sa.Enum('EMPLOYEE', 'DOG', name='entitytype'), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('PRESENT', 'ABSENT', 'LATE', 'SICK', 'LEAVE', 'REMOTE', 'OVERTIME', name='attendancestatus'), nullable=False),
        sa.Column('absence_reason', sa.Enum('ANNUAL', 'SICK', 'EMERGENCY', 'TRAINING', 'MISSION', 'NO_REASON', 'OTHER', name='absencereason'), nullable=True),
        sa.Column('late_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('check_in_time', sa.Time(), nullable=True),
        sa.Column('check_out_time', sa.Time(), nullable=True),
        sa.Column('recorded_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['recorded_by_user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['shift_id'], ['shift.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('shift_id', 'date', 'entity_type', 'entity_id', name='unique_standalone_attendance_record')
    )
    
    # Recreate shift_assignment table (standalone)
    op.create_table(
        'shift_assignment',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shift_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.Enum('EMPLOYEE', 'DOG', name='entitytype'), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('assigned_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shift_id'], ['shift.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('shift_id', 'entity_type', 'entity_id', name='unique_standalone_shift_entity_assignment')
    )
