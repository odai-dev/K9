#!/usr/bin/env python3
"""
Create sample data for PM Daily Report system
Uses the actual model structure to create compatible data
"""

from datetime import date, timedelta
from uuid import uuid4
from app import app, db
from models import Project, Employee, User, UserRole, ProjectStatus, EmployeeRole
from models_attendance_reporting import PMDailyEvaluation, ProjectAttendanceReporting, LeaveType

def create_sample_data():
    """Create sample data for PM Daily system that works with existing models"""
    with app.app_context():
        print("Creating PM Daily sample data...")
        
        # Get existing project and employees
        project = Project.query.first()
        if not project:
            print("No project found. Please run create_test_user.py first.")
            return
            
        employees = Employee.query.all()
        if not employees:
            print("No employees found. Creating sample employees...")
            # Create sample employees
            admin_user = User.query.filter_by(username='admin').first()
            
            sample_employees = [
                ('أحمد محمد العلي', 'EMP001', EmployeeRole.TRAINER),
                ('سارة أحمد الخالد', 'EMP002', EmployeeRole.TRAINER),
                ('محمد علي الشمري', 'EMP003', EmployeeRole.VETERINARIAN),
                ('فاطمة سالم النجار', 'EMP004', EmployeeRole.BREEDER),
                ('عبدالله حسن الزهراني', 'EMP005', EmployeeRole.TRAINER)
            ]
            
            for name, emp_id, role in sample_employees:
                employee = Employee(
                    name=name,
                    employee_id=emp_id,
                    role=role,
                    phone='0501234567',
                    email=f"{emp_id.lower()}@test.com",
                    hire_date=date(2024, 1, 1),
                    user_account_id=admin_user.id if admin_user else None
                )
                db.session.add(employee)
                print(f"Created employee: {name}")
            
            db.session.commit()
            employees = Employee.query.all()
        
        # Create ProjectAttendanceReporting records for employees
        print("Creating attendance records...")
        for employee in employees[:5]:  # Use first 5 employees
            existing = ProjectAttendanceReporting.query.filter_by(
                project_id=str(project.id),
                employee_id=str(employee.id)
            ).first()
            
            if not existing:
                attendance_record = ProjectAttendanceReporting(
                    project_id=str(project.id),
                    employee_id=str(employee.id),
                    is_active=True,
                    joined_date=date(2024, 1, 1)
                )
                db.session.add(attendance_record)
                print(f"Created attendance record for {employee.name}")
        
        db.session.commit()
        
        # Create PM Daily evaluations for the last few days
        print("Creating PM Daily evaluations...")
        dates_to_create = [
            date.today() - timedelta(days=i) for i in range(5)
        ]
        
        for eval_date in dates_to_create:
            existing = PMDailyEvaluation.query.filter_by(
                project_id=str(project.id),
                evaluation_date=eval_date
            ).first()
            
            if not existing:
                evaluation = PMDailyEvaluation(
                    project_id=str(project.id),
                    evaluation_date=eval_date,
                    weather_condition='مشمس',
                    overall_notes='تم تنفيذ الأنشطة المخططة بنجاح',
                    achievements='تم تدريب 3 كلاب جديدة',
                    challenges='طقس حار في فترة الظهيرة',
                    tomorrow_plan='الاستمرار في برنامج التدريب المتقدم'
                )
                db.session.add(evaluation)
                db.session.flush()
                
                print(f"Created evaluation for {eval_date}")
                
                # Add attendance for some employees
                attendance_records = ProjectAttendanceReporting.query.filter_by(
                    project_id=str(project.id)
                ).limit(3).all()
                
                for attendance in attendance_records:
                    evaluation.attendances.append(attendance)
                
                print(f"Added {len(attendance_records)} attendance records to evaluation")
        
        db.session.commit()
        print("PM Daily sample data created successfully!")
        print(f"Created evaluations for project: {project.name}")

if __name__ == '__main__':
    create_sample_data()