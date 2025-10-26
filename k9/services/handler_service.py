"""
خدمات نظام السائس اليومي
Handler Daily System Services
"""
from app import db
from datetime import datetime, date, time, timedelta
from k9.models.models_handler_daily import (
    DailySchedule, DailyScheduleItem, HandlerReport,
    HandlerReportHealth, HandlerReportTraining, HandlerReportCare,
    HandlerReportBehavior, HandlerReportIncident, HandlerReportAttachment,
    Notification, ScheduleStatus, ScheduleItemStatus, ReportStatus,
    NotificationType
)
from k9.models.models import User, Employee, Dog, Project, Shift
from sqlalchemy import and_, or_
from typing import Optional, List, Dict
import os


class DailyScheduleService:
    """خدمة إدارة الجداول اليومية"""
    
    @staticmethod
    def create_schedule(date: date, project_id: Optional[str], created_by_user_id: str, notes: Optional[str] = None):
        """إنشاء جدول يومي جديد"""
        # Check if schedule already exists
        existing = DailySchedule.query.filter_by(date=date, project_id=project_id).first()
        if existing:
            return None, "يوجد جدول لهذا اليوم بالفعل"
        
        schedule = DailySchedule(
            date=date,
            project_id=project_id,
            created_by_user_id=created_by_user_id,
            notes=notes,
            status=ScheduleStatus.OPEN
        )
        db.session.add(schedule)
        db.session.commit()
        
        return schedule, None
    
    @staticmethod
    def add_schedule_item(schedule_id: str, employee_id: str, dog_id: Optional[str], 
                         shift_id: Optional[str]) -> tuple:
        """إضافة عنصر للجدول"""
        item = DailyScheduleItem(
            daily_schedule_id=schedule_id,
            employee_id=employee_id,
            dog_id=dog_id,
            shift_id=shift_id,
            status=ScheduleItemStatus.PLANNED
        )
        db.session.add(item)
        db.session.commit()
        return item, None
    
    @staticmethod
    def mark_present(item_id: str) -> bool:
        """تسجيل حضور"""
        item = DailyScheduleItem.query.get(item_id)
        if item:
            item.status = ScheduleItemStatus.PRESENT
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def mark_absent(item_id: str, reason: str) -> bool:
        """تسجيل غياب"""
        item = DailyScheduleItem.query.get(item_id)
        if item:
            item.status = ScheduleItemStatus.ABSENT
            item.absence_reason = reason
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def replace_employee(item_id: str, replacement_employee_id: str, reason: str, notes: Optional[str] = None) -> bool:
        """استبدال موظف"""
        item = DailyScheduleItem.query.get(item_id)
        if item:
            item.status = ScheduleItemStatus.REPLACED
            item.replacement_employee_id = replacement_employee_id
            item.absence_reason = reason
            item.replacement_notes = notes
            db.session.commit()
            
            # Get the user_id from employee
            replacement_employee = Employee.query.get(replacement_employee_id)
            if replacement_employee and replacement_employee.user_account_id:
                # Create notification for replacement employee's user account
                NotificationService.create_notification(
                    user_id=replacement_employee.user_account_id,
                    notification_type=NotificationType.EMPLOYEE_REPLACED,
                    title="تم تكليفك كبديل",
                    message=f"تم تكليفك كبديل في جدول {item.schedule.date}",
                    related_id=str(item_id),
                    related_type="DailyScheduleItem"
                )
            return True
        return False
    
    @staticmethod
    def lock_schedule(schedule_id: str) -> tuple:
        """إقفال الجدول اليومي"""
        schedule = DailySchedule.query.get(schedule_id)
        if not schedule:
            return False, "الجدول غير موجود"
        
        if schedule.status == ScheduleStatus.LOCKED:
            return False, "الجدول مقفل بالفعل"
        
        schedule.status = ScheduleStatus.LOCKED
        db.session.commit()
        return True, "تم إقفال الجدول بنجاح"
    
    @staticmethod
    def get_handler_schedule_for_date(handler_user_id: str, target_date: date):
        """الحصول على جدول السائس ليوم معين"""
        user = User.query.get(handler_user_id)
        if not user or not user.project_id:
            return []
        
        schedule = DailySchedule.query.filter_by(
            date=target_date,
            project_id=user.project_id
        ).first()
        
        if not schedule:
            return []
        
        # Get employee associated with this user
        employee = Employee.query.filter_by(user_account_id=handler_user_id).first()
        if not employee:
            return []
        
        items = DailyScheduleItem.query.filter(
            and_(
                DailyScheduleItem.daily_schedule_id == schedule.id,
                or_(
                    DailyScheduleItem.employee_id == employee.id,
                    DailyScheduleItem.replacement_employee_id == employee.id
                )
            )
        ).all()
        
        return items
    
    @staticmethod
    def notify_handlers_of_new_schedule(schedule_id: str):
        """إرسال إشعارات للسائسين بالجدول الجديد"""
        schedule = DailySchedule.query.get(schedule_id)
        if not schedule:
            return
        
        # Get all schedule items
        items = DailyScheduleItem.query.filter_by(daily_schedule_id=schedule_id).all()
        
        # Notify each handler
        for item in items:
            # Get handler user ID from employee
            if item.handler_user_id:
                # Direct user ID is available
                handler_user_id = item.handler_user_id
            elif item.employee_id:
                # Get user ID from employee
                employee = Employee.query.get(item.employee_id)
                if employee and employee.user_account_id:
                    handler_user_id = employee.user_account_id
                else:
                    continue
            else:
                continue
            
            # Create notification
            NotificationService.create_notification(
                user_id=str(handler_user_id),
                notification_type=NotificationType.SCHEDULE_CREATED,
                title="جدول يومي جديد",
                message=f"تم إنشاء جدول جديد لتاريخ {schedule.date.strftime('%Y-%m-%d')}",
                related_id=str(schedule_id),
                related_type="DailySchedule"
            )


