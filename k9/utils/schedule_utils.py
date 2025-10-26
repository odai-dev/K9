"""
Utility functions for daily schedule management
"""
from datetime import date, datetime, timedelta
from k9.models.models_handler_daily import DailySchedule, ScheduleStatus
from k9.services.handler_service import NotificationService, DailyScheduleService
from k9.models.models_handler_daily import NotificationType
from app import db


def auto_lock_yesterday_schedules():
    """
    Automatically lock all schedules from yesterday
    This should be run as a cron job at the end of each day
    """
    yesterday = date.today() - timedelta(days=1)
    
    schedules = DailySchedule.query.filter(
        db.and_(
            DailySchedule.date <= yesterday,
            DailySchedule.status == ScheduleStatus.OPEN
        )
    ).all()
    
    locked_count = 0
    for schedule in schedules:
        if DailyScheduleService.lock_schedule(str(schedule.id)):
            locked_count += 1
    
    return locked_count


def cleanup_old_notifications(days=30):
    """
    Clean up notifications older than specified days
    """
    from k9.models.models_handler_daily import Notification
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    old_notifications = Notification.query.filter(
        db.and_(
            Notification.created_at < cutoff_date,
            Notification.read == True
        )
    ).all()
    
    count = len(old_notifications)
    for notif in old_notifications:
        db.session.delete(notif)
    
    db.session.commit()
    return count
