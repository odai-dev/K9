"""add breeding training activity with subtypes

Revision ID: breeding_training_001
Revises: 7e3cbfe31f8d
Create Date: 2025-09-10 16:34:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'breeding_training_001'
down_revision = '7e3cbfe31f8d'
branch_labels = None
depends_on = None


def upgrade():
    # Create the required enum types first (idempotently)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace WHERE t.typname='socializationtype' AND n.nspname='public') THEN
                CREATE TYPE socializationtype AS ENUM ('تفاعل مع البشر', 'تفاعل مع الحيوانات', 'التعرض للمركبات', 'إزالة الحساسية للأصوات', 'استكشاف البيئة', 'تفاعل مع الحشود');
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace WHERE t.typname='ballworktype' AND n.nspname='public') THEN
                CREATE TYPE ballworktype AS ENUM ('تدريب الإحضار', 'تدريب المسك', 'كرة الرشاقة', 'كرة التناسق', 'كرة المكافأة');
            END IF;
        END $$;
    """)

    # Create breeding_training_activity table using existing enum types
    op.create_table('breeding_training_activity',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('dog_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trainer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_date', sa.DateTime(), nullable=False),
        sa.Column('category', postgresql.ENUM(name='trainingcategory', create_type=False), nullable=False),
        sa.Column('subtype_socialization', postgresql.ENUM(name='socializationtype', create_type=False), nullable=True),
        sa.Column('subtype_ball', postgresql.ENUM(name='ballworktype', create_type=False), nullable=True),
        sa.Column('subject', sa.Text(), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.Column('success_rating', sa.Integer(), nullable=False),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('weather_conditions', sa.String(length=100), nullable=True),
        sa.Column('equipment_used', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('success_rating >= 1 AND success_rating <= 5', name='valid_success_rating'),
        sa.CheckConstraint('duration > 0', name='positive_duration'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['dog_id'], ['dog.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['trainer_id'], ['employee.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_breeding_training_dog_date', 'breeding_training_activity', ['dog_id', 'session_date'], unique=False)
    op.create_index('ix_breeding_training_project_date', 'breeding_training_activity', ['project_id', 'session_date'], unique=False)
    op.create_index('ix_breeding_training_trainer_date', 'breeding_training_activity', ['trainer_id', 'session_date'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index('ix_breeding_training_trainer_date', table_name='breeding_training_activity')
    op.drop_index('ix_breeding_training_project_date', table_name='breeding_training_activity')
    op.drop_index('ix_breeding_training_dog_date', table_name='breeding_training_activity')
    
    # Drop table
    op.drop_table('breeding_training_activity')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS socializationtype')
    op.execute('DROP TYPE IF EXISTS ballworktype')