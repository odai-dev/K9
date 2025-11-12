"""add access audit log

Revision ID: 20251112215208
Revises: 20251111230000
Create Date: 2025-11-12 21:52:08.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251112215208'
down_revision = '86db172d1e3c'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    
    conn.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'accessactiontype') THEN
                CREATE TYPE accessactiontype AS ENUM ('PAGE_ACCESS', 'FILE_DOWNLOAD', 'REPORT_APPROVAL', 'REPORT_REJECTION', 'SCHEDULE_ACCESS', 'SHIFT_ACCESS', 'PROJECT_ACCESS', 'DATA_EXPORT');
            END IF;
        END $$;
    """))
    
    conn.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'accessoutcome') THEN
                CREATE TYPE accessoutcome AS ENUM ('SUCCESS', 'FAILURE', 'BLOCKED');
            END IF;
        END $$;
    """))
    
    op.create_table('access_audit_logs',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('action_type', postgresql.ENUM('PAGE_ACCESS', 'FILE_DOWNLOAD', 'REPORT_APPROVAL', 'REPORT_REJECTION', 'SCHEDULE_ACCESS', 'SHIFT_ACCESS', 'PROJECT_ACCESS', 'DATA_EXPORT', name='accessactiontype', create_type=False), nullable=False),
    sa.Column('target_type', sa.String(length=80), nullable=True),
    sa.Column('target_id', sa.String(length=36), nullable=True),
    sa.Column('target_name', sa.String(length=200), nullable=True),
    sa.Column('request_path', sa.String(length=300), nullable=True),
    sa.Column('http_method', sa.String(length=10), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.Column('session_id', sa.String(length=255), nullable=True),
    sa.Column('admin_mode', sa.String(length=40), nullable=True),
    sa.Column('outcome', postgresql.ENUM('SUCCESS', 'FAILURE', 'BLOCKED', name='accessoutcome', create_type=False), nullable=True),
    sa.Column('extra_metadata', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_access_audit_action_time', 'access_audit_logs', ['action_type', 'created_at'], unique=False)
    op.create_index('idx_access_audit_user_time', 'access_audit_logs', ['user_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_access_audit_logs_created_at'), 'access_audit_logs', ['created_at'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_access_audit_logs_created_at'), table_name='access_audit_logs')
    op.drop_index('idx_access_audit_user_time', table_name='access_audit_logs')
    op.drop_index('idx_access_audit_action_time', table_name='access_audit_logs')
    op.drop_table('access_audit_logs')
    op.execute('DROP TYPE accessactiontype')
    op.execute('DROP TYPE accessoutcome')
