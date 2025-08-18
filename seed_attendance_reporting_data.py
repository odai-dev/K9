#!/usr/bin/env python3
"""
Sample data seeding script for attendance reporting system
Creates test data for daily sheet functionality
"""

import os
import sys
from datetime import date, time, datetime
from uuid import uuid4

# Add current directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Project, Employee, Dog
from models_attendance_reporting import ProjectAttendanceReporting, AttendanceDayLeave, AttendanceStatus, LeaveType


def seed_attendance_data():
    """Create sample attendance reporting data"""
    
    with app.app_context():
        print("🌱 Seeding attendance reporting data...")
        
        # Get first project for testing
        project = Project.query.first()
        if not project:
            print("❌ No projects found. Please create a project first.")
            return
        
        print(f"📋 Using project: {project.name}")
        
        # Get some employees for testing
        employees = Employee.query.limit(5).all()
        if len(employees) < 2:
            print("❌ Need at least 2 employees for testing.")
            return
        
        # Get some dogs for testing
        dogs = Dog.query.limit(3).all()
        if len(dogs) < 2:
            print("❌ Need at least 2 dogs for testing.")
            return
        
        # Target date for the report (today)
        target_date = date.today()
        
        # Clear existing data for this project and date
        ProjectAttendanceReporting.query.filter_by(
            project_id=project.id, 
            date=target_date
        ).delete()
        
        AttendanceDayLeave.query.filter_by(
            project_id=project.id, 
            date=target_date
        ).delete()
        
        # Create Group 1 attendance records (8-column format)
        group_1_records = [
            {
                "seq_no": 1,
                "employee_id": employees[0].id,
                "substitute_employee_id": employees[1].id,
                "dog_id": dogs[0].id,
                "check_in_time": time(7, 30),
                "check_out_time": time(15, 30),
                "status": AttendanceStatus.PRESENT
            },
            {
                "seq_no": 2,
                "employee_id": employees[1].id,
                "substitute_employee_id": None,
                "dog_id": dogs[1].id,
                "check_in_time": time(8, 0),
                "check_out_time": time(16, 0),
                "status": AttendanceStatus.PRESENT
            },
            {
                "seq_no": 3,
                "employee_id": employees[2].id if len(employees) > 2 else None,
                "substitute_employee_id": None,
                "dog_id": dogs[2].id if len(dogs) > 2 else None,
                "check_in_time": time(7, 45),
                "check_out_time": None,  # Still on duty
                "status": AttendanceStatus.PRESENT
            }
        ]
        
        for record_data in group_1_records:
            record = ProjectAttendanceReporting(
                project_id=project.id,
                date=target_date,
                group_no=1,
                **record_data
            )
            db.session.add(record)
        
        # Create Group 2 attendance records (7-column format)
        group_2_records = [
            {
                "seq_no": 1,
                "employee_id": employees[3].id if len(employees) > 3 else employees[0].id,
                "dog_id": dogs[0].id,
                "check_in_time": time(6, 0),
                "check_out_time": time(14, 0),
                "status": AttendanceStatus.PRESENT
            },
            {
                "seq_no": 2,
                "employee_id": employees[4].id if len(employees) > 4 else employees[1].id,
                "dog_id": dogs[1].id,
                "check_in_time": time(14, 0),
                "check_out_time": time(22, 0),
                "status": AttendanceStatus.PRESENT
            }
        ]
        
        for record_data in group_2_records:
            record = ProjectAttendanceReporting(
                project_id=project.id,
                date=target_date,
                group_no=2,
                **record_data
            )
            db.session.add(record)
        
        # Create leave records
        leave_records = [
            {
                "seq_no": 1,
                "employee_id": employees[2].id if len(employees) > 2 else employees[0].id,
                "leave_type": LeaveType.ANNUAL,
                "note": "إجازة سنوية"
            },
            {
                "seq_no": 2,
                "employee_id": employees[1].id,
                "leave_type": LeaveType.SICK,
                "note": "إجازة مرضية"
            }
        ]
        
        for leave_data in leave_records:
            leave = AttendanceDayLeave(
                project_id=project.id,
                date=target_date,
                **leave_data
            )
            db.session.add(leave)
        
        # Commit all changes
        db.session.commit()
        
        print(f"✅ Successfully created attendance data for {target_date}")
        print(f"   - {len(group_1_records)} Group 1 records")
        print(f"   - {len(group_2_records)} Group 2 records") 
        print(f"   - {len(leave_records)} leave records")
        print(f"🌐 Access the daily sheet at: /reports/attendance/daily-sheet?project_id={project.id}&date={target_date}")


if __name__ == "__main__":
    seed_attendance_data()