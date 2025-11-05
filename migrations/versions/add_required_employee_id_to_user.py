"""add required employee_id to user

Revision ID: add_emp_id_to_user
Revises: 1c71b2aa4886
Create Date: 2025-11-05 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import String
import uuid
import os


# revision identifiers, used by Alembic.
revision = 'add_emp_id_to_user'
down_revision = '1c71b2aa4886'
branch_labels = None
depends_on = None


def get_uuid_column_type():
    """Get the appropriate UUID column type based on database"""
    # Use the bind to get the actual dialect
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        return postgresql.UUID(as_uuid=True)
    else:
        # SQLite and others use String
        return String(36)


def upgrade():
    """Add employee_id foreign key to user table (required for all users)"""
    
    # Step 1: Add employee_id column as nullable first (to allow data migration)
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('employee_id', get_uuid_column_type(), nullable=True))
    
    # Step 2: Migrate existing data - link users to employees
    connection = op.get_bind()
    
    # Get database type
    database_url = os.environ.get("DATABASE_URL", "")
    is_postgres = not (database_url.startswith("sqlite") or not database_url)
    
    # Update users that already have employee records linked via employee.user_account_id
    if is_postgres:
        connection.execute(sa.text("""
            UPDATE "user" 
            SET employee_id = employee.id 
            FROM employee 
            WHERE employee.user_account_id = "user".id
        """))
    else:
        # SQLite doesn't support UPDATE FROM, so we need to do it differently
        employees = connection.execute(sa.text("""
            SELECT id, user_account_id FROM employee WHERE user_account_id IS NOT NULL
        """)).fetchall()
        
        for emp_id, user_id in employees:
            connection.execute(sa.text("""
                UPDATE user SET employee_id = :emp_id WHERE id = :user_id
            """), {"emp_id": emp_id, "user_id": user_id})
    
    # For users without linked employees, create employee records
    users_without_employees = connection.execute(sa.text("""
        SELECT id, username, email, full_name, role, active, created_at, phone
        FROM user 
        WHERE employee_id IS NULL
    """)).fetchall()
    
    from datetime import datetime, date as dt_date
    
    for user_data in users_without_employees:
        user_id, username, email, full_name, role, active, created_at, phone = user_data
        
        # Generate unique employee_id
        base_emp_id = f"EMP{str(user_id)[:8]}"
        emp_id_value = base_emp_id
        counter = 1
        
        while True:
            exists = connection.execute(sa.text("""
                SELECT COUNT(*) FROM employee WHERE employee_id = :emp_id
            """), {"emp_id": emp_id_value}).scalar()
            
            if not exists:
                break
            emp_id_value = f"{base_emp_id}_{counter}"
            counter += 1
        
        # Map user role to employee role (use enum names, not Arabic labels)
        role_mapping = {
            'HANDLER': 'HANDLER',
            'TRAINER': 'TRAINER',
            'BREEDER': 'BREEDER',
            'VET': 'VET',
            'PROJECT_MANAGER': 'PROJECT_MANAGER',
            'GENERAL_ADMIN': 'PROJECT_MANAGER',  # General admin maps to project manager for employee role
        }
        employee_role = role_mapping.get(role, 'PROJECT_MANAGER')
        
        # Generate phone if not set
        if not phone:
            phone = f"+967{str(user_id)[:9]}"
        
        # Create new employee record
        new_emp_id = str(uuid.uuid4())
        
        # Handle hire_date properly
        if created_at:
            if isinstance(created_at, datetime):
                hire_date = created_at.date()
            elif isinstance(created_at, str):
                hire_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
            else:
                hire_date = dt_date.today()
        else:
            hire_date = dt_date.today()
        
        # Get current timestamp
        now = datetime.utcnow()
        
        connection.execute(sa.text("""
            INSERT INTO employee (id, name, employee_id, role, phone, email, hire_date, is_active, user_account_id, created_at, updated_at)
            VALUES (:id, :name, :emp_id, :role, :phone, :email, :hire_date, :is_active, :user_id, :created_at, :updated_at)
        """), {
            "id": new_emp_id,
            "name": full_name,
            "emp_id": emp_id_value,
            "role": employee_role,
            "phone": phone,
            "email": email,
            "hire_date": hire_date,
            "is_active": bool(active),
            "user_id": user_id,
            "created_at": now,
            "updated_at": now
        })
        
        # Link user to new employee
        connection.execute(sa.text("""
            UPDATE user SET employee_id = :emp_id WHERE id = :user_id
        """), {"emp_id": new_emp_id, "user_id": user_id})
    
    # Step 3: Make employee_id NOT NULL and add foreign key constraint
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('employee_id', nullable=False)
        batch_op.create_foreign_key('fk_user_employee_id', 'employee', ['employee_id'], ['id'])


def downgrade():
    """Remove employee_id foreign key from user table"""
    
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('fk_user_employee_id', type_='foreignkey')
        batch_op.drop_column('employee_id')
