#!/usr/bin/env python3
"""
Migration script to add project linking functionality to dog activities.
This script adds the necessary columns for automatic project linking.
"""

import os
import sqlite3
from datetime import datetime

def run_migration():
    """Add project linking columns to the database"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'k9_operations.db')
    
    if not os.path.exists(db_path):
        print("Database file not found. Creating new database...")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starting database migration for project linking...")
        
        # Check and add project_id to training_session
        cursor.execute("PRAGMA table_info(training_session)")
        training_columns = [column[1] for column in cursor.fetchall()]
        
        if 'project_id' not in training_columns:
            print("Adding project_id column to training_session...")
            cursor.execute("ALTER TABLE training_session ADD COLUMN project_id VARCHAR(36)")
            print("✓ Added project_id to training_session")
        else:
            print("✓ project_id already exists in training_session")
        
        # Check and add project_id to veterinary_visit
        cursor.execute("PRAGMA table_info(veterinary_visit)")
        vet_columns = [column[1] for column in cursor.fetchall()]
        
        if 'project_id' not in vet_columns:
            print("Adding project_id column to veterinary_visit...")
            cursor.execute("ALTER TABLE veterinary_visit ADD COLUMN project_id VARCHAR(36)")
            print("✓ Added project_id to veterinary_visit")
        else:
            print("✓ project_id already exists in veterinary_visit")
        
        # Check and add datetime fields to project_assignment
        cursor.execute("PRAGMA table_info(project_assignment)")
        assignment_columns = [column[1] for column in cursor.fetchall()]
        
        if 'assigned_from' not in assignment_columns:
            print("Adding assigned_from column to project_assignment...")
            cursor.execute("ALTER TABLE project_assignment ADD COLUMN assigned_from DATETIME")
            print("✓ Added assigned_from to project_assignment")
        else:
            print("✓ assigned_from already exists in project_assignment")
            
        if 'assigned_to' not in assignment_columns:
            print("Adding assigned_to column to project_assignment...")
            cursor.execute("ALTER TABLE project_assignment ADD COLUMN assigned_to DATETIME")
            print("✓ Added assigned_to to project_assignment")
        else:
            print("✓ assigned_to already exists in project_assignment")
        
        # Update existing project assignments to have assigned_from dates
        print("Updating existing project assignments with assigned_from dates...")
        current_time = datetime.utcnow().isoformat()
        cursor.execute("""
            UPDATE project_assignment 
            SET assigned_from = ? 
            WHERE assigned_from IS NULL AND is_active = 1
        """, (current_time,))
        
        updated_rows = cursor.rowcount
        if updated_rows > 0:
            print(f"✓ Updated {updated_rows} existing project assignments with assigned_from dates")
        
        conn.commit()
        print("\n🎉 Database migration completed successfully!")
        print("The system now supports automatic project linking for dog activities.")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during migration: {e}")
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    run_migration()