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
    ShiftReport, ShiftReportHealth, ShiftReportBehavior, ShiftReportIncident, ShiftReportAttachment,
    Notification, ScheduleStatus, ScheduleItemStatus, ReportStatus,
    NotificationType, ReportType
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
        
        schedule = DailySchedule(  # type: ignore
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
    def add_schedule_item(schedule_id: str, handler_user_id: str, dog_id: Optional[str], 
                         shift_id: Optional[str], location_id: Optional[str] = None) -> tuple:
        """إضافة عنصر للجدول"""
        item = DailyScheduleItem(  # type: ignore
            daily_schedule_id=schedule_id,
            handler_user_id=handler_user_id,
            dog_id=dog_id,
            shift_id=shift_id,
            location_id=location_id,
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
    def replace_handler(item_id: str, replacement_handler_id: str, reason: str, notes: Optional[str] = None) -> bool:
        """استبدال سائس"""
        item = DailyScheduleItem.query.get(item_id)
        if item:
            item.status = ScheduleItemStatus.REPLACED
            item.replacement_handler_id = replacement_handler_id
            item.absence_reason = reason
            item.replacement_notes = notes
            db.session.commit()
            
            # Create notification for replacement handler
            NotificationService.create_notification(
                user_id=str(replacement_handler_id),
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
        
        # Query schedule items for this handler (either as primary or replacement)
        items = DailyScheduleItem.query.filter(
            and_(
                DailyScheduleItem.daily_schedule_id == schedule.id,
                or_(
                    DailyScheduleItem.handler_user_id == handler_user_id,
                    DailyScheduleItem.replacement_handler_id == handler_user_id
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
            if item.handler_user_id:
                # Create notification
                NotificationService.create_notification(
                    user_id=str(item.handler_user_id),
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
    def can_create_daily_report(dog_id: str, report_date: date) -> tuple:
        """التحقق من إمكانية إنشاء تقرير يومي - منع التكرار لنفس الكلب في نفس اليوم"""
        # Check if daily report already exists for this dog on this date
        existing = HandlerReport.query.filter_by(
            dog_id=dog_id,
            date=report_date,
            report_type=ReportType.DAILY
        ).first()
        
        if existing:
            return False, f"يوجد تقرير يومي لهذا الكلب بتاريخ {report_date.strftime('%Y-%m-%d')} بالفعل"
        
        return True, None
    
    @staticmethod
    def get_dogs_worked_today(handler_user_id: str, target_date: Optional[date] = None) -> List[Dict]:
        """الحصول على قائمة الكلاب التي عمل معها السائس اليوم مع حالة التقارير"""
        if target_date is None:
            target_date = date.today()
        
        # Get user and project
        user = User.query.get(handler_user_id)
        if not user or not user.project_id:
            return []
        
        schedule = DailySchedule.query.filter_by(
            date=target_date,
            project_id=user.project_id
        ).first()
        
        if not schedule:
            return []
        
        # Get schedule items where this handler is assigned (as primary or replacement)
        items = DailyScheduleItem.query.filter(
            and_(
                DailyScheduleItem.daily_schedule_id == schedule.id,
                or_(
                    DailyScheduleItem.handler_user_id == handler_user_id,
                    DailyScheduleItem.replacement_handler_id == handler_user_id
                )
            )
        ).all()
        
        dogs_info = []
        seen_dogs = set()
        
        for item in items:
            if not item.dog_id or str(item.dog_id) in seen_dogs:
                continue
            
            seen_dogs.add(str(item.dog_id))
            
            # Check if shift report exists
            shift_report = ShiftReport.query.filter_by(schedule_item_id=item.id).first()
            
            # Check if daily report exists
            daily_report = HandlerReport.query.filter_by(
                dog_id=item.dog_id,
                date=target_date,
                report_type=ReportType.DAILY
            ).first()
            
            dogs_info.append({
                'dog': item.dog,
                'dog_id': str(item.dog_id),
                'shift_report': shift_report,
                'daily_report': daily_report,
                'has_shift_report': shift_report is not None,
                'has_daily_report': daily_report is not None,
                'schedule_item': item
            })
        
        return dogs_info
    
    @staticmethod
    def get_shift_reports_for_prepopulation(dog_id: str, report_date: date) -> List[ShiftReport]:
        """الحصول على تقارير الورديات لكلب معين في يوم معين لملء التقرير اليومي"""
        shift_reports = ShiftReport.query.filter_by(
            dog_id=dog_id,
            date=report_date
        ).all()
        
        return shift_reports
    
    @staticmethod
    def create_report(handler_user_id: str, dog_id: str, schedule_item_id: Optional[str],
                     project_id: Optional[str], location: Optional[str], report_date: Optional[date] = None,
                     report_type: ReportType = ReportType.DAILY) -> tuple:
        """إنشاء تقرير جديد"""
        if report_date is None:
            report_date = date.today()
        
        # Validate for daily reports only (shift reports are validated separately)
        if report_type == ReportType.DAILY:
            can_create, error = HandlerReportService.can_create_daily_report(dog_id, report_date)
            if not can_create:
                return None, error
        
        report = HandlerReport(  # type: ignore
            date=report_date,
            report_type=report_type,
            schedule_item_id=schedule_item_id,
            handler_user_id=handler_user_id,
            dog_id=dog_id,
            project_id=project_id,
            location=location,
            status=ReportStatus.DRAFT
        )
        
        # Create related sections
        report.health = HandlerReportHealth(report=report)  # type: ignore
        report.care = HandlerReportCare(report=report)  # type: ignore
        report.behavior = HandlerReportBehavior(report=report)  # type: ignore
        
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
                if employee and employee.user_account is not None:
                    NotificationService.create_notification(
                        user_id=str(employee.user_account.id),
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


class ShiftReportService:
    """خدمة إدارة تقارير الوردية"""
    
    @staticmethod
    def can_create_shift_report(schedule_item_id: str) -> tuple:
        """التحقق من إمكانية إنشاء تقرير وردية"""
        item = DailyScheduleItem.query.get(schedule_item_id)
        if not item or not item.shift:
            return False, "لم يتم العثور على عنصر الجدول أو الوردية"
        
        # Check if shift report already exists for this schedule item
        existing = ShiftReport.query.filter_by(schedule_item_id=schedule_item_id).first()
        if existing:
            return False, "يوجد تقرير وردية لهذا العنصر بالفعل"
        
        # Timing validation: Can only create from shift end until end of same day
        shift = item.shift
        if not shift.end_time:
            return False, "وقت نهاية الوردية غير محدد"
        
        # Combine schedule date with shift end time
        shift_end_datetime = datetime.combine(item.schedule.date, shift.end_time)
        
        # End of same day (23:59:59)
        day_end = datetime.combine(item.schedule.date, time(23, 59, 59))
        
        now = datetime.now()
        
        if now < shift_end_datetime:
            return False, f"لا يمكن إنشاء التقرير قبل انتهاء الوردية. انتهاء الوردية: {shift_end_datetime.strftime('%H:%M')}"
        
        if now > day_end:
            return False, f"انتهت فترة تقديم تقرير الوردية. آخر موعد كان: {day_end.strftime('%Y-%m-%d %H:%M')}"
        
        return True, None
    
    @staticmethod
    def create_shift_report(schedule_item_id: str, handler_user_id: str, 
                           dog_id: str, project_id: str, report_date: date,
                           location: Optional[str] = None) -> tuple:
        """إنشاء تقرير وردية جديد"""
        # Verify can create
        can_create, error = ShiftReportService.can_create_shift_report(schedule_item_id)
        if not can_create:
            return None, error
        
        # Create shift report
        shift_report = ShiftReport(  # type: ignore
            schedule_item_id=schedule_item_id,
            handler_user_id=handler_user_id,
            dog_id=dog_id,
            project_id=project_id,
            date=report_date,
            location=location,
            status=ReportStatus.DRAFT
        )
        
        # Create related sections (only 3 for shift reports)
        shift_report.health = ShiftReportHealth(shift_report=shift_report)  # type: ignore
        shift_report.behavior = ShiftReportBehavior(shift_report=shift_report)  # type: ignore
        
        db.session.add(shift_report)
        db.session.commit()
        
        return shift_report, None
    
    @staticmethod
    def submit_shift_report(shift_report_id: str) -> tuple:
        """إرسال تقرير الوردية للمراجعة"""
        shift_report = ShiftReport.query.get(shift_report_id)
        if not shift_report:
            return False, "التقرير غير موجود"
        
        if shift_report.status != ReportStatus.DRAFT:
            return False, "التقرير تم إرساله مسبقاً"
        
        shift_report.status = ReportStatus.SUBMITTED
        shift_report.submitted_at = datetime.utcnow()
        db.session.commit()
        
        # Notify project manager
        if shift_report.project_id:
            from k9.models.models import Project, Employee
            project = Project.query.get(shift_report.project_id)
            
            if project and project.project_manager_id:
                employee = Employee.query.get(project.project_manager_id)
                if employee and employee.user_account is not None:
                    NotificationService.create_notification(
                        user_id=str(employee.user_account.id),
                        notification_type=NotificationType.REPORT_SUBMITTED,
                        title="تقرير وردية جديد",
                        message=f"تم رفع تقرير وردية جديد بتاريخ {shift_report.date.strftime('%Y-%m-%d')} - المشروع: {project.name}",
                        related_id=str(shift_report_id),
                        related_type="ShiftReport"
                    )
        
        # Notify all admins
        from k9.models.models import UserRole
        admins = User.query.filter_by(role=UserRole.GENERAL_ADMIN, is_active=True).all()
        for admin in admins:
            NotificationService.create_notification(
                user_id=str(admin.id),
                notification_type=NotificationType.REPORT_SUBMITTED,
                title="تقرير وردية جديد",
                message=f"تم رفع تقرير وردية جديد بتاريخ {shift_report.date.strftime('%Y-%m-%d')}",
                related_id=str(shift_report_id),
                related_type="ShiftReport"
            )
        
        return True, None
    
    @staticmethod
    def approve_shift_report(shift_report_id: str, reviewer_user_id: str, notes: Optional[str] = None) -> tuple:
        """اعتماد تقرير الوردية"""
        shift_report = ShiftReport.query.get(shift_report_id)
        if not shift_report:
            return False, "التقرير غير موجود"
        
        shift_report.status = ReportStatus.APPROVED
        shift_report.reviewed_by_user_id = reviewer_user_id
        shift_report.reviewed_at = datetime.utcnow()
        shift_report.review_notes = notes
        db.session.commit()
        
        # Notify handler
        NotificationService.create_notification(
            user_id=str(shift_report.handler_user_id),
            notification_type=NotificationType.REPORT_APPROVED,
            title="تم اعتماد تقرير الوردية",
            message=f"تم اعتماد تقرير الوردية بتاريخ {shift_report.date}",
            related_id=str(shift_report_id),
            related_type="ShiftReport"
        )
        
        return True, None
    
    @staticmethod
    def reject_shift_report(shift_report_id: str, reviewer_user_id: str, notes: str) -> tuple:
        """رفض تقرير الوردية"""
        shift_report = ShiftReport.query.get(shift_report_id)
        if not shift_report:
            return False, "التقرير غير موجود"
        
        shift_report.status = ReportStatus.REJECTED
        shift_report.reviewed_by_user_id = reviewer_user_id
        shift_report.reviewed_at = datetime.utcnow()
        shift_report.review_notes = notes
        db.session.commit()
        
        # Notify handler
        NotificationService.create_notification(
            user_id=str(shift_report.handler_user_id),
            notification_type=NotificationType.REPORT_REJECTED,
            title="تم رفض تقرير الوردية",
            message=f"تم رفض تقرير الوردية بتاريخ {shift_report.date}. السبب: {notes}",
            related_id=str(shift_report_id),
            related_type="ShiftReport"
        )
        
        return True, None
    
    @staticmethod
    def get_shift_reports_for_dog_date(dog_id: str, report_date: date):
        """الحصول على تقارير الوردية لكلب في يوم معين"""
        return ShiftReport.query.filter_by(
            dog_id=dog_id,
            date=report_date
        ).all()


class NotificationService:
    """خدمة إدارة الإشعارات"""
    
    @staticmethod
    def create_notification(user_id: str, notification_type: NotificationType,
                          title: str, message: str,
                          related_id: Optional[str] = None,
                          related_type: Optional[str] = None):
        """إنشاء إشعار جديد"""
        notification = Notification(  # type: ignore
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
    
    # Configuration
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    ALLOWED_MIMES = {
        'image/png', 'image/jpeg', 'image/gif',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    @staticmethod
    def validate_file(file) -> tuple:
        """التحقق من صحة الملف"""
        from werkzeug.utils import secure_filename
        
        if not file or not file.filename:
            return False, "لم يتم اختيار ملف"
        
        # Secure filename
        filename = secure_filename(file.filename)
        if not filename:
            return False, "اسم الملف غير صالح"
        
        # Check extension
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if file_ext not in AttachmentService.ALLOWED_EXTENSIONS:
            return False, f"نوع الملف .{file_ext} غير مسموح. الأنواع المسموحة: {', '.join(AttachmentService.ALLOWED_EXTENSIONS)}"
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > AttachmentService.MAX_FILE_SIZE:
            size_mb = AttachmentService.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"حجم الملف أكبر من {size_mb:.0f} ميجا"
        
        if file_size == 0:
            return False, "الملف فارغ"
        
        # MIME type validation (optional but recommended)
        try:
            import magic
            file_content = file.read(2048)  # Read first 2KB for MIME detection
            file.seek(0)  # Reset
            mime = magic.from_buffer(file_content, mime=True)
            if mime not in AttachmentService.ALLOWED_MIMES:
                return False, f"نوع المحتوى غير مسموح: {mime}"
        except (ImportError, Exception):
            # If python-magic is not available or errors, skip MIME check
            pass
        
        return True, None
    
    @staticmethod
    def save_report_attachment(file, report_id: str, description: Optional[str] = None) -> tuple:
        """حفظ مرفق تقرير مع SHA256 وجميع التحققات الأمنية"""
        import hashlib
        from werkzeug.utils import secure_filename
        import uuid
        
        # Validate file
        valid, error = AttachmentService.validate_file(file)
        if not valid:
            return None, error
        
        try:
            # Secure filename
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            # Generate unique filename with UUID
            unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
            
            # Create directory structure: uploads/handler_reports/YYYY/MM/
            now = datetime.now()
            relative_path = os.path.join('handler_reports', str(now.year), f"{now.month:02d}")
            upload_folder = 'uploads'
            full_dir = os.path.join(upload_folder, relative_path)
            os.makedirs(full_dir, exist_ok=True)
            
            file_path = os.path.join(full_dir, unique_filename)
            
            # Read file content and calculate SHA256
            file_content = file.read()
            sha256_hash = hashlib.sha256(file_content).hexdigest()
            
            # Check for duplicate hash (optional - prevent duplicate uploads)
            existing = HandlerReportAttachment.query.filter_by(sha256_hash=sha256_hash).first()
            if existing:
                # File already exists with same hash - could reuse or reject
                pass  # For now, allow duplicates
            
            # Save file atomically
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Determine file type
            if file_ext in {'png', 'jpg', 'jpeg', 'gif'}:
                file_type = 'image'
            elif file_ext == 'pdf':
                file_type = 'pdf'
            else:
                file_type = 'document'
            
            # Create attachment record
            attachment = HandlerReportAttachment(  # type: ignore
                report_id=report_id,
                filename=unique_filename,
                original_filename=filename,
                file_path=os.path.join(relative_path, unique_filename),
                file_type=file_type,
                file_size=len(file_content),
                sha256_hash=sha256_hash,
                description=description
            )
            
            db.session.add(attachment)
            # Don't commit here - let the caller commit transactionally
            
            return attachment, None
            
        except Exception as e:
            # Log the exception
            print(f"Error saving attachment: {str(e)}")
            return None, f"خطأ في حفظ الملف: {str(e)}"
    
    @staticmethod
    def save_attachment(file, incident_id: str, upload_folder: str) -> tuple:
        """حفظ مرفق مع SHA256 - legacy method for incidents"""
        import hashlib
        from werkzeug.utils import secure_filename
        import uuid
        
        # Validate file
        valid, error = AttachmentService.validate_file(file)
        if not valid:
            return None, error
        
        # Validate file type
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
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
        attachment = HandlerReportAttachment(  # type: ignore
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
