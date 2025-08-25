#!/usr/bin/env python3
"""Setup script to create grooming table with English enums"""

import os
import sys
from app import app, db

def setup_grooming_tables():
    """Create grooming table using SQLAlchemy model"""
    with app.app_context():
        try:
            # Import the model to ensure it's registered
            from models import GroomingLog
            
            print("Creating grooming table...")
            # Create the grooming_log table
            db.create_all()
            
            print("✓ Grooming table created successfully!")
            return True
            
        except Exception as e:
            print(f"Error setting up grooming tables: {e}")
            return False

if __name__ == "__main__":
    success = setup_grooming_tables()
    sys.exit(0 if success else 1)