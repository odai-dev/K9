"""Add PMDailyEvaluation model for PM Daily Reports

Revision ID: 20250818_pm_daily
Revises: 
Create Date: 2025-08-18 20:07:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision = '20250818_pm_daily'
down_revision = None
depends_on = None


def upgrade():
    """Create PMDailyEvaluation table"""
    op.create_table('pm_daily_evaluation',
    sa.Column('id', UUID(as_uuid=True), nullable=False),
    sa.Column('project_id', UUID(as_uuid=True), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('group_no', sa.Integer(), nullable=False),
    sa.Column('seq_no', sa.Integer(), nullable=False),
    sa.Column('employee_id', UUID(as_uuid=True), nullable=True),
    sa.Column('dog_id', UUID(as_uuid=True), nullable=True),
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
    sa.Column('on_leave_employee_id', UUID(as_uuid=True), nullable=True),
    sa.Column('on_leave_dog_id', UUID(as_uuid=True), nullable=True),
    sa.Column('on_leave_type', sa.Enum('ANNUAL', 'SICK', 'EMERGENCY', 'OTHER', name='leavetype'), nullable=True),
    sa.Column('on_leave_note', sa.String(length=250), nullable=True),
    sa.Column('is_replacement_row', sa.Boolean(), nullable=False),
    sa.Column('replacement_employee_id', UUID(as_uuid=True), nullable=True),
    sa.Column('replacement_dog_id', UUID(as_uuid=True), nullable=True),
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
    
    # Create indexes
    op.create_index('ix_pm_daily_project_date', 'pm_daily_evaluation', ['project_id', 'date'], unique=False)
    op.create_index('ix_pm_daily_group_seq', 'pm_daily_evaluation', ['project_id', 'date', 'group_no', 'seq_no'], unique=False)


def downgrade():
    """Drop PMDailyEvaluation table"""
    op.drop_index('ix_pm_daily_group_seq', table_name='pm_daily_evaluation')
    op.drop_index('ix_pm_daily_project_date', table_name='pm_daily_evaluation')
    op.drop_table('pm_daily_evaluation')