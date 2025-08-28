from app import db
from datetime import datetime, date, timedelta
from enum import Enum
import uuid
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import String, Text, Boolean, DateTime, Date, Time, Integer, Enum as SQLEnum
import os

# Use String for UUID when using SQLite, UUID when using PostgreSQL
def get_uuid_column():
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url.startswith("sqlite") or not database_url:
        return String(36)
    else:
        from sqlalchemy.dialects.postgresql import UUID
        return UUID(as_uuid=True)

def default_uuid():
    return str(uuid.uuid4())

class NotificationType(Enum):
    ATTENDANCE_LATE = "ATTENDANCE_LATE"           # تأخر في الحضور
    ATTENDANCE_ABSENT = "ATTENDANCE_ABSENT"       # غياب
    VACCINATION_DUE = "VACCINATION_DUE"           # موعد تطعيم قريب
    PROJECT_ENDING = "PROJECT_ENDING"             # انتهاء مشروع قريب
    HEAT_CYCLE_START = "HEAT_CYCLE_START"         # بداية دورة حرارة
    HEAT_CYCLE_END = "HEAT_CYCLE_END"             # انتهاء دورة حرارة
    TRAINING_OVERDUE = "TRAINING_OVERDUE"         # تدريب متأخر
    VET_CHECKUP_DUE = "VET_CHECKUP_DUE"          # فحص طبي مطلوب
    PROJECT_MILESTONE = "PROJECT_MILESTONE"       # معلم مشروع مهم
    EMERGENCY_ALERT = "EMERGENCY_ALERT"           # تنبيه طارئ
    SYSTEM_MAINTENANCE = "SYSTEM_MAINTENANCE"     # صيانة نظام

class NotificationPriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class NotificationStatus(Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    FAILED = "FAILED"

class NotificationChannel(Enum):
    BROWSER = "BROWSER"      # إشعارات المتصفح
    PUSH = "PUSH"           # Push notifications
    EMAIL = "EMAIL"         # البريد الإلكتروني
    SMS = "SMS"             # رسائل نصية
    IN_APP = "IN_APP"       # داخل التطبيق

class Notification(db.Model):
    """نموذج الإشعارات الأساسي"""
    __tablename__ = 'notifications'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    
    # معلومات الإشعار الأساسية
    type = db.Column(SQLEnum(NotificationType), nullable=False)
    title = db.Column(String(200), nullable=False)
    message = db.Column(Text, nullable=False)
    priority = db.Column(SQLEnum(NotificationPriority), nullable=False, default=NotificationPriority.MEDIUM)
    
    # المستقبل
    user_id = db.Column(Integer, db.ForeignKey('user.id'), nullable=False)
    role_filter = db.Column(String(50), nullable=True)  # لإرسال لدور معين
    
    # الكائن المرتبط
    related_type = db.Column(String(50), nullable=True)  # Dog, Employee, Project, etc.
    related_id = db.Column(get_uuid_column(), nullable=True)
    
    # التوقيت
    scheduled_for = db.Column(DateTime, nullable=True)  # موعد الإرسال المجدول
    expires_at = db.Column(DateTime, nullable=True)     # تاريخ انتهاء الصلاحية
    
    # الحالة
    status = db.Column(SQLEnum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING)
    read_at = db.Column(DateTime, nullable=True)
    
    # قنوات الإرسال
    channels = db.Column(JSON, nullable=False, default=list)  # قائمة القنوات المطلوبة
    
    # بيانات إضافية  
    extra_data = db.Column(JSON, nullable=True)  # بيانات مساعدة
    action_url = db.Column(String(500), nullable=True)  # رابط للإجراء
    
    # تواريخ النظام
    created_at = db.Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = db.Column(DateTime, nullable=True)
    
    # العلاقات
    user = db.relationship('User', backref='notifications')
    delivery_attempts = db.relationship('NotificationDelivery', backref='notification', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Notification {self.title} to {self.user_id}>'

class NotificationDelivery(db.Model):
    """محاولات إرسال الإشعارات"""
    __tablename__ = 'notification_deliveries'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    notification_id = db.Column(get_uuid_column(), db.ForeignKey('notifications.id'), nullable=False)
    
    channel = db.Column(SQLEnum(NotificationChannel), nullable=False)
    status = db.Column(SQLEnum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING)
    
    # تفاصيل الإرسال
    attempted_at = db.Column(DateTime, nullable=True)
    delivered_at = db.Column(DateTime, nullable=True)
    error_message = db.Column(Text, nullable=True)
    
    # بيانات إضافية خاصة بالقناة
    channel_data = db.Column(JSON, nullable=True)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)

class NotificationSettings(db.Model):
    """إعدادات الإشعارات للمستخدمين"""
    __tablename__ = 'notification_settings'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    user_id = db.Column(Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # إعدادات عامة
    enabled = db.Column(Boolean, default=True)
    quiet_hours_start = db.Column(Time, nullable=True)  # بداية الساعات الهادئة
    quiet_hours_end = db.Column(Time, nullable=True)    # نهاية الساعات الهادئة
    
    # إعدادات أنواع الإشعارات
    attendance_alerts = db.Column(Boolean, default=True)
    vaccination_reminders = db.Column(Boolean, default=True)
    project_updates = db.Column(Boolean, default=True)
    heat_cycle_alerts = db.Column(Boolean, default=True)
    training_reminders = db.Column(Boolean, default=True)
    vet_checkup_reminders = db.Column(Boolean, default=True)
    emergency_alerts = db.Column(Boolean, default=True)
    system_updates = db.Column(Boolean, default=False)
    
    # إعدادات القنوات
    browser_notifications = db.Column(Boolean, default=True)
    push_notifications = db.Column(Boolean, default=True)
    email_notifications = db.Column(Boolean, default=False)
    sms_notifications = db.Column(Boolean, default=False)
    
    # بيانات Push Notifications
    push_subscription = db.Column(JSON, nullable=True)  # بيانات اشتراك المتصفح
    
    # تواريخ النظام
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    user = db.relationship('User', backref='notification_settings', uselist=False)
    
    def __repr__(self):
        return f'<NotificationSettings for {self.user_id}>'

class NotificationTemplate(db.Model):
    """قوالب الإشعارات"""
    __tablename__ = 'notification_templates'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    
    type = db.Column(SQLEnum(NotificationType), nullable=False, unique=True)
    title_template = db.Column(String(200), nullable=False)
    message_template = db.Column(Text, nullable=False)
    priority = db.Column(SQLEnum(NotificationPriority), nullable=False, default=NotificationPriority.MEDIUM)
    
    # إعدادات التوقيت
    advance_hours = db.Column(Integer, default=24)  # كم ساعة قبل الحدث
    reminder_intervals = db.Column(JSON, nullable=True)  # فترات التذكير المتعددة
    
    # إعدادات القنوات الافتراضية
    default_channels = db.Column(JSON, nullable=False, default=list)
    
    # شروط الإرسال
    conditions = db.Column(JSON, nullable=True)  # شروط إضافية للإرسال
    
    # إعدادات النظام
    is_active = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<NotificationTemplate {self.type.value}>'

class NotificationRule(db.Model):
    """قواعد إنشاء الإشعارات التلقائية"""
    __tablename__ = 'notification_rules'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    
    name = db.Column(String(100), nullable=False)
    description = db.Column(Text, nullable=True)
    
    # نوع الحدث المراقب
    event_type = db.Column(String(50), nullable=False)  # attendance, vaccination, project, etc.
    trigger_condition = db.Column(JSON, nullable=False)  # شروط التشغيل
    
    # الإشعار المطلوب إرساله
    notification_type = db.Column(SQLEnum(NotificationType), nullable=False)
    notification_template_id = db.Column(get_uuid_column(), db.ForeignKey('notification_templates.id'), nullable=True)
    
    # المستقبلون
    target_roles = db.Column(JSON, nullable=True)  # الأدوار المستهدفة
    target_users = db.Column(JSON, nullable=True)  # مستخدمون محددون
    
    # إعدادات التشغيل
    is_active = db.Column(Boolean, default=True)
    run_frequency = db.Column(String(20), default='daily')  # daily, hourly, realtime
    last_run = db.Column(DateTime, nullable=True)
    next_run = db.Column(DateTime, nullable=True)
    
    # تواريخ النظام
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    template = db.relationship('NotificationTemplate', backref='rules')
    
    def __repr__(self):
        return f'<NotificationRule {self.name}>'