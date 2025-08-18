#!/usr/bin/env python3
"""
Simple script to create a test admin user and basic project data
"""

from datetime import date
from werkzeug.security import generate_password_hash
from app import app, db
from models import User, Project, Employee, UserRole, ProjectStatus, EmployeeRole

def create_test_data():
    """Create a test admin user and basic project data"""
    with app.app_context():
        print("Creating test data...")
        
        # Create admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@test.com',
                full_name='مدير النظام',
                role=UserRole.GENERAL_ADMIN,
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            print("Created admin user (username: admin, password: admin123)")
        
        # Create a test project
        project = Project.query.filter_by(name='مشروع الكلاب الأمنية').first()
        if not project:
            project = Project(
                name='مشروع الكلاب الأمنية',
                code='SEC-DOGS-001',
                description='مشروع تدريب وإدارة الكلاب الأمنية',
                status=ProjectStatus.ACTIVE,
                start_date=date(2024, 1, 1),
                location='الرياض',
                manager_id=admin.id
            )
            db.session.add(project)
            print("Created test project")
        
        # Create a test employee
        employee = Employee.query.filter_by(name='أحمد محمد').first()
        if not employee:
            employee = Employee(
                name='أحمد محمد',
                employee_id='EMP001',
                role=EmployeeRole.TRAINER,
                phone='0501234567',
                email='ahmed@test.com',
                hire_date=date(2024, 1, 1),
                user_account_id=admin.id
            )
            db.session.add(employee)
            print("Created test employee")
        
        db.session.commit()
        print("Test data created successfully!")
        print("\nYou can now login with:")
        print("Username: admin")
        print("Password: admin123")

if __name__ == '__main__':
    create_test_data()