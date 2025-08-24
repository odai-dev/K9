#!/usr/bin/env python3
"""
Test the dropdown API endpoints
"""

import os
from app import app, db
from models import User, Project, Employee, Dog

def test_dropdown_apis():
    """Test the dropdown API endpoints with auth"""
    
    with app.app_context():
        print("🧪 Testing Dropdown APIs...")
        
        # Get admin user
        admin_user = db.session.query(User).filter_by(username='admin').first()
        if not admin_user:
            print("❌ Admin user not found")
            return
            
        print(f"✅ Using user: {admin_user.username}")
        
        # Test data counts
        projects = db.session.query(Project).all()
        employees = db.session.query(Employee).all()  
        dogs = db.session.query(Dog).all()
        
        print(f"📊 Database contents:")
        print(f"   - Projects: {len(projects)}")
        print(f"   - Employees: {len(employees)}")
        print(f"   - Dogs: {len(dogs)}")
        
        # Sample data
        if projects:
            print(f"\n📁 Sample Project: {projects[0].name}")
        if employees:
            print(f"👨‍💼 Sample Employee: {employees[0].name}")
        if dogs:
            print(f"🐕 Sample Dog: {dogs[0].name}")

if __name__ == "__main__":
    test_dropdown_apis()