class HandlerReportService:
    """خدمة إدارة تقارير السائس"""
    
    @staticmethod
    def can_submit_report(handler_user_id: str, schedule_item_id: str, grace_minutes: int = 240) -> tuple:
        """التحقق من إمكانية تقديم التقرير"""
        item = DailyScheduleItem.query.get(schedule_item_id)
        if not item or not item.shift:
            return False, "لم يتم العثور على الوردية"
        
        # Get shift end time
        shift = item.shift
        if not shift.end_time:
            return False, "وقت نهاية الوردية غير محدد"
        
        # Combine schedule date with shift end time
        shift_end_datetime = datetime.combine(item.schedule.date, shift.end_time)
        grace_period = timedelta(minutes=grace_minutes)
        allowed_time = shift_end_datetime + grace_period
        
        now = datetime.now()
        
        if now < shift_end_datetime:
            return False, f"لا يمكن تقديم التقرير قبل انتهاء الوردية. انتهاء الوردية: {shift_end_datetime.strftime('%H:%M')}"
        
        if now > allowed_time:
            return False, f"انتهت فترة السماح لتقديم التقرير. آخر موعد كان: {allowed_time.strftime('%Y-%m-%d %H:%M')}"
        
        return True, None
    
    @staticmethod
    def create_report(handler_user_id: str, dog_id: str, schedule_item_id: Optional[str],
                     project_id: Optional[str], location: Optional[str], report_date: Optional[date] = None) -> tuple:
        """إنشاء تقرير جديد"""
        if report_date is None:
            report_date = date.today()
        
        report = HandlerReport(
            date=report_date,
            schedule_item_id=schedule_item_id,
            handler_user_id=handler_user_id,
            dog_id=dog_id,
            project_id=project_id,
            location=location,
            status=ReportStatus.DRAFT
        )
        
        # Create related sections
        report.health = HandlerReportHealth(report=report)
        report.care = HandlerReportCare(report=report)
        report.behavior = HandlerReportBehavior(report=report)
        
        db.session.add(report)
        db.session.commit()
        
        return report, None
    
    @staticmethod
    def submit_report(report_id: str) -> tuple:
        """إرسال التقرير للمراجعة"""
        report = HandlerReport.query.get(report_id)
        if not report:
            return False, "التقرير غير موجود"
        
        if report.status != ReportStatus.DRAFT:
            return False, "التقرير تم إرساله مسبقاً"
        
        report.status = ReportStatus.SUBMITTED
        report.submitted_at = datetime.utcnow()
        db.session.commit()
        
        # Notify project manager
        if report.project_id:
            from k9.models.models import Project, Employee
            project = Project.query.get(report.project_id)
            
            if project and project.project_manager_id:
                # Find user account for project manager
                employee = Employee.query.get(project.project_manager_id)
                if employee and employee.user_account_id:
                    NotificationService.create_notification(
                        user_id=str(employee.user_account_id),
                        notification_type=NotificationType.REPORT_SUBMITTED,
                        title="تقرير سائس جديد",
                        message=f"تم رفع تقرير جديد من السائس بتاريخ {report.date.strftime('%Y-%m-%d')} - المشروع: {project.name}",
                        related_id=str(report_id),
                        related_type="HandlerReport"
                    )
        
        # Notify all admins
        from k9.models.models import UserRole
        admins = User.query.filter_by(role=UserRole.GENERAL_ADMIN, is_active=True).all()
        for admin in admins:
            NotificationService.create_notification(
                user_id=str(admin.id),
                notification_type=NotificationType.REPORT_SUBMITTED,
                title="تقرير سائس جديد",
                message=f"تم رفع تقرير جديد من السائس بتاريخ {report.date.strftime('%Y-%m-%d')}",
                related_id=str(report_id),
                related_type="HandlerReport"
            )
        
        return True, None
    
    @staticmethod
    def approve_report(report_id: str, reviewer_user_id: str, notes: Optional[str] = None) -> tuple:
        """اعتماد التقرير"""
        report = HandlerReport.query.get(report_id)
        if not report:
            return False, "التقرير غير موجود"
        
        report.status = ReportStatus.APPROVED
        report.reviewed_by_user_id = reviewer_user_id
        report.reviewed_at = datetime.utcnow()
        report.review_notes = notes
        db.session.commit()
        
        # Notify handler
        NotificationService.create_notification(
            user_id=str(report.handler_user_id),
            notification_type=NotificationType.REPORT_APPROVED,
            title="تم اعتماد التقرير",
            message=f"تم اعتماد تقريرك بتاريخ {report.date}",
            related_id=str(report_id),
            related_type="HandlerReport"
        )
        
        return True, None
    
    @staticmethod
    def reject_report(report_id: str, reviewer_user_id: str, notes: str) -> tuple:
        """رفض التقرير"""
        report = HandlerReport.query.get(report_id)
        if not report:
            return False, "التقرير غير موجود"
        
        report.status = ReportStatus.REJECTED
        report.reviewed_by_user_id = reviewer_user_id
        report.reviewed_at = datetime.utcnow()
        report.review_notes = notes
        db.session.commit()
        
        # Notify handler
        NotificationService.create_notification(
            user_id=str(report.handler_user_id),
            notification_type=NotificationType.REPORT_REJECTED,
            title="تم رفض التقرير",
            message=f"تم رفض تقريرك بتاريخ {report.date}. السبب: {notes}",
            related_id=str(report_id),
            related_type="HandlerReport"
        )
        
        return True, None


