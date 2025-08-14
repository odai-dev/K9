#!/usr/bin/env python3
"""
Seed script to create sample data for the standalone attendance system.
"""

from datetime import date, time, datetime, timedelta
from app import app, db
from models import (
    Shift, ShiftAssignment, Attendance, Employee, Dog, User,
    EntityType, AttendanceStatus, AbsenceReason, UserRole, DogStatus
)

def create_sample_shifts():
    """Create sample shifts"""
    shifts_data = [
        {
            'name': 'الصباحية',
            'start_time': time(6, 0),
            'end_time': time(14, 0),
            'is_active': True
        },
        {
            'name': 'المسائية', 
            'start_time': time(14, 0),
            'end_time': time(22, 0),
            'is_active': True
        },
        {
            'name': 'الليلية',
            'start_time': time(22, 0),
            'end_time': time(6, 0),
            'is_active': True
        },
        {
            'name': 'نصف يوم',
            'start_time': time(8, 0),
            'end_time': time(12, 0),
            'is_active': True
        }
    ]
    
    created_shifts = []
    for shift_data in shifts_data:
        # Check if shift already exists
        existing = Shift.query.filter_by(name=shift_data['name']).first()
        if not existing:
            shift = Shift(**shift_data)
            db.session.add(shift)
            created_shifts.append(shift)
            print(f"Created shift: {shift.name}")
        else:
            created_shifts.append(existing)
            print(f"Shift already exists: {existing.name}")
    
    return created_shifts

def create_sample_assignments(shifts):
    """Create sample shift assignments"""
    # Get available employees and dogs (not assigned to projects)
    available_employees = Employee.query.filter_by(is_active=True).limit(10).all()
    available_dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).limit(8).all()
    
    assignments_created = 0
    
    # Assign employees to shifts
    for i, employee in enumerate(available_employees):
        shift = shifts[i % len(shifts)]  # Distribute across shifts
        
        # Check if assignment already exists
        existing = ShiftAssignment.query.filter_by(
            shift_id=shift.id,
            entity_type=EntityType.EMPLOYEE,
            entity_id=employee.id,
            is_active=True
        ).first()
        
        if not existing:
            assignment = ShiftAssignment(
                shift_id=shift.id,
                entity_type=EntityType.EMPLOYEE,
                entity_id=employee.id,
                is_active=True,
                assigned_date=date.today(),
                notes=f'تعيين تجريبي للموظف {employee.name}'
            )
            db.session.add(assignment)
            assignments_created += 1
            print(f"Assigned employee {employee.name} to shift {shift.name}")
    
    # Assign dogs to shifts 
    for i, dog in enumerate(available_dogs):
        shift = shifts[i % len(shifts)]  # Distribute across shifts
        
        # Check if assignment already exists
        existing = ShiftAssignment.query.filter_by(
            shift_id=shift.id,
            entity_type=EntityType.DOG,
            entity_id=dog.id,
            is_active=True
        ).first()
        
        if not existing:
            assignment = ShiftAssignment(
                shift_id=shift.id,
                entity_type=EntityType.DOG,
                entity_id=dog.id,
                is_active=True,
                assigned_date=date.today(),
                notes=f'تعيين تجريبي للكلب {dog.name}'
            )
            db.session.add(assignment)
            assignments_created += 1
            print(f"Assigned dog {dog.name} to shift {shift.name}")
    
    print(f"Created {assignments_created} new assignments")
    return assignments_created

def create_sample_attendance(shifts):
    """Create sample attendance records for the past week"""
    # Get user for recording attendance
    admin_user = User.query.filter_by(role=UserRole.GENERAL_ADMIN).first()
    if not admin_user:
        admin_user = User.query.first()
    
    if not admin_user:
        print("No users found to record attendance")
        return 0
    
    # Get all active assignments
    assignments = ShiftAssignment.query.filter_by(is_active=True).all()
    
    if not assignments:
        print("No assignments found to create attendance records")
        return 0
    
    records_created = 0
    
    # Create attendance records for the past 7 days
    for days_ago in range(7):
        attendance_date = date.today() - timedelta(days=days_ago)
        
        for assignment in assignments:
            # Check if record already exists
            existing = Attendance.query.filter_by(
                shift_id=assignment.shift_id,
                date=attendance_date,
                entity_type=assignment.entity_type,
                entity_id=assignment.entity_id
            ).first()
            
            if not existing:
                # Randomly assign attendance status for demo
                import random
                status_weights = [
                    (AttendanceStatus.PRESENT, 70),  # 70% present
                    (AttendanceStatus.ABSENT, 20),   # 20% absent  
                    (AttendanceStatus.LATE, 10)      # 10% late
                ]
                
                # Choose status based on weights
                statuses, weights = zip(*status_weights)
                status = random.choices(statuses, weights=weights)[0]
                
                # Set appropriate fields based on status
                absence_reason = None
                late_reason = None
                check_in_time = None
                check_out_time = None
                
                if status == AttendanceStatus.ABSENT:
                    absence_reasons = [AbsenceReason.ANNUAL, AbsenceReason.SICK, AbsenceReason.NO_REASON]
                    absence_reason = random.choice(absence_reasons)
                elif status == AttendanceStatus.LATE:
                    late_reason = "تأخير في المواصلات"
                    # Late check-in time
                    shift = assignment.shift
                    late_minutes = random.randint(10, 60)
                    check_in_datetime = datetime.combine(attendance_date, shift.start_time) + timedelta(minutes=late_minutes)
                    check_in_time = check_in_datetime.time()
                elif status == AttendanceStatus.PRESENT:
                    # Normal check-in time
                    shift = assignment.shift
                    early_minutes = random.randint(-15, 15)  # Can be early or on time
                    check_in_datetime = datetime.combine(attendance_date, shift.start_time) + timedelta(minutes=early_minutes)
                    check_in_time = check_in_datetime.time()
                
                attendance = Attendance(
                    shift_id=assignment.shift_id,
                    date=attendance_date,
                    entity_type=assignment.entity_type,
                    entity_id=assignment.entity_id,
                    status=status,
                    absence_reason=absence_reason,
                    late_reason=late_reason,
                    check_in_time=check_in_time,
                    check_out_time=check_out_time,
                    notes=f"سجل تجريبي لتاريخ {attendance_date}",
                    recorded_by_user_id=admin_user.id
                )
                
                db.session.add(attendance)
                records_created += 1
    
    print(f"Created {records_created} attendance records")
    return records_created

def main():
    """Main seeding function"""
    with app.app_context():
        print("Starting attendance system seeding...")
        
        try:
            # Create shifts
            print("\n1. Creating sample shifts...")
            shifts = create_sample_shifts()
            db.session.commit()
            
            # Create assignments
            print("\n2. Creating sample assignments...")
            assignments_count = create_sample_assignments(shifts)
            db.session.commit()
            
            # Create attendance records
            print("\n3. Creating sample attendance records...")
            attendance_count = create_sample_attendance(shifts)
            db.session.commit()
            
            print(f"\n✅ Attendance system seeding completed successfully!")
            print(f"Created {len(shifts)} shifts")
            print(f"Created {assignments_count} assignments")
            print(f"Created {attendance_count} attendance records")
            
        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    main()