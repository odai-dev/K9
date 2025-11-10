"""add report attachments support

Revision ID: 20251110200957
Revises: 1c71b2aa4886
Create Date: 2025-11-10 20:09:57.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251110200957'
down_revision = 'add_emp_id_to_user'
branch_labels = None
depends_on = None


def upgrade():
    # Add report_id column (nullable FK to handler_report)
    op.add_column('handler_report_attachment', 
                  sa.Column('report_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_handler_report_attachment_report_id', 
                         'handler_report_attachment', 'handler_report',
                         ['report_id'], ['id'], ondelete='CASCADE')
    
    # Add description column
    op.add_column('handler_report_attachment',
                  sa.Column('description', sa.Text(), nullable=True))
    
    # Make incident_id nullable
    op.alter_column('handler_report_attachment', 'incident_id',
                   existing_type=sa.UUID(),
                   nullable=True)
    
    # Add check constraint to ensure at least one parent
    op.create_check_constraint(
        'attachment_must_have_parent',
        'handler_report_attachment',
        '(report_id IS NOT NULL) OR (incident_id IS NOT NULL)'
    )
    
    # Create indexes for better query performance
    op.create_index('idx_attachment_report', 'handler_report_attachment', ['report_id'])
    op.create_index('idx_attachment_incident', 'handler_report_attachment', ['incident_id'])


def downgrade():
    # Remove indexes
    op.drop_index('idx_attachment_incident', table_name='handler_report_attachment')
    op.drop_index('idx_attachment_report', table_name='handler_report_attachment')
    
    # Remove check constraint
    op.drop_constraint('attachment_must_have_parent', 'handler_report_attachment', type_='check')
    
    # Revert incident_id to NOT NULL (requires data cleanup first)
    op.alter_column('handler_report_attachment', 'incident_id',
                   existing_type=sa.UUID(),
                   nullable=False)
    
    # Remove new columns
    op.drop_column('handler_report_attachment', 'description')
    op.drop_constraint('fk_handler_report_attachment_report_id', 'handler_report_attachment', type_='foreignkey')
    op.drop_column('handler_report_attachment', 'report_id')