class NotificationService:
    """خدمة إدارة الإشعارات"""
    
    @staticmethod
    def create_notification(user_id: str, notification_type: NotificationType,
                          title: str, message: str,
                          related_id: Optional[str] = None,
                          related_type: Optional[str] = None):
        """إنشاء إشعار جديد"""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            related_id=related_id,
            related_type=related_type,
            read=False
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    
    @staticmethod
    def get_user_notifications(user_id: str, unread_only: bool = False, limit: int = 50):
        """الحصول على إشعارات المستخدم"""
        query = Notification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(read=False)
        
        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
        return notifications
    
    @staticmethod
    def mark_as_read(notification_id: str) -> bool:
        """تعليم الإشعار كمقروء"""
        notification = Notification.query.get(notification_id)
        if notification:
            notification.mark_as_read()
            return True
        return False
    
    @staticmethod
    def mark_all_as_read(user_id: str) -> int:
        """تعليم جميع الإشعارات كمقروءة"""
        notifications = Notification.query.filter_by(user_id=user_id, read=False).all()
        count = len(notifications)
        for notif in notifications:
            notif.mark_as_read()
        return count
    
    @staticmethod
    def get_unread_count(user_id: str) -> int:
        """الحصول على عدد الإشعارات غير المقروءة"""
        return Notification.query.filter_by(user_id=user_id, read=False).count()


class AttachmentService:
    """خدمة إدارة المرفقات"""
    
    @staticmethod
    def save_attachment(file, incident_id: str, upload_folder: str) -> tuple:
        """حفظ مرفق مع SHA256"""
        import hashlib
        from werkzeug.utils import secure_filename
        import uuid
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'pdf', 'gif'}
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext not in allowed_extensions:
            return None, "نوع الملف غير مسموح"
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        
        # Create directory structure: uploads/handler_reports/YYYY/MM/
        now = datetime.now()
        relative_path = os.path.join('handler_reports', str(now.year), f"{now.month:02d}")
        full_dir = os.path.join(upload_folder, relative_path)
        os.makedirs(full_dir, exist_ok=True)
        
        file_path = os.path.join(full_dir, unique_filename)
        
        # Read file content and calculate SHA256
        file_content = file.read()
        sha256_hash = hashlib.sha256(file_content).hexdigest()
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Determine file type
        file_type = 'pdf' if file_ext == 'pdf' else 'image'
        
        # Create attachment record
        attachment = HandlerReportAttachment(
            incident_id=incident_id,
            filename=unique_filename,
            original_filename=filename,
            file_path=os.path.join(relative_path, unique_filename),
            file_type=file_type,
            file_size=len(file_content),
            sha256_hash=sha256_hash
        )
        
        db.session.add(attachment)
        db.session.commit()
        
        return attachment, None
