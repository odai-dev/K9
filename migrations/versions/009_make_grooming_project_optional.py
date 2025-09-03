"""Make project_id optional in grooming_log table

Revision ID: 009_make_grooming_project_optional
Revises: 008
Create Date: 2025-01-03 22:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009_make_grooming_project_optional'
down_revision = '008'
branch_labels = None
depends_on = None

def upgrade():
    """Make project_id nullable in grooming_log table"""
    
    # Check if we're using SQLite or PostgreSQL  
    conn = op.get_bind()
    if conn.dialect.name == 'sqlite':
        # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
        # First create a temporary table with the new structure
        op.execute("""
            CREATE TABLE grooming_log_new (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                date DATE NOT NULL,
                time TIME NOT NULL,
                dog_id TEXT NOT NULL,
                recorder_employee_id TEXT,
                washed_bathed TEXT,
                shampoo_type TEXT,
                brushing TEXT,
                nail_trimming TEXT,
                teeth_brushing TEXT,
                ear_cleaning TEXT,
                eye_cleaning TEXT,
                cleanliness_score TEXT,
                notes TEXT,
                created_by_user_id INTEGER,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                FOREIGN KEY(project_id) REFERENCES project (id) ON DELETE CASCADE,
                FOREIGN KEY(dog_id) REFERENCES dog (id) ON DELETE CASCADE,
                FOREIGN KEY(recorder_employee_id) REFERENCES employee (id) ON DELETE SET NULL,
                FOREIGN KEY(created_by_user_id) REFERENCES user (id) ON DELETE SET NULL
            )
        """)
        
        # Copy data from the old table to the new table
        op.execute("""
            INSERT INTO grooming_log_new 
            SELECT id, project_id, date, time, dog_id, recorder_employee_id, 
                   washed_bathed, shampoo_type, brushing, nail_trimming, 
                   teeth_brushing, ear_cleaning, eye_cleaning, cleanliness_score, 
                   notes, created_by_user_id, created_at, updated_at
            FROM grooming_log
        """)
        
        # Drop the old table
        op.drop_table('grooming_log')
        
        # Rename the new table
        op.execute("ALTER TABLE grooming_log_new RENAME TO grooming_log")
    else:
        # PostgreSQL supports ALTER COLUMN
        op.alter_column('grooming_log', 'project_id',
                       existing_type=sa.String(36),
                       nullable=True)

def downgrade():
    """Make project_id non-nullable again (this may fail if there are NULL values)"""
    
    conn = op.get_bind()
    if conn.dialect.name == 'sqlite':
        # For SQLite, we'd need to recreate the table again
        # This is complex and may cause data loss, so we'll skip it for now
        pass
    else:
        # PostgreSQL - this may fail if there are NULL values
        op.alter_column('grooming_log', 'project_id',
                       existing_type=sa.String(36),
                       nullable=False)