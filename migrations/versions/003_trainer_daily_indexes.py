"""Add training session indexes for trainer daily reports

Revision ID: 003_trainer_daily_indexes
Revises: 002_daily_sheet_models
Create Date: 2025-08-24 20:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_trainer_daily_indexes'
down_revision = '002_daily_sheet_models'
branch_labels = None
depends_on = None

def upgrade():
    """Add indexes for trainer daily report performance."""
    # Add indexes for training session queries
    try:
        op.create_index('ix_training_session_project_date', 'training_session', ['project_id', 'session_date'])
    except Exception:
        pass  # Index might already exist
        
    try:
        op.create_index('ix_training_session_dog_date', 'training_session', ['dog_id', 'session_date'])
    except Exception:
        pass
        
    try:
        op.create_index('ix_training_session_trainer_date', 'training_session', ['trainer_id', 'session_date'])
    except Exception:
        pass
        
    try:
        op.create_index('ix_training_session_category_date', 'training_session', ['category', 'session_date'])
    except Exception:
        pass

def downgrade():
    """Remove indexes."""
    try:
        op.drop_index('ix_training_session_category_date', 'training_session')
    except Exception:
        pass
        
    try:
        op.drop_index('ix_training_session_trainer_date', 'training_session')
    except Exception:
        pass
        
    try:
        op.drop_index('ix_training_session_dog_date', 'training_session')
    except Exception:
        pass
        
    try:
        op.drop_index('ix_training_session_project_date', 'training_session')
    except Exception:
        pass