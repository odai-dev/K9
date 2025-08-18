"""
Database models for attendance reporting
Defines the data structures for daily sheet and attendance leave tracking
"""

from datetime import datetime, date, time
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, String, Integer, Date, Time, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

from app import db


class AttendanceStatus(Enum):
    """Status of employee attendance"""
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    SICK = "SICK"
    LEAVE = "LEAVE"
    REMOTE = "REMOTE"
    OVERTIME = "OVERTIME"


class LeaveType(Enum):
    """Types of employee leave"""
    ANNUAL = "ANNUAL"
    SICK = "SICK"
    EMERGENCY = "EMERGENCY"
    OTHER = "OTHER"


class ProjectAttendanceReporting(db.Model):
    """
    Table for project-based attendance tracking for daily sheet reports
    This table provides a printable format for attendance tracking
    """
    __tablename__ = 'project_attendance_reporting'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    date = Column(Date, nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey('project.id'), nullable=False, index=True)
    shift_id = Column(UUID(as_uuid=True), ForeignKey('project_shift.id'), nullable=True)
    
    # Group and sequence for table layout (Group 1 = 8 columns, Group 2 = 7 columns)
    group_no = Column(Integer, nullable=False, default=1)  # 1 or 2
    seq_no = Column(Integer, nullable=False, default=1)   # Sequential number within group
    
    # Attendance details
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employee.id'), nullable=True)
    substitute_employee_id = Column(UUID(as_uuid=True), ForeignKey('employee.id'), nullable=True)
    dog_id = Column(UUID(as_uuid=True), ForeignKey('dog.id'), nullable=True)
    
    # Times
    check_in_time = Column(Time, nullable=True)
    check_out_time = Column(Time, nullable=True)
    
    # Status
    status = Column(SQLEnum(AttendanceStatus), nullable=False, default=AttendanceStatus.PRESENT)
    
    # Project control flag
    is_project_controlled = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", backref="attendance_reporting_entries")
    employee = relationship("Employee", foreign_keys=[employee_id], backref="reporting_attendance_records")
    substitute_employee = relationship("Employee", foreign_keys=[substitute_employee_id], backref="reporting_substitute_records")
    dog = relationship("Dog", backref="reporting_attendance_records")
    shift = relationship("ProjectShift", backref="reporting_attendance_records")
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('project_id', 'date', 'group_no', 'seq_no', name='uq_attendance_print_slot'),
        db.Index('ix_attendance_project_date', 'project_id', 'date'),
        db.Index('ix_attendance_group_seq', 'project_id', 'date', 'group_no', 'seq_no'),
    )

    def __repr__(self):
        return f'<ProjectAttendanceReporting {self.project_id} {self.date} G{self.group_no}#{self.seq_no}>'


class AttendanceDayLeave(db.Model):
    """
    Table for tracking employee leaves on specific dates for daily sheet reports
    """
    __tablename__ = 'attendance_day_leave'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('project.id'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    seq_no = Column(Integer, nullable=False, default=1)  # Sequential number for printing
    
    # Leave details
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employee.id'), nullable=True)
    leave_type = Column(SQLEnum(LeaveType), nullable=False)
    note = Column(String(250), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", backref="attendance_day_leaves")
    employee = relationship("Employee", backref="attendance_day_leaves")
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('project_id', 'date', 'seq_no', name='uq_dayleave_print_slot'),
        db.Index('ix_dayleave_project_date', 'project_id', 'date'),
    )

    def __repr__(self):
        return f'<AttendanceDayLeave {self.project_id} {self.date} #{self.seq_no}>'