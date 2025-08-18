#!/usr/bin/env python3
"""
Sample attendance data seeder for testing daily sheet functionality
Creates comprehensive attendance reporting data for testing purposes
"""

import os
import sys
from datetime import datetime, date, time, timedelta
from uuid import uuid4

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Project, Employee, Dog, ProjectStatus, EmployeeRole, DogStatus, DogGender
from models_attendance_reporting import (
    ProjectAttendanceReporting, AttendanceDayLeave, 
    AttendanceStatus, LeaveType
)

def create_sample_attendance_data():
    """Create comprehensive sample attendance data for testing"""
    
    with app.app_context():
        print("🔄 Creating sample attendance reporting data...")
        
        # Check if we have projects, employees, and dogs
        projects = Project.query.filter(Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED])).all()
        employees = Employee.query.all()
        dogs = Dog.query.filter(Dog.current_status == DogStatus.ACTIVE).all()
        
        if not projects:
            print("⚠️  No active/planned projects found. Creating sample project...")
            # Create a sample project
            project = Project()
            project.id = str(uuid4())
            project.name = "مشروع الحراسة الأمنية"
            project.code = "SEC-001"
            project.main_task = "الحراسة والأمن"
            project.description = "مشروع الحراسة الأمنية للمنطقة الشمالية"
            project.status = ProjectStatus.ACTIVE
            project.start_date = date.today() - timedelta(days=30)
            project.location = "المنطقة الشمالية"
            project.mission_type = "أمني"
            project.priority = "عالية"
            db.session.add(project)
            projects = [project]
        
        if not employees:
            print("⚠️  No employees found. Creating sample employees...")
            # Create sample employees
            employee_data = [
                {"name": "أحمد محمد السائس", "role": EmployeeRole.HANDLER},
                {"name": "سعد علي المدرب", "role": EmployeeRole.TRAINER},
                {"name": "فايز محمود البديل", "role": EmployeeRole.HANDLER},
                {"name": "نادر خالد المربي", "role": EmployeeRole.BREEDER},
                {"name": "محمد أحمد الطبيب", "role": EmployeeRole.VET},
            ]
            
            for i, emp_data in enumerate(employee_data):
                employee = Employee()
                employee.id = str(uuid4())
                employee.name = emp_data["name"]
                employee.employee_id = f"EMP{i+1:03d}"
                employee.role = emp_data["role"]
                employee.phone = "+966501234567"
                employee.email = f"employee{i+1}@k9ops.com"
                employee.hire_date = date.today() - timedelta(days=365)
                employee.is_active = True
                db.session.add(employee)
                employees.append(employee)
        
        if not dogs:
            print("⚠️  No active dogs found. Creating sample dogs...")
            # Create sample dogs
            dog_data = [
                {"name": "رعد", "breed": "الراعي الألماني", "gender": DogGender.MALE},
                {"name": "نمر", "breed": "البلجيكي", "gender": DogGender.MALE},
                {"name": "ليلى", "breed": "الراعي الألماني", "gender": DogGender.FEMALE},
                {"name": "صقر", "breed": "البلجيكي", "gender": DogGender.MALE},
                {"name": "عاصفة", "breed": "الراعي الألماني", "gender": DogGender.FEMALE},
            ]
            
            for i, dog_info in enumerate(dog_data):
                dog = Dog()
                dog.id = str(uuid4())
                dog.name = dog_info["name"]
                dog.code = f"DOG{i+1:03d}"
                dog.breed = dog_info["breed"]
                dog.gender = dog_info["gender"]
                dog.current_status = DogStatus.ACTIVE
                dog.birth_date = date(2020, 1, 1)
                db.session.add(dog)
                dogs.append(dog)
        
        # Commit initial data
        db.session.commit()
        print(f"✓ Projects: {len(projects)}, Employees: {len(employees)}, Dogs: {len(dogs)}")
        
        # Create attendance data for the last 7 days
        target_project = projects[0]
        today = date.today()
        
        for days_back in range(0, 7):
            target_date = today - timedelta(days=days_back)
            
            print(f"🗓️  Creating attendance data for {target_date.strftime('%Y-%m-%d')}")
            
            # Clear existing data for this date
            ProjectAttendanceReporting.query.filter(
                ProjectAttendanceReporting.project_id == target_project.id,
                ProjectAttendanceReporting.date == target_date
            ).delete()
            
            AttendanceDayLeave.query.filter(
                AttendanceDayLeave.project_id == target_project.id,
                AttendanceDayLeave.date == target_date
            ).delete()
            
            # Group 1 attendance records (with substitute employee)
            group_1_data = [
                {
                    "seq_no": 1,
                    "employee": employees[0] if len(employees) > 0 else None,
                    "substitute": employees[2] if len(employees) > 2 else None,
                    "dog": dogs[0] if len(dogs) > 0 else None,
                    "check_in": time(6, 0),
                    "check_out": time(14, 0),
                },
                {
                    "seq_no": 2, 
                    "employee": employees[1] if len(employees) > 1 else None,
                    "substitute": None,
                    "dog": dogs[1] if len(dogs) > 1 else None,
                    "check_in": time(6, 15),
                    "check_out": time(14, 15),
                },
                {
                    "seq_no": 3,
                    "employee": employees[3] if len(employees) > 3 else None,
                    "substitute": employees[4] if len(employees) > 4 else None,
                    "dog": dogs[2] if len(dogs) > 2 else None,
                    "check_in": time(6, 30),
                    "check_out": time(14, 30),
                },
            ]
            
            for record_data in group_1_data:
                attendance = ProjectAttendanceReporting()
                attendance.id = str(uuid4())
                attendance.project_id = target_project.id
                attendance.date = target_date
                attendance.group_no = 1
                attendance.seq_no = record_data["seq_no"]
                attendance.employee_id = record_data["employee"].id if record_data["employee"] else None
                attendance.substitute_employee_id = record_data["substitute"].id if record_data["substitute"] else None
                attendance.dog_id = record_data["dog"].id if record_data["dog"] else None
                attendance.check_in_time = record_data["check_in"]
                attendance.check_out_time = record_data["check_out"]
                attendance.status = AttendanceStatus.PRESENT
                db.session.add(attendance)
            
            # Group 2 attendance records (combined employee/substitute name)
            group_2_data = [
                {
                    "seq_no": 1,
                    "employee": employees[0] if len(employees) > 0 else None,
                    "substitute": None,
                    "dog": dogs[3] if len(dogs) > 3 else None,
                    "check_in": time(14, 0),
                    "check_out": time(22, 0),
                },
                {
                    "seq_no": 2,
                    "employee": None,
                    "substitute": employees[2] if len(employees) > 2 else None,
                    "dog": dogs[4] if len(dogs) > 4 else None,
                    "check_in": time(14, 15),
                    "check_out": time(22, 15),
                },
                {
                    "seq_no": 3,
                    "employee": employees[1] if len(employees) > 1 else None,
                    "substitute": None,
                    "dog": dogs[0] if len(dogs) > 0 else None,
                    "check_in": time(14, 30),
                    "check_out": time(22, 30),
                },
            ]
            
            for record_data in group_2_data:
                attendance = ProjectAttendanceReporting()
                attendance.id = str(uuid4())
                attendance.project_id = target_project.id
                attendance.date = target_date
                attendance.group_no = 2
                attendance.seq_no = record_data["seq_no"]
                attendance.employee_id = record_data["employee"].id if record_data["employee"] else None
                attendance.substitute_employee_id = record_data["substitute"].id if record_data["substitute"] else None
                attendance.dog_id = record_data["dog"].id if record_data["dog"] else None
                attendance.check_in_time = record_data["check_in"]
                attendance.check_out_time = record_data["check_out"]
                attendance.status = AttendanceStatus.PRESENT
                db.session.add(attendance)
            
            # Create some leave records
            if days_back < 3:  # Only for recent days
                leave_data = [
                    {
                        "seq_no": 1,
                        "employee": employees[4] if len(employees) > 4 else employees[0],
                        "leave_type": LeaveType.SICK_LEAVE,
                        "note": "إجازة مرضية - حمى"
                    },
                    {
                        "seq_no": 2,
                        "employee": employees[3] if len(employees) > 3 else employees[0],
                        "leave_type": LeaveType.ANNUAL_LEAVE,
                        "note": "إجازة سنوية"
                    },
                ]
                
                for leave_record in leave_data:
                    leave = AttendanceDayLeave()
                    leave.id = str(uuid4())
                    leave.project_id = target_project.id
                    leave.date = target_date
                    leave.seq_no = leave_record["seq_no"]
                    leave.employee_id = leave_record["employee"].id
                    leave.leave_type = leave_record["leave_type"]
                    leave.note = leave_record["note"]
                    db.session.add(leave)
        
        # Commit all attendance data
        db.session.commit()
        
        print(f"✅ Created attendance data for project: {target_project.name}")
        print(f"📊 Daily attendance records for last 7 days")
        print(f"🔗 Test URL: /reports/attendance/daily-sheet?project_id={target_project.id}&date={today.strftime('%Y-%m-%d')}")
        
        return target_project.id

if __name__ == "__main__":
    project_id = create_sample_attendance_data()
    print(f"\n🎯 Sample data created successfully!")
    print(f"📋 You can now test the daily sheet with project ID: {project_id}")