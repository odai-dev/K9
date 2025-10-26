"""
نماذج نظام التحضير اليومي والتقارير اليومية للسائس
Daily Schedule and Handler Daily Report Models
"""
from app import db
from datetime import datetime, date, time
from enum import Enum
from k9.models.models import get_uuid_column, default_uuid
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Text

# ============================================================================
# Enums
# ============================================================================

class ScheduleStatus(Enum):
    """حالة الجدول اليومي"""
    OPEN = "OPEN"          # مفتوح - يمكن التعديل
    LOCKED = "LOCKED"      # مقفل - لا يمكن التعديل

class ScheduleItemStatus(Enum):
    """حالة عنصر الجدول"""
    PLANNED = "PLANNED"        # مخطط
    PRESENT = "PRESENT"        # حاضر
    ABSENT = "ABSENT"          # غائب
    REPLACED = "REPLACED"      # تم الاستبدال

class ReportStatus(Enum):
    """حالة تقرير السائس"""
    DRAFT = "DRAFT"            # مسودة
    SUBMITTED = "SUBMITTED"    # مرسل
    APPROVED = "APPROVED"      # معتمد
    REJECTED = "REJECTED"      # مرفوض

class HealthCheckStatus(Enum):
    """حالة الفحص الصحي"""
    NORMAL = "سليم"
    ABNORMAL = "غير طبيعي"
    NEEDS_ATTENTION = "يحتاج متابعة"

class TrainingType(Enum):
    """نوع التدريب"""
    FITNESS = "لياقة"
    AGILITY = "خفة الحركة"
    OBEDIENCE = "طاعة"
    BALL = "كرة"
    EXPLOSIVES = "متفجرات"
    OTHER = "أخرى"

class BehaviorType(Enum):
    """نوع السلوك"""
    GOOD = "جيد"
    BAD = "سيئ"

class IncidentType(Enum):
    """نوع الحادث"""
    SUSPICION = "اشتباه"
    DETECTION = "كشف"

class StoolColor(Enum):
    """لون البراز"""
    BROWN = "بني"
    YELLOW = "أصفر"
    GREEN = "أخضر"
    BLACK = "أسود"
    RED = "أحمر"
    WHITE = "أبيض"

class StoolShape(Enum):
    """شكل البراز"""
    NORMAL = "طبيعي"
    HARD = "صلب"
    SOFT = "لين"
    LIQUID = "سائل"

class NotificationType(Enum):
    """نوع الإشعار"""
    SCHEDULE_CREATED = "SCHEDULE_CREATED"
    EMPLOYEE_REPLACED = "EMPLOYEE_REPLACED"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    REPORT_SUBMITTED = "REPORT_SUBMITTED"
    REPORT_APPROVED = "REPORT_APPROVED"
    REPORT_REJECTED = "REPORT_REJECTED"

# ============================================================================
# Daily Schedule Models
# ============================================================================

class DailySchedule(db.Model):
    """جدول التحضير اليومي"""
    __tablename__ = 'daily_schedule'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    date = db.Column(db.Date, nullable=False, index=True)
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=True)
    status = db.Column(db.Enum(ScheduleStatus), nullable=False, default=ScheduleStatus.OPEN)
    notes = db.Column(Text, nullable=True)
    
    # Audit fields
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    project = db.relationship('Project', backref='daily_schedules')
    created_by = db.relationship('User', backref='created_schedules')
    items = db.relationship('DailyScheduleItem', backref='schedule', cascade='all, delete-orphan', lazy='dynamic')
    
    __table_args__ = (
        db.UniqueConstraint('date', 'project_id', name='uq_daily_schedule_date_project'),
        db.Index('idx_daily_schedule_date', 'date'),
        db.Index('idx_daily_schedule_status', 'status'),
    )
    
    def __repr__(self):
        return f'<DailySchedule {self.date} - {self.status.value}>'


