"""Add GroomingLog model with Arabic enums for breeding grooming feature

Revision ID: 007_breeding_grooming
Revises: 20250818_pm_daily
Create Date: 2025-08-25 17:37:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers
revision = '007_breeding_grooming'
down_revision = '20250818_pm_daily'
depends_on = None


def upgrade():
    """Create grooming enums and grooming_log table"""
    
    # Create YesNo enum with Arabic values
    op.execute("""
        CREATE TYPE yesno AS ENUM ('نعم', 'لا')
    """)
    
    # Create CleanlinessScore enum
    op.execute("""
        CREATE TYPE cleanlinessscore AS ENUM ('1', '2', '3', '4', '5')
    """)
    
    # Create grooming_log table
    op.create_table('grooming_log',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('time', sa.Time(), nullable=False),
        sa.Column('dog_id', UUID(as_uuid=True), nullable=False),
        sa.Column('recorder_employee_id', UUID(as_uuid=True), nullable=True),
        sa.Column('غسل_الكلب', sa.Enum('نعم', 'لا', name='yesno'), nullable=True),
        sa.Column('نوع_الشامبو', sa.String(length=120), nullable=True),
        sa.Column('تمشيط', sa.Enum('نعم', 'لا', name='yesno'), nullable=True),
        sa.Column('قص_الأظافر', sa.Enum('نعم', 'لا', name='yesno'), nullable=True),
        sa.Column('فرش_الأسنان', sa.Enum('نعم', 'لا', name='yesno'), nullable=True),
        sa.Column('تنظيف_الأذن', sa.Enum('نعم', 'لا', name='yesno'), nullable=True),
        sa.Column('تنظيف_العين', sa.Enum('نعم', 'لا', name='yesno'), nullable=True),
        sa.Column('نظافة_عامه', sa.Enum('1', '2', '3', '4', '5', name='cleanlinessscore'), nullable=True),
        sa.Column('ملاحظات', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['dog_id'], ['dog.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recorder_employee_id'], ['employee.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'dog_id', 'date', 'time', name='uq_grooming_project_dog_dt')
    )
    
    # Create indexes
    op.create_index('ix_grooming_project_date', 'grooming_log', ['project_id', 'date'])
    op.create_index('ix_grooming_dog_datetime', 'grooming_log', ['dog_id', 'date', 'time'])


def downgrade():
    """Drop grooming_log table and enums"""
    
    # Drop indexes
    op.drop_index('ix_grooming_dog_datetime', table_name='grooming_log')
    op.drop_index('ix_grooming_project_date', table_name='grooming_log')
    
    # Drop table
    op.drop_table('grooming_log')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS cleanlinessscore")
    op.execute("DROP TYPE IF EXISTS yesno")