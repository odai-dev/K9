"""drop legacy attendance reporting tables

Revision ID: 20251111230000
Revises: 20251111172050
Create Date: 2025-11-11 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251111230000'
down_revision = '20251111172050'
branch_labels = None
depends_on = None


def upgrade():
    """
    Drop legacy attendance reporting tables that have been replaced by DailySchedule system.
    
    Tables being dropped:
    - project_attendance_reporting
    - attendance_day_leave
    - pm_daily_evaluation
    """
    # Drop tables in reverse dependency order
    op.drop_table('pm_daily_evaluation')
    op.drop_table('attendance_day_leave')
    op.drop_table('project_attendance_reporting')
    
    # Note: Enums AttendanceStatus and LeaveType are kept for now as they may be referenced
    # by other parts of the system (standalone attendance). Clean them up in a future migration
    # if confirmed unused.


def downgrade():
    """
    Recreate legacy attendance reporting tables (without data).
    Note: This is for rollback support only. Data will not be restored.
    """
    # Recreate project_attendance_reporting table
    op.create_table(
        'project_attendance_reporting',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shift_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('group_no', sa.Integer(), nullable=False),
        sa.Column('seq_no', sa.Integer(), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('substitute_employee_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('dog_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('check_in_time', sa.Time(), nullable=True),
        sa.Column('check_out_time', sa.Time(), nullable=True),
        sa.Column('status', sa.Enum('PRESENT', 'ABSENT', 'LATE', 'SICK', 'LEAVE', 'REMOTE', 'OVERTIME', name='attendancestatus'), nullable=False),
        sa.Column('is_project_controlled', sa.Boolean(), nullable=False),
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
    op.create_index('ix_attendance_group_seq', 'project_attendance_reporting', ['project_id', 'date', 'group_no', 'seq_no'], unique=False)
    op.create_index('ix_attendance_project_date', 'project_attendance_reporting', ['project_id', 'date'], unique=False)
    op.create_index(op.f('ix_project_attendance_reporting_date'), 'project_attendance_reporting', ['date'], unique=False)
    op.create_index(op.f('ix_project_attendance_reporting_project_id'), 'project_attendance_reporting', ['project_id'], unique=False)
    
    # Recreate attendance_day_leave table
    op.create_table(
        'attendance_day_leave',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('seq_no', sa.Integer(), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('leave_type', sa.Enum('ANNUAL', 'SICK', 'EMERGENCY', 'OTHER', name='leavetype'), nullable=False),
        sa.Column('note', sa.String(length=250), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employee.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'date', 'seq_no', name='uq_dayleave_print_slot')
    )
    op.create_index('ix_dayleave_project_date', 'attendance_day_leave', ['project_id', 'date'], unique=False)
    op.create_index(op.f('ix_attendance_day_leave_date'), 'attendance_day_leave', ['date'], unique=False)
    op.create_index(op.f('ix_attendance_day_leave_project_id'), 'attendance_day_leave', ['project_id'], unique=False)
    
    # Recreate pm_daily_evaluation table
    op.create_table(
        'pm_daily_evaluation',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('group_no', sa.Integer(), nullable=False),
        sa.Column('seq_no', sa.Integer(), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('dog_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('site_name', sa.String(length=120), nullable=True),
        sa.Column('shift_name', sa.String(length=60), nullable=True),
        sa.Column('uniform_ok', sa.Boolean(), nullable=False),
        sa.Column('card_ok', sa.Boolean(), nullable=False),
        sa.Column('appearance_ok', sa.Boolean(), nullable=False),
        sa.Column('cleanliness_ok', sa.Boolean(), nullable=False),
        sa.Column('dog_exam_done', sa.Boolean(), nullable=False),
        sa.Column('dog_fed', sa.Boolean(), nullable=False),
        sa.Column('dog_watered', sa.Boolean(), nullable=False),
        sa.Column('training_tansheti', sa.Boolean(), nullable=False),
        sa.Column('training_other', sa.Boolean(), nullable=False),
        sa.Column('field_deployment_done', sa.Boolean(), nullable=False),
        sa.Column('perf_sais', sa.String(length=10), nullable=True),
        sa.Column('perf_dog', sa.String(length=10), nullable=True),
        sa.Column('perf_murabbi', sa.String(length=10), nullable=True),
        sa.Column('perf_sehi', sa.String(length=10), nullable=True),
        sa.Column('perf_mudarrib', sa.String(length=10), nullable=True),
        sa.Column('violations', sa.Text(), nullable=True),
        sa.Column('is_on_leave_row', sa.Boolean(), nullable=False),
        sa.Column('on_leave_employee_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('on_leave_dog_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('on_leave_type', sa.Enum('ANNUAL', 'SICK', 'EMERGENCY', 'OTHER', name='leavetype'), nullable=True),
        sa.Column('on_leave_note', sa.String(length=250), nullable=True),
        sa.Column('is_replacement_row', sa.Boolean(), nullable=False),
        sa.Column('replacement_employee_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('replacement_dog_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dog_id'], ['dog.id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employee.id'], ),
        sa.ForeignKeyConstraint(['on_leave_dog_id'], ['dog.id'], ),
        sa.ForeignKeyConstraint(['on_leave_employee_id'], ['employee.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.ForeignKeyConstraint(['replacement_dog_id'], ['dog.id'], ),
        sa.ForeignKeyConstraint(['replacement_employee_id'], ['employee.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pm_daily_group_seq', 'pm_daily_evaluation', ['project_id', 'date', 'group_no', 'seq_no'], unique=False)
    op.create_index('ix_pm_daily_project_date', 'pm_daily_evaluation', ['project_id', 'date'], unique=False)