class DailyScheduleItem(db.Model):
    """عنصر في جدول التحضير اليومي"""
    __tablename__ = 'daily_schedule_item'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    daily_schedule_id = db.Column(get_uuid_column(), db.ForeignKey('daily_schedule.id', ondelete='CASCADE'), nullable=False)
    
    # Assignment - using handler users (not employees)
    handler_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=False)
    dog_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'), nullable=True)
    shift_id = db.Column(get_uuid_column(), db.ForeignKey('shift.id'), nullable=True)
    
    # Status
    status = db.Column(db.Enum(ScheduleItemStatus), nullable=False, default=ScheduleItemStatus.PLANNED)
    
    # Replacement info
    replacement_handler_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=True)
    absence_reason = db.Column(db.String(500), nullable=True)
    replacement_notes = db.Column(Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - using User (handlers) not Employee
    handler = db.relationship('User', foreign_keys=[handler_user_id], backref='schedule_items')
    replacement_handler = db.relationship('User', foreign_keys=[replacement_handler_id], backref='replacement_schedule_items')
    dog = db.relationship('Dog', backref='schedule_items')
    shift = db.relationship('Shift', backref='schedule_items')
    
    __table_args__ = (
        db.Index('idx_schedule_item_handler', 'handler_user_id'),
        db.Index('idx_schedule_item_status', 'status'),
    )
    
    def __repr__(self):
        return f'<DailyScheduleItem Handler:{self.handler_user_id} - {self.status.value}>'


# ============================================================================
# Handler Report Models
# ============================================================================

class HandlerReport(db.Model):
    """التقرير اليومي للسائس - الجدول الرئيسي"""
    __tablename__ = 'handler_report'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    
    # Report metadata
    date = db.Column(db.Date, nullable=False, index=True)
    schedule_item_id = db.Column(get_uuid_column(), db.ForeignKey('daily_schedule_item.id'), nullable=True)
    handler_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=False)
    dog_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'), nullable=False)
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=True)
    
    # General info
    location = db.Column(db.String(200), nullable=True)
    
    # Status and approval
    status = db.Column(db.Enum(ReportStatus), nullable=False, default=ReportStatus.DRAFT)
    submitted_at = db.Column(db.DateTime, nullable=True)
    reviewed_by_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_notes = db.Column(Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    schedule_item = db.relationship('DailyScheduleItem', backref='handler_reports')
    handler = db.relationship('User', foreign_keys=[handler_user_id], backref='submitted_reports')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by_user_id], backref='reviewed_reports')
    dog = db.relationship('Dog', backref='handler_reports')
    project = db.relationship('Project', backref='handler_reports')
    
    # Related report sections
    health = db.relationship('HandlerReportHealth', backref='report', uselist=False, cascade='all, delete-orphan')
    training_sessions = db.relationship('HandlerReportTraining', backref='report', cascade='all, delete-orphan')
    care = db.relationship('HandlerReportCare', backref='report', uselist=False, cascade='all, delete-orphan')
    behavior = db.relationship('HandlerReportBehavior', backref='report', uselist=False, cascade='all, delete-orphan')
    incidents = db.relationship('HandlerReportIncident', backref='report', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_handler_report_date', 'date'),
        db.Index('idx_handler_report_handler', 'handler_user_id'),
        db.Index('idx_handler_report_status', 'status'),
    )
    
    def __repr__(self):
        return f'<HandlerReport {self.date} - Handler:{self.handler_user_id}>'


