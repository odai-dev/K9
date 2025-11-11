"""
Database models for attendance reporting
LEGACY FILE - Models removed as part of migration to DailySchedule system
All attendance tracking now uses DailySchedule and DailyScheduleItem models from models_handler_daily.py
"""

# Legacy attendance reporting models removed:
# - ProjectAttendanceReporting
# - AttendanceDayLeave  
# - PMDailyEvaluation
# - AttendanceStatus enum (moved to models.py for standalone attendance)
# - LeaveType enum (no longer needed)
#
# See migration: migrations/versions/[timestamp]_drop_legacy_attendance_reporting.py