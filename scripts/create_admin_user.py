#!/usr/bin/env python3
"""
K9 Operations Management System - Admin User Creation Script

This script creates an admin user for production deployments where the default
admin user creation is disabled.

Usage:
    python create_admin_user.py
    
Or within Docker container:
    docker-compose exec web python create_admin_user.py
"""

import os
import sys
import getpass
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Create an admin user with interactive prompts."""
    
    # Import Flask app and models
    try:
        from app import app, db
        from k9.models.models import User, UserRole
    except ImportError as e:
        print(f"Error importing application modules: {e}")
        print("Make sure you're running this script from the application directory.")
        sys.exit(1)
    
    with app.app_context():
        print("K9 Operations Management System - Admin User Creation")
        print("=" * 60)
        
        # Get user input
        username = input("Enter admin username: ").strip()
        if not username:
            print("Username cannot be empty.")
            sys.exit(1)
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"User '{username}' already exists.")
            overwrite = input("Overwrite existing user? (y/N): ").strip().lower()
            if overwrite != 'y':
                print("Aborted.")
                sys.exit(1)
        
        email = input("Enter admin email: ").strip()
        if not email:
            print("Email cannot be empty.")
            sys.exit(1)
        
        full_name = input("Enter full name: ").strip()
        if not full_name:
            full_name = "System Administrator"
        
        # Get password securely
        password = getpass.getpass("Enter password: ")
        if not password:
            print("Password cannot be empty.")
            sys.exit(1)
        
        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            print("Passwords do not match.")
            sys.exit(1)
        
        if len(password) < 8:
            print("Password must be at least 8 characters long.")
            sys.exit(1)
        
        try:
            if existing_user:
                # Update existing user
                user = existing_user
                user.email = email
                user.full_name = full_name
                user.password_hash = generate_password_hash(password)
                user.role = UserRole.GENERAL_ADMIN
                user.active = True
                action = "updated"
            else:
                # Create new user
                user = User()
                user.username = username
                user.email = email
                user.full_name = full_name
                user.password_hash = generate_password_hash(password)
                user.role = UserRole.GENERAL_ADMIN
                user.active = True
                db.session.add(user)
                action = "created"
            
            db.session.commit()
            
            print(f"\n✓ Admin user '{username}' {action} successfully!")
            print(f"  Email: {email}")
            print(f"  Name: {full_name}")
            print(f"  Role: General Admin")
            print(f"  Status: Active")
            print("\nYou can now log in to the K9 Operations Management System.")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error creating admin user: {e}")
            sys.exit(1)

if __name__ == "__main__":
    create_admin_user()