class HandlerReportHealth(db.Model):
    """الفحص الصحي للكلب"""
    __tablename__ = 'handler_report_health'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    report_id = db.Column(get_uuid_column(), db.ForeignKey('handler_report.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Health check fields - كل حقل له حالة وملاحظات
    eyes_status = db.Column(db.Enum(HealthCheckStatus), nullable=True)
    eyes_notes = db.Column(db.String(500), nullable=True)
    
    nose_status = db.Column(db.Enum(HealthCheckStatus), nullable=True)
    nose_notes = db.Column(db.String(500), nullable=True)
    
    ears_status = db.Column(db.Enum(HealthCheckStatus), nullable=True)
    ears_notes = db.Column(db.String(500), nullable=True)
    
    mouth_status = db.Column(db.Enum(HealthCheckStatus), nullable=True)
    mouth_notes = db.Column(db.String(500), nullable=True)
    
    teeth_status = db.Column(db.Enum(HealthCheckStatus), nullable=True)
    teeth_notes = db.Column(db.String(500), nullable=True)
    
    gums_status = db.Column(db.Enum(HealthCheckStatus), nullable=True)
    gums_notes = db.Column(db.String(500), nullable=True)
    
    front_limbs_status = db.Column(db.Enum(HealthCheckStatus), nullable=True)
    front_limbs_notes = db.Column(db.String(500), nullable=True)
    
    back_limbs_status = db.Column(db.Enum(HealthCheckStatus), nullable=True)
    back_limbs_notes = db.Column(db.String(500), nullable=True)
    
    hair_status = db.Column(db.Enum(HealthCheckStatus), nullable=True)
    hair_notes = db.Column(db.String(500), nullable=True)
    
    tail_status = db.Column(db.Enum(HealthCheckStatus), nullable=True)
    tail_notes = db.Column(db.String(500), nullable=True)
    
    rear_status = db.Column(db.Enum(HealthCheckStatus), nullable=True)
    rear_notes = db.Column(db.String(500), nullable=True)
    
    def __repr__(self):
        return f'<HandlerReportHealth Report:{self.report_id}>'


class HandlerReportTraining(db.Model):
    """تفاصيل التدريب"""
    __tablename__ = 'handler_report_training'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    report_id = db.Column(get_uuid_column(), db.ForeignKey('handler_report.id', ondelete='CASCADE'), nullable=False)
    
    training_type = db.Column(db.Enum(TrainingType), nullable=False)
    description = db.Column(Text, nullable=True)
    time_from = db.Column(db.Time, nullable=True)
    time_to = db.Column(db.Time, nullable=True)
    notes = db.Column(Text, nullable=True)
    
    def __repr__(self):
        return f'<HandlerReportTraining {self.training_type.value}>'


class HandlerReportCare(db.Model):
    """العناية بالكلب"""
    __tablename__ = 'handler_report_care'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    report_id = db.Column(get_uuid_column(), db.ForeignKey('handler_report.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Food
    food_amount = db.Column(db.String(100), nullable=True)  # كمية الطعام
    food_type = db.Column(db.String(200), nullable=True)     # نوع الطعام
    supplements = db.Column(db.String(200), nullable=True)   # المكملات الغذائية
    water_amount = db.Column(db.String(100), nullable=True)  # كمية الماء
    
    # Grooming
    grooming_done = db.Column(db.Boolean, default=False)     # تمشيط
    washing_done = db.Column(db.Boolean, default=False)      # غسل
    
    # Excretion
    excretion_location = db.Column(db.String(200), nullable=True)  # مكان التبرز
    stool_color = db.Column(db.Enum(StoolColor), nullable=True)    # لون البراز
    stool_shape = db.Column(db.Enum(StoolShape), nullable=True)    # شكل البراز
    
    def __repr__(self):
        return f'<HandlerReportCare Report:{self.report_id}>'


class HandlerReportBehavior(db.Model):
    """سلوك الكلب"""
    __tablename__ = 'handler_report_behavior'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    report_id = db.Column(get_uuid_column(), db.ForeignKey('handler_report.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    good_behavior_notes = db.Column(Text, nullable=True)  # السلوك الجيد
    bad_behavior_notes = db.Column(Text, nullable=True)   # السلوك السيئ
    
    def __repr__(self):
        return f'<HandlerReportBehavior Report:{self.report_id}>'


class HandlerReportIncident(db.Model):
    """حالات الاشتباه والكشف"""
    __tablename__ = 'handler_report_incident'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    report_id = db.Column(get_uuid_column(), db.ForeignKey('handler_report.id', ondelete='CASCADE'), nullable=False)
    
    incident_type = db.Column(db.Enum(IncidentType), nullable=False)
    description = db.Column(Text, nullable=False)
    incident_datetime = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    
    # Attachments stored as JSON array of file paths
    attachments = db.relationship('HandlerReportAttachment', backref='incident', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<HandlerReportIncident {self.incident_type.value}>'


class HandlerReportAttachment(db.Model):
    """مرفقات التقرير"""
    __tablename__ = 'handler_report_attachment'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    incident_id = db.Column(get_uuid_column(), db.ForeignKey('handler_report_incident.id', ondelete='CASCADE'), nullable=False)
    
    filename = db.Column(db.String(255), nullable=False)      # اسم الملف الآمن
    original_filename = db.Column(db.String(255), nullable=False)  # الاسم الأصلي
    file_path = db.Column(db.String(500), nullable=False)     # المسار
    file_type = db.Column(db.String(50), nullable=False)      # نوع الملف (image, pdf)
    file_size = db.Column(db.Integer, nullable=False)         # حجم الملف بالبايت
    sha256_hash = db.Column(db.String(64), nullable=False)    # SHA256 للتحقق من السلامة
    
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<HandlerReportAttachment {self.filename}>'


# ============================================================================
# Notification Model
# ============================================================================

class Notification(db.Model):
    """الإشعارات"""
    __tablename__ = 'notification'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    
    type = db.Column(db.Enum(NotificationType), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(Text, nullable=False)
    
    # Related object (optional)
    related_id = db.Column(db.String(36), nullable=True)   # UUID as string for flexibility
    related_type = db.Column(db.String(50), nullable=True) # Type of related object
    
    # Status
    read = db.Column(db.Boolean, default=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    
    __table_args__ = (
        db.Index('idx_notification_user_read', 'user_id', 'read'),
        db.Index('idx_notification_created', 'created_at'),
    )
    
    def __repr__(self):
        return f'<Notification {self.type.value} - User:{self.user_id}>'
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.read:
            self.read = True
            self.read_at = datetime.utcnow()
            db.session.commit()


# ============================================================================
# Task Assignment Model
# ============================================================================

class TaskStatus(Enum):
    """حالة المهمة"""
    PENDING = "PENDING"        # قيد الانتظار
    IN_PROGRESS = "IN_PROGRESS"  # قيد التنفيذ
    COMPLETED = "COMPLETED"    # مكتملة
    CANCELLED = "CANCELLED"    # ملغاة


class TaskPriority(Enum):
    """أولوية المهمة"""
    LOW = "منخفضة"
    MEDIUM = "متوسطة"
    HIGH = "عالية"
    URGENT = "عاجلة"


class Task(db.Model):
    """المهام والتكليفات"""
    __tablename__ = 'task'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    
    # Task details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(Text, nullable=True)
    priority = db.Column(db.Enum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM)
    status = db.Column(db.Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    
    # Assignment
    assigned_to_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=False)
    created_by_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=False)
    
    # Optional project association
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=True)
    
    # Timing
    due_date = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_user_id], backref='assigned_tasks')
    created_by = db.relationship('User', foreign_keys=[created_by_user_id], backref='created_tasks')
    project = db.relationship('Project', backref='tasks')
    
    __table_args__ = (
        db.Index('idx_task_assigned_to', 'assigned_to_user_id'),
        db.Index('idx_task_status', 'status'),
        db.Index('idx_task_due_date', 'due_date'),
    )
    
    def __repr__(self):
        return f'<Task {self.title} - {self.status.value}>'
