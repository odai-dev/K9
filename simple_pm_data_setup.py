#!/usr/bin/env python3
"""
Simple setup script to create database tables and basic PM Daily sample data
"""

from datetime import date, timedelta
import uuid
from werkzeug.security import generate_password_hash
from app import app, db

def setup_pm_daily_system():
    """Initialize database and create sample data for PM Daily system"""
    with app.app_context():
        print("Initializing database and creating sample data...")
        
        # Create all tables
        db.create_all()
        print("Created database tables")
        
        # Import models after db is created
        from models import User, Project, Employee, UserRole, ProjectStatus, EmployeeRole
        from models_attendance_reporting import PMDailyEvaluation
        
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
            db.session.commit()
            print("Created admin user")
        
        # Create test project
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
            db.session.commit()
            print("Created test project")
        
        # Create test employees
        employees_data = [
            ('أحمد محمد العلي', 'EMP001'),
            ('سارة أحمد الخالد', 'EMP002'), 
            ('محمد علي الشمري', 'EMP003'),
        ]
        
        for name, emp_id in employees_data:
            employee = Employee.query.filter_by(employee_id=emp_id).first()
            if not employee:
                employee = Employee(
                    name=name,
                    employee_id=emp_id,
                    role=EmployeeRole.TRAINER,
                    phone='0501234567',
                    email=f"{emp_id.lower()}@test.com",
                    hire_date=date(2024, 1, 1)
                )
                db.session.add(employee)
        
        db.session.commit()
        print("Created test employees")
        
        # Create PM Daily evaluations for today and yesterday
        dates_to_create = [date.today(), date.today() - timedelta(days=1)]
        
        for eval_date in dates_to_create:
            existing = PMDailyEvaluation.query.filter_by(
                project_id=str(project.id),
                date=eval_date
            ).first()
            
            if not existing:
                evaluation = PMDailyEvaluation(
                    project_id=str(project.id),
                    date=eval_date,
                    group_no=1,
                    seq_no=1,
                    site_name='موقع التدريب الأساسي',
                    shift_name='الفترة الصباحية',
                    uniform_ok=True,
                    card_ok=True,
                    appearance_ok=True,
                    dog_exam_done=True,
                    dog_fed=True,
                    training_tansheti=True,
                    perf_sais='ممتاز',
                    perf_dog='جيد'
                )
                db.session.add(evaluation)
                print(f"Created PM Daily evaluation for {eval_date}")
        
        db.session.commit()
        print("Sample data creation completed successfully!")
        print("\nLogin credentials:")
        print("Username: admin")  
        print("Password: admin123")
        print(f"\nCreated project: {project.name}")

if __name__ == '__main__':
    setup_pm_daily_system()