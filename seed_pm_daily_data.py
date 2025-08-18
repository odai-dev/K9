#!/usr/bin/env python3
"""
Seed script for PM Daily Evaluation system
Creates sample data for testing the PM Daily Report functionality
"""

from datetime import date, datetime, timedelta
from app import app, db
from models import Project, Employee, User
from models_attendance_reporting import (
    PMDailyEvaluation, ProjectAttendanceReporting, LeaveType
)

def seed_pm_daily_data():
    """Create sample data for PM Daily system"""
    with app.app_context():
        print("Starting PM Daily data seeding...")
        
        # Get or create a test project
        project = Project.query.filter_by(name='مشروع الكلاب الأمنية').first()
        if not project:
            # Create a sample project
            project = Project(
                name='مشروع الكلاب الأمنية',
                description='مشروع تدريب وإدارة الكلاب الأمنية',
                status='active',
                start_date=date(2024, 1, 1),
                location='الرياض'
            )
            db.session.add(project)
            db.session.commit()
            print(f"Created project: {project.name}")
        
        # Get or create sample employees
        employees_data = [
            ('أحمد محمد السعد', 'TRAINER', 'ahmed.saad@example.com'),
            ('سارة أحمد الخالد', 'TRAINER', 'sara.khaled@example.com'),
            ('محمد علي الشمري', 'VETERINARIAN', 'mohammed.shamri@example.com'),
            ('فاطمة سالم النجار', 'BREEDER', 'fatma.najjar@example.com'),
            ('عبدالله حسن الزهراني', 'TRAINER', 'abdullah.zahrani@example.com')
        ]
        
        employees = []
        for name, role, email in employees_data:
            employee = Employee.query.filter_by(email=email).first()
            if not employee:
                # Create user first
                user = User(
                    username=email.split('@')[0],
                    email=email,
                    full_name=name,
                    role='EMPLOYEE'
                )
                db.session.add(user)
                db.session.flush()
                
                employee = Employee(
                    user_id=user.id,
                    full_name=name,
                    role=role,
                    email=email,
                    phone='0501234567',
                    hire_date=date(2024, 1, 1)
                )
                db.session.add(employee)
                print(f"Created employee: {name}")
            employees.append(employee)
        
        db.session.commit()
        
        # Create ProjectAttendanceReporting records
        for employee in employees:
            attendance = ProjectAttendanceReporting.query.filter_by(
                project_id=project.id, 
                employee_id=employee.id
            ).first()
            if not attendance:
                attendance = ProjectAttendanceReporting(
                    project_id=project.id,
                    employee_id=employee.id,
                    is_active=True,
                    joined_date=date(2024, 1, 1)
                )
                db.session.add(attendance)
                print(f"Created attendance record for: {employee.full_name}")
        
        db.session.commit()
        
        # Create leave types if they don't exist
        leave_types_data = [
            ('إجازة مرضية', 'SICK'),
            ('إجازة شخصية', 'PERSONAL'),
            ('إجازة طوارئ', 'EMERGENCY')
        ]
        
        for name, code in leave_types_data:
            leave_type = LeaveType.query.filter_by(code=code).first()
            if not leave_type:
                leave_type = LeaveType(name=name, code=code)
                db.session.add(leave_type)
                print(f"Created leave type: {name}")
        
        db.session.commit()
        
        # Create sample PM Daily evaluations for the past few days
        dates_to_create = [
            date.today() - timedelta(days=i) for i in range(5)
        ]
        
        for eval_date in dates_to_create:
            existing = PMDailyEvaluation.query.filter_by(
                project_id=project.id,
                evaluation_date=eval_date
            ).first()
            
            if not existing:
                # Create evaluation
                evaluation = PMDailyEvaluation(
                    project_id=project.id,
                    evaluation_date=eval_date,
                    weather_condition='مشمس',
                    overall_notes='تم تنفيذ الأنشطة المخططة بنجاح. الفريق متحمس ومنتج.',
                    achievements='تم تدريب 5 كلاب جديدة وإنجاز جلسات التدريب الأساسية',
                    challenges='طقس حار قليلاً في فترة الظهيرة',
                    tomorrow_plan='الاستمرار في برنامج التدريب وبدء مرحلة جديدة من التدريبات المتقدمة'
                )
                db.session.add(evaluation)
                db.session.flush()
                
                print(f"Created evaluation for {eval_date}")
                
                # Add some attendance records
                for i, employee in enumerate(employees[:3]):  # First 3 employees present
                    attendance = ProjectAttendanceReporting.query.filter_by(
                        project_id=project.id,
                        employee_id=employee.id
                    ).first()
                    
                    if attendance:
                        evaluation.attendances.append(attendance)
                        print(f"Added attendance for {employee.full_name}")
                
                # Add some replacements for absent employees
                if len(employees) >= 5:
                    # Employee 4 is replaced by employee 5
                    absent_employee = employees[3]
                    replacement_employee = employees[4]
                    
                    absent_attendance = ProjectAttendanceReporting.query.filter_by(
                        project_id=project.id,
                        employee_id=absent_employee.id
                    ).first()
                    
                    replacement_attendance = ProjectAttendanceReporting.query.filter_by(
                        project_id=project.id,
                        employee_id=replacement_employee.id
                    ).first()
                    
                    if absent_attendance and replacement_attendance:
                        evaluation.replacements.append({
                            'absent_employee_id': absent_attendance.id,
                            'replacement_employee_id': replacement_attendance.id,
                            'reason': 'إجازة مرضية'
                        })
                        print(f"Added replacement: {replacement_employee.full_name} replacing {absent_employee.full_name}")
        
        db.session.commit()
        print("PM Daily data seeding completed successfully!")

if __name__ == '__main__':
    seed_pm_daily_data()