"""PM Review Workflow - Add workflow fields to VeterinaryVisit, BreedingTrainingActivity, and CaretakerDailyLog

Revision ID: 20251028_pm_review
Revises: 2cb36121e571
Create Date: 2025-10-28 23:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers, used by Alembic.
revision = '20251028_pm_review'
down_revision = '2cb36121e571'
branch_labels = None
depends_on = None


def upgrade():
    # Add workflow fields to VeterinaryVisit
    op.add_column('veterinary_visit', sa.Column('status', sa.String(50), nullable=False, server_default='DRAFT'))
    op.add_column('veterinary_visit', sa.Column('submitted_at', sa.DateTime(), nullable=True))
    op.add_column('veterinary_visit', sa.Column('reviewed_by_user_id', UUID(as_uuid=True), nullable=True))
    op.add_column('veterinary_visit', sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    op.add_column('veterinary_visit', sa.Column('review_notes', sa.Text(), nullable=True))
    op.add_column('veterinary_visit', sa.Column('created_by_user_id', UUID(as_uuid=True), nullable=True))
    
    # Add foreign keys for VeterinaryVisit
    op.create_foreign_key(
        'fk_veterinary_visit_reviewed_by_user',
        'veterinary_visit', 'user',
        ['reviewed_by_user_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_veterinary_visit_created_by_user',
        'veterinary_visit', 'user',
        ['created_by_user_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add indexes for VeterinaryVisit
    op.create_index('idx_veterinary_status', 'veterinary_visit', ['status'])
    
    # Add workflow fields to BreedingTrainingActivity
    op.add_column('breeding_training_activity', sa.Column('status', sa.String(50), nullable=False, server_default='DRAFT'))
    op.add_column('breeding_training_activity', sa.Column('submitted_at', sa.DateTime(), nullable=True))
    op.add_column('breeding_training_activity', sa.Column('reviewed_by_user_id', UUID(as_uuid=True), nullable=True))
    op.add_column('breeding_training_activity', sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    op.add_column('breeding_training_activity', sa.Column('review_notes', sa.Text(), nullable=True))
    
    # Add foreign key for BreedingTrainingActivity
    op.create_foreign_key(
        'fk_breeding_training_reviewed_by_user',
        'breeding_training_activity', 'user',
        ['reviewed_by_user_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add indexes for BreedingTrainingActivity
    op.create_index('idx_breeding_training_status', 'breeding_training_activity', ['status'])
    
    # Add workflow fields to CaretakerDailyLog
    op.add_column('caretaker_daily_log', sa.Column('status', sa.String(50), nullable=False, server_default='DRAFT'))
    op.add_column('caretaker_daily_log', sa.Column('submitted_at', sa.DateTime(), nullable=True))
    op.add_column('caretaker_daily_log', sa.Column('reviewed_by_user_id', UUID(as_uuid=True), nullable=True))
    op.add_column('caretaker_daily_log', sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    op.add_column('caretaker_daily_log', sa.Column('review_notes', sa.Text(), nullable=True))
    
    # Add foreign key for CaretakerDailyLog
    op.create_foreign_key(
        'fk_caretaker_daily_reviewed_by_user',
        'caretaker_daily_log', 'user',
        ['reviewed_by_user_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add indexes for CaretakerDailyLog
    op.create_index('idx_caretaker_daily_status', 'caretaker_daily_log', ['status'])
    
    # Create ReportReview audit table
    op.create_table(
        'report_review',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('report_id', sa.String(36), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('previous_status', sa.String(50), nullable=False),
        sa.Column('new_status', sa.String(50), nullable=False),
        sa.Column('reviewed_by_user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('project_id', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Add foreign keys for ReportReview
    op.create_foreign_key(
        'fk_report_review_user',
        'report_review', 'user',
        ['reviewed_by_user_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_report_review_project',
        'report_review', 'project',
        ['project_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add indexes for ReportReview
    op.create_index('idx_report_review_type_id', 'report_review', ['report_type', 'report_id'])
    op.create_index('idx_report_review_created_at', 'report_review', ['created_at'])
    op.create_index('idx_report_review_project', 'report_review', ['project_id'])


def downgrade():
    # Drop ReportReview table
    op.drop_index('idx_report_review_project', 'report_review')
    op.drop_index('idx_report_review_created_at', 'report_review')
    op.drop_index('idx_report_review_type_id', 'report_review')
    op.drop_constraint('fk_report_review_project', 'report_review', type_='foreignkey')
    op.drop_constraint('fk_report_review_user', 'report_review', type_='foreignkey')
    op.drop_table('report_review')
    
    # Remove CaretakerDailyLog workflow fields
    op.drop_index('idx_caretaker_daily_status', 'caretaker_daily_log')
    op.drop_constraint('fk_caretaker_daily_reviewed_by_user', 'caretaker_daily_log', type_='foreignkey')
    op.drop_column('caretaker_daily_log', 'review_notes')
    op.drop_column('caretaker_daily_log', 'reviewed_at')
    op.drop_column('caretaker_daily_log', 'reviewed_by_user_id')
    op.drop_column('caretaker_daily_log', 'submitted_at')
    op.drop_column('caretaker_daily_log', 'status')
    
    # Remove BreedingTrainingActivity workflow fields
    op.drop_index('idx_breeding_training_status', 'breeding_training_activity')
    op.drop_constraint('fk_breeding_training_reviewed_by_user', 'breeding_training_activity', type_='foreignkey')
    op.drop_column('breeding_training_activity', 'review_notes')
    op.drop_column('breeding_training_activity', 'reviewed_at')
    op.drop_column('breeding_training_activity', 'reviewed_by_user_id')
    op.drop_column('breeding_training_activity', 'submitted_at')
    op.drop_column('breeding_training_activity', 'status')
    
    # Remove VeterinaryVisit workflow fields
    op.drop_index('idx_veterinary_status', 'veterinary_visit')
    op.drop_constraint('fk_veterinary_visit_created_by_user', 'veterinary_visit', type_='foreignkey')
    op.drop_constraint('fk_veterinary_visit_reviewed_by_user', 'veterinary_visit', type_='foreignkey')
    op.drop_column('veterinary_visit', 'created_by_user_id')
    op.drop_column('veterinary_visit', 'review_notes')
    op.drop_column('veterinary_visit', 'reviewed_at')
    op.drop_column('veterinary_visit', 'reviewed_by_user_id')
    op.drop_column('veterinary_visit', 'submitted_at')
    op.drop_column('veterinary_visit', 'status')
