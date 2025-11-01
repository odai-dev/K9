"""
Initialize database with proper handling of circular dependencies.
This script creates all tables bypassing Alembic's automatic dependency resolution.
"""
from app import app, db
from sqlalchemy import text

def init_database():
    """Initialize database by creating all tables"""
    with app.app_context():
        try:
            # Drop all existing tables if any
            print("Dropping existing tables if any...")
            db.drop_all()
            
            # Create all tables - SQLAlchemy will handle the circular dependencies
            print("Creating all tables...")
            db.create_all()
            
            # Initialize the alembic version table to mark as migrated
            print("Initializing alembic version table...")
            
            # Create alembic version table if it doesn't exist
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                )
            """))
            
            # Insert the current migration version
            # First check if there's already a version
            result = db.session.execute(text("SELECT version_num FROM alembic_version")).fetchone()
            if result:
                # Update existing version
                db.session.execute(
                    text("UPDATE alembic_version SET version_num = '3e4e3e2cfa84'")
                )
            else:
                # Insert new version
                db.session.execute(
                    text("INSERT INTO alembic_version (version_num) VALUES ('3e4e3e2cfa84')")
                )
            
            db.session.commit()
            
            print("✓ Database initialized successfully!")
            print("✓ All tables created")
            print("✓ Migration version set to 3e4e3e2cfa84")
            
            # Verify tables were created
            result = db.session.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema='public' 
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"✓ Total tables created: {len(tables)}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error initializing database: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = init_database()
    exit(0 if success else 1)
