#!/usr/bin/env python3
"""Quick script to create an admin user for testing"""

from app import app, db
from k9.models.models import User, UserRole
from werkzeug.security import generate_password_hash
import uuid

with app.app_context():
    # Check if admin user already exists
    admin_user = User.query.filter_by(username='admin').first()
    if admin_user:
        print("Admin user already exists")
    else:
        # Create admin user
        admin_user = User()
        admin_user.username = 'admin'
        admin_user.email = 'admin@k9system.com'
        admin_user.full_name = 'System Administrator'
        admin_user.password_hash = generate_password_hash('password123')
        admin_user.role = UserRole.GENERAL_ADMIN
        admin_user.active = True
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("✓ Admin user created successfully!")
        print("Username: admin")
        print("Password: password123")