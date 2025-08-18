"""
New models for attendance reporting system (Daily Sheet)
Extends existing ProjectAttendance for specialized reporting needs
"""
from datetime import datetime, date
from enum import Enum
from app import db
from models import get_uuid_column, default_uuid

# New enums for attendance reporting
class AttendanceStatus(Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    SICK = "SICK"
    LEAVE = "LEAVE"
    REMOTE = "REMOTE"
    OVERTIME = "OVERTIME"

class LeaveType(Enum):
    ANNUAL = "ANNUAL"
    SICK = "SICK" 
    EMERGENCY = "EMERGENCY"
    OTHER = "OTHER"

class ProjectAttendance(db.Model):
    """
    Extended ProjectAttendance model for daily sheet reporting
    This extends the existing ProjectAttendance with additional fields needed for the daily sheet report
    """
    __tablename__ = 'project_attendance_reporting'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    date = db.Column(db.Date, nullable=False)
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=False)
    shift_id = db.Column(get_uuid_column(), db.ForeignKey('project_shift.id'), nullable=True)
    
    # Group and sequence for printing layout (Group 1 = left block, Group 2 = right block)
    group_no = db.Column(db.Integer, default=1, nullable=False)  # 1 or 2
    seq_no = db.Column(db.Integer, default=1, nullable=False)   # row order within group
    
    # Employee assignment
    employee_id = db.Column(get_uuid_column(), db.ForeignKey('employee.id'), nullable=True)
    substitute_employee_id = db.Column(get_uuid_column(), db.ForeignKey('employee.id'), nullable=True)  # for group 1
    
    # Dog assignment
    dog_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'), nullable=True)
    
    # Time tracking
    check_in_time = db.Column(db.Time, nullable=True)
    check_out_time = db.Column(db.Time, nullable=True)
    
    # Status and control
    status = db.Column(db.Enum(AttendanceStatus), nullable=False, default=AttendanceStatus.PRESENT)
    is_project_controlled = db.Column(db.Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='daily_attendance_records')
    employee = db.relationship('Employee', foreign_keys=[employee_id], backref='daily_attendance_records')
    substitute_employee = db.relationship('Employee', foreign_keys=[substitute_employee_id], backref='substitute_attendance_records')
    dog = db.relationship('Dog', backref='daily_attendance_records')
    shift = db.relationship('ProjectShift', backref='daily_attendance_records')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('ix_attendance_date', 'date'),
        db.Index('ix_attendance_project_date', 'project_id', 'date'),
        db.Index('ix_attendance_group_seq', 'project_id', 'date', 'group_no', 'seq_no'),
        db.UniqueConstraint('project_id', 'date', 'group_no', 'seq_no', name='uq_attendance_print_slot'),
    )
    
    def __repr__(self):
        entity_name = self.employee.name if self.employee else (self.dog.name if self.dog else "Unknown")
        return f'<ProjectAttendanceReporting {entity_name} - Group {self.group_no}, Seq {self.seq_no} on {self.date}>'

class AttendanceDayLeave(db.Model):
    """
    Model for tracking employees on leave for the daily sheet report
    Powers the "employees on leave" mini-table at the bottom of the report
    """
    __tablename__ = 'attendance_day_leave'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    seq_no = db.Column(db.Integer, nullable=False, default=1)  # row order in the leave table
    
    employee_id = db.Column(get_uuid_column(), db.ForeignKey('employee.id'), nullable=True)
    leave_type = db.Column(db.Enum(LeaveType), nullable=False)
    note = db.Column(db.String(250), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='daily_leave_records')
    employee = db.relationship('Employee', backref='daily_leave_records')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('ix_dayleave_date', 'date'),
        db.Index('ix_dayleave_project_date', 'project_id', 'date'),
        db.UniqueConstraint('project_id', 'date', 'seq_no', name='uq_dayleave_print_slot'),
    )
    
    def __repr__(self):
        employee_name = self.employee.name if self.employee else "Unknown"
        return f'<AttendanceDayLeave {employee_name} - {self.leave_type.value} on {self.date}>'