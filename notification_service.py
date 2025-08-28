from flask import current_app, render_template_string
from flask_socketio import emit, join_room, leave_room
from models_notifications import (
    Notification, NotificationDelivery, NotificationSettings, 
    NotificationTemplate, NotificationRule, NotificationType, 
    NotificationPriority, NotificationStatus, NotificationChannel
)
from models import User, Employee, Dog, Project, VeterinaryVisit, HeatCycle, AttendanceDay, ProjectAttendance
from app import db
from datetime import datetime, date, timedelta
import json
import logging
from typing import List, Dict, Optional, Any
from pywebpush import webpush, WebPushException
import os

logger = logging.getLogger(__name__)

class NotificationService:
    """خدمة إدارة الإشعارات الفورية"""
    
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.vapid_private_key = os.environ.get('VAPID_PRIVATE_KEY', '')
        self.vapid_public_key = os.environ.get('VAPID_PUBLIC_KEY', '')
        self.vapid_claims = {
            "sub": "mailto:admin@k9ops.com"
        }
    
    def create_notification(self, 
                          notification_type: NotificationType,
                          user_id: int,
                          title: str,
                          message: str,
                          priority: NotificationPriority = NotificationPriority.MEDIUM,
                          related_type: Optional[str] = None,
                          related_id: Optional[str] = None,
                          action_url: Optional[str] = None,
                          metadata: Optional[Dict] = None,
                          channels: Optional[List[str]] = None,
                          scheduled_for: Optional[datetime] = None) -> Optional[Notification]:
        """إنشاء إشعار جديد"""
        try:
            # التحقق من إعدادات المستخدم
            settings = self.get_user_settings(user_id)
            if not settings.enabled:
                logger.info(f"Notifications disabled for user {user_id}")
                return None
            
            # التحقق من نوع الإشعار
            if not self._is_notification_type_enabled(settings, notification_type):
                logger.info(f"Notification type {notification_type.value} disabled for user {user_id}")
                return None
            
            # تحديد القنوات الافتراضية
            if channels is None:
                channels = self._get_default_channels(settings)
            
            # إنشاء الإشعار
            notification = Notification()
            notification.type = notification_type
            notification.title = title
            notification.message = message
            notification.priority = priority
            notification.user_id = user_id
            notification.related_type = related_type
            notification.related_id = related_id
            notification.action_url = action_url
            notification.extra_data = metadata or {}
            notification.channels = channels
            notification.scheduled_for = scheduled_for or datetime.utcnow()
            
            db.session.add(notification)
            db.session.commit()
            
            # إرسال فوري إذا لم يكن مجدول
            if scheduled_for is None or scheduled_for <= datetime.utcnow():
                self._send_notification(notification)
            
            logger.info(f"Created notification {notification.id} for user {user_id}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            db.session.rollback()
            return None
    
    def send_to_role(self, 
                     notification_type: NotificationType,
                     role: str,
                     title: str,
                     message: str,
                     priority: NotificationPriority = NotificationPriority.MEDIUM,
                     **kwargs) -> List[Notification]:
        """إرسال إشعار لجميع المستخدمين بدور معين"""
        try:
            # الحصول على المستخدمين بالدور المطلوب
            users = User.query.filter_by(role=role, active=True).all()
            notifications = []
            
            for user in users:
                notification = self.create_notification(
                    notification_type=notification_type,
                    user_id=user.id,
                    title=title,
                    message=message,
                    priority=priority,
                    **kwargs
                )
                if notification:
                    notifications.append(notification)
            
            logger.info(f"Sent notification to {len(notifications)} users with role {role}")
            return notifications
            
        except Exception as e:
            logger.error(f"Error sending notification to role {role}: {e}")
            return []
    
    def _send_notification(self, notification: Notification):
        """إرسال الإشعار عبر القنوات المحددة"""
        try:
            settings = self.get_user_settings(notification.user_id)
            
            # التحقق من الساعات الهادئة
            if self._is_quiet_hours(settings):
                logger.info(f"Delaying notification {notification.id} - quiet hours")
                # تأجيل الإرسال لنهاية الساعات الهادئة
                next_send_time = self._get_next_active_time(settings)
                notification.scheduled_for = next_send_time
                db.session.commit()
                return
            
            # إرسال عبر كل قناة
            for channel_name in notification.channels:
                delivery = None
                try:
                    channel = NotificationChannel(channel_name)
                    delivery = self._create_delivery_record(notification, channel)
                    
                    if channel == NotificationChannel.BROWSER:
                        self._send_browser_notification(notification, delivery)
                    elif channel == NotificationChannel.PUSH:
                        self._send_push_notification(notification, delivery, settings)
                    elif channel == NotificationChannel.IN_APP:
                        self._send_in_app_notification(notification, delivery)
                    elif channel == NotificationChannel.EMAIL:
                        self._send_email_notification(notification, delivery)
                    
                except ValueError:
                    logger.warning(f"Unknown notification channel: {channel_name}")
                except Exception as e:
                    logger.error(f"Error sending via {channel_name}: {e}")
                    if delivery:
                        delivery.status = NotificationStatus.FAILED
                        delivery.error_message = str(e)
            
            # تحديث حالة الإشعار
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error sending notification {notification.id}: {e}")
            notification.status = NotificationStatus.FAILED
            db.session.commit()
    
    def _send_browser_notification(self, notification: Notification, delivery: NotificationDelivery):
        """إرسال إشعار عبر المتصفح (WebSocket)"""
        try:
            if not self.socketio:
                delivery.status = NotificationStatus.FAILED
                delivery.error_message = "WebSocket not available"
                return
            
            user_room = f"user_{notification.user_id}"
            
            notification_data = {
                'id': notification.id,
                'type': notification.type.value,
                'title': notification.title,
                'message': notification.message,
                'priority': notification.priority.value,
                'action_url': notification.action_url,
                'metadata': notification.extra_data,
                'created_at': notification.created_at.isoformat()
            }
            
            # إرسال عبر WebSocket
            self.socketio.emit('notification', notification_data, room=user_room)
            
            # تحديث حالة الإرسال
            delivery.status = NotificationStatus.SENT
            delivery.attempted_at = datetime.utcnow()
            delivery.delivered_at = datetime.utcnow()
            
            logger.info(f"Sent browser notification {notification.id} to user {notification.user_id}")
            
        except Exception as e:
            logger.error(f"Error sending browser notification: {e}")
            delivery.status = NotificationStatus.FAILED
            delivery.error_message = str(e)
    
    def _send_push_notification(self, notification: Notification, delivery: NotificationDelivery, settings: NotificationSettings):
        """إرسال Push Notification"""
        try:
            if not settings.push_subscription or not self.vapid_private_key:
                delivery.status = NotificationStatus.FAILED
                delivery.error_message = "Push subscription or VAPID keys not available"
                return
            
            payload = {
                'title': notification.title,
                'body': notification.message,
                'icon': '/static/img/logo.png',
                'badge': '/static/img/logo.png',
                'data': {
                    'id': notification.id,
                    'type': notification.type.value,
                    'action_url': notification.action_url,
                    'metadata': notification.extra_data
                },
                'actions': []
            }
            
            # إضافة إجراءات حسب النوع
            if notification.action_url:
                payload['actions'].append({
                    'action': 'open',
                    'title': 'عرض التفاصيل'
                })
            
            payload['actions'].append({
                'action': 'dismiss',
                'title': 'إغلاق'
            })
            
            # إرسال Push Notification
            webpush(
                subscription_info=settings.push_subscription,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims
            )
            
            delivery.status = NotificationStatus.SENT
            delivery.attempted_at = datetime.utcnow()
            delivery.delivered_at = datetime.utcnow()
            
            logger.info(f"Sent push notification {notification.id} to user {notification.user_id}")
            
        except WebPushException as e:
            logger.error(f"WebPush error: {e}")
            delivery.status = NotificationStatus.FAILED
            delivery.error_message = str(e)
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            delivery.status = NotificationStatus.FAILED
            delivery.error_message = str(e)
    
    def _send_in_app_notification(self, notification: Notification, delivery: NotificationDelivery):
        """إرسال إشعار داخل التطبيق"""
        try:
            # الإشعارات داخل التطبيق تُحفظ في قاعدة البيانات فقط
            # ويتم عرضها عند تحميل الصفحة
            delivery.status = NotificationStatus.DELIVERED
            delivery.attempted_at = datetime.utcnow()
            delivery.delivered_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error with in-app notification: {e}")
            delivery.status = NotificationStatus.FAILED
            delivery.error_message = str(e)
    
    def _send_email_notification(self, notification: Notification, delivery: NotificationDelivery):
        """إرسال إشعار عبر البريد الإلكتروني"""
        try:
            # TODO: تنفيذ إرسال البريد الإلكتروني
            delivery.status = NotificationStatus.FAILED
            delivery.error_message = "Email sending not implemented yet"
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            delivery.status = NotificationStatus.FAILED
            delivery.error_message = str(e)
    
    def _create_delivery_record(self, notification: Notification, channel: NotificationChannel) -> NotificationDelivery:
        """إنشاء سجل محاولة إرسال"""
        delivery = NotificationDelivery()
        delivery.notification_id = notification.id
        delivery.channel = channel
        delivery.status = NotificationStatus.PENDING
        db.session.add(delivery)
        db.session.flush()  # للحصول على ID
        return delivery
    
    def get_user_settings(self, user_id: int) -> NotificationSettings:
        """الحصول على إعدادات المستخدم أو إنشاء إعدادات افتراضية"""
        settings = NotificationSettings.query.filter_by(user_id=user_id).first()
        if not settings:
            settings = NotificationSettings()
            settings.user_id = user_id
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def update_user_settings(self, user_id: int, **kwargs) -> NotificationSettings:
        """تحديث إعدادات المستخدم"""
        settings = self.get_user_settings(user_id)
        
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        settings.updated_at = datetime.utcnow()
        db.session.commit()
        return settings
    
    def mark_as_read(self, notification_id: str, user_id: int) -> bool:
        """تحديد الإشعار كمقروء"""
        try:
            notification = Notification.query.filter_by(
                id=notification_id, 
                user_id=user_id
            ).first()
            
            if notification:
                notification.status = NotificationStatus.READ
                notification.read_at = datetime.utcnow()
                db.session.commit()
                
                # إرسال تحديث عبر WebSocket
                if self.socketio:
                    user_room = f"user_{user_id}"
                    self.socketio.emit('notification_read', {
                        'id': notification_id
                    }, room=user_room)
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    def get_user_notifications(self, user_id: int, limit: int = 50, unread_only: bool = False) -> List[Dict]:
        """الحصول على إشعارات المستخدم"""
        try:
            query = Notification.query.filter_by(user_id=user_id)
            
            if unread_only:
                query = query.filter(Notification.status != NotificationStatus.READ)
            
            notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
            
            return [{
                'id': n.id,
                'type': n.type.value,
                'title': n.title,
                'message': n.message,
                'priority': n.priority.value,
                'status': n.status.value,
                'action_url': n.action_url,
                'metadata': n.extra_data,
                'created_at': n.created_at.isoformat(),
                'read_at': n.read_at.isoformat() if n.read_at else None
            } for n in notifications]
            
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []
    
    def _is_notification_type_enabled(self, settings: NotificationSettings, notification_type: NotificationType) -> bool:
        """التحقق من تفعيل نوع الإشعار"""
        type_mapping = {
            NotificationType.ATTENDANCE_LATE: settings.attendance_alerts,
            NotificationType.ATTENDANCE_ABSENT: settings.attendance_alerts,
            NotificationType.VACCINATION_DUE: settings.vaccination_reminders,
            NotificationType.PROJECT_ENDING: settings.project_updates,
            NotificationType.HEAT_CYCLE_START: settings.heat_cycle_alerts,
            NotificationType.HEAT_CYCLE_END: settings.heat_cycle_alerts,
            NotificationType.TRAINING_OVERDUE: settings.training_reminders,
            NotificationType.VET_CHECKUP_DUE: settings.vet_checkup_reminders,
            NotificationType.EMERGENCY_ALERT: settings.emergency_alerts,
            NotificationType.SYSTEM_MAINTENANCE: settings.system_updates,
        }
        return type_mapping.get(notification_type, True)
    
    def _get_default_channels(self, settings: NotificationSettings) -> List[str]:
        """الحصول على القنوات الافتراضية للمستخدم"""
        channels = []
        
        if settings.browser_notifications:
            channels.append(NotificationChannel.BROWSER.value)
        if settings.push_notifications:
            channels.append(NotificationChannel.PUSH.value)
        if settings.email_notifications:
            channels.append(NotificationChannel.EMAIL.value)
        
        # إضافة الإشعارات داخل التطبيق دائماً
        channels.append(NotificationChannel.IN_APP.value)
        
        return channels
    
    def _is_quiet_hours(self, settings: NotificationSettings) -> bool:
        """التحقق من الساعات الهادئة"""
        if not settings.quiet_hours_start or not settings.quiet_hours_end:
            return False
        
        now = datetime.now().time()
        start = settings.quiet_hours_start
        end = settings.quiet_hours_end
        
        if start <= end:
            return start <= now <= end
        else:  # عبر منتصف الليل
            return now >= start or now <= end
    
    def _get_next_active_time(self, settings: NotificationSettings) -> datetime:
        """الحصول على التوقيت التالي خارج الساعات الهادئة"""
        if not settings.quiet_hours_end:
            return datetime.utcnow() + timedelta(hours=1)
        
        today = date.today()
        end_time = datetime.combine(today, settings.quiet_hours_end)
        
        # إذا كان وقت النهاية اليوم، أضف يوم
        if end_time <= datetime.now():
            end_time += timedelta(days=1)
        
        return end_time

# خدمة مراقبة الأحداث والإشعارات التلقائية
class NotificationMonitor:
    """مراقب الأحداث لإنشاء الإشعارات التلقائية"""
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
    
    def check_attendance_alerts(self):
        """فحص تنبيهات الحضور"""
        try:
            today = date.today()
            now = datetime.now()
            
            # فحص المتأخرين (بعد 30 دقيقة من بداية الدوام)
            late_threshold = now - timedelta(minutes=30)
            
            # الحصول على السجلات المتأخرة اليوم
            late_records = ProjectAttendance.query.filter(
                ProjectAttendance.date == today,
                ProjectAttendance.status.in_(['LATE', 'ABSENT']),
                ProjectAttendance.created_at <= late_threshold
            ).all()
            
            for record in late_records:
                # إرسال تنبيه للمديرين
                if record.status.value == 'LATE':
                    self._send_attendance_alert(
                        record, 
                        NotificationType.ATTENDANCE_LATE,
                        f"تأخر في الحضور",
                        f"تأخر {record.get_entity_name()} عن الحضور في المشروع"
                    )
                else:
                    self._send_attendance_alert(
                        record, 
                        NotificationType.ATTENDANCE_ABSENT,
                        f"غياب",
                        f"غياب {record.get_entity_name()} عن العمل في المشروع"
                    )
                    
        except Exception as e:
            logger.error(f"Error checking attendance alerts: {e}")
    
    def check_vaccination_reminders(self):
        """فحص تذكيرات التطعيمات"""
        try:
            # البحث عن الكلاب التي تحتاج تطعيم خلال الأسبوع القادم
            week_ahead = date.today() + timedelta(days=7)
            
            # TODO: تنفيذ منطق التحقق من التطعيمات القادمة
            # يحتاج إلى جدول منفصل لجدولة التطعيمات
            
        except Exception as e:
            logger.error(f"Error checking vaccination reminders: {e}")
    
    def check_project_deadlines(self):
        """فحص مواعيد انتهاء المشاريع"""
        try:
            week_ahead = date.today() + timedelta(days=7)
            
            # المشاريع التي تنتهي خلال أسبوع
            ending_projects = Project.query.filter(
                Project.end_date <= week_ahead,
                Project.end_date >= date.today(),
                Project.status.in_(['ACTIVE', 'PLANNED'])
            ).all()
            
            for project in ending_projects:
                days_left = (project.end_date - date.today()).days
                
                # إرسال تنبيه للمديرين والمعنيين
                self.notification_service.send_to_role(
                    notification_type=NotificationType.PROJECT_ENDING,
                    role='GENERAL_ADMIN',
                    title=f"اقتراب انتهاء المشروع",
                    message=f"سينتهي المشروع '{project.name}' خلال {days_left} أيام",
                    priority=NotificationPriority.HIGH,
                    related_type='Project',
                    related_id=project.id,
                    action_url=f"/projects/view/{project.id}"
                )
                
        except Exception as e:
            logger.error(f"Error checking project deadlines: {e}")
    
    def check_heat_cycles(self):
        """فحص دورات الحرارة للإناث"""
        try:
            today = date.today()
            
            # البحث عن دورات حرارة جديدة أو قريبة من الانتهاء
            active_cycles = HeatCycle.query.filter(
                HeatCycle.status == 'ACTIVE',
                HeatCycle.start_date <= today
            ).all()
            
            for cycle in active_cycles:
                # التحقق من بداية الدورة (إشعار في نفس اليوم)
                if cycle.start_date == today:
                    dog = Dog.query.get(cycle.dog_id)
                    if dog:
                        self.notification_service.send_to_role(
                            notification_type=NotificationType.HEAT_CYCLE_START,
                            role='BREEDER',
                            title=f"بداية دورة حرارة",
                            message=f"بدأت دورة حرارة للكلبة {dog.name}",
                            priority=NotificationPriority.MEDIUM,
                            related_type='Dog',
                            related_id=dog.id,
                            action_url=f"/dogs/view/{dog.id}"
                        )
                
                # التحقق من اقتراب انتهاء الدورة
                if cycle.end_date and cycle.end_date <= today + timedelta(days=2):
                    dog = Dog.query.get(cycle.dog_id)
                    if dog:
                        self.notification_service.send_to_role(
                            notification_type=NotificationType.HEAT_CYCLE_END,
                            role='BREEDER',
                            title=f"اقتراب انتهاء دورة الحرارة",
                            message=f"ستنتهي دورة حرارة الكلبة {dog.name} قريباً",
                            priority=NotificationPriority.LOW,
                            related_type='Dog',
                            related_id=dog.id
                        )
                        
        except Exception as e:
            logger.error(f"Error checking heat cycles: {e}")
    
    def _send_attendance_alert(self, record, notification_type, title, message):
        """إرسال تنبيه حضور للمديرين"""
        try:
            # إرسال للمدير العام
            self.notification_service.send_to_role(
                notification_type=notification_type,
                role='GENERAL_ADMIN',
                title=title,
                message=message,
                priority=NotificationPriority.HIGH,
                related_type='ProjectAttendance',
                related_id=record.id,
                action_url=f"/projects/attendance/{record.project_id}"
            )
            
            # إرسال لمدير المشروع إذا كان مختلف
            project = Project.query.get(record.project_id)
            if project and project.manager_id:
                manager_user = User.query.join(Employee).filter(
                    Employee.user_account_id == User.id,
                    Employee.id == project.manager_id
                ).first()
                
                if manager_user:
                    self.notification_service.create_notification(
                        notification_type=notification_type,
                        user_id=manager_user.id,
                        title=title,
                        message=message,
                        priority=NotificationPriority.HIGH,
                        related_type='ProjectAttendance',
                        related_id=record.id,
                        action_url=f"/projects/attendance/{record.project_id}"
                    )
                    
        except Exception as e:
            logger.error(f"Error sending attendance alert: {e}")