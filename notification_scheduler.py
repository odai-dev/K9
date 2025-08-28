import schedule
import time
import threading
from datetime import datetime, date, timedelta
from notification_service import NotificationService, NotificationMonitor
from models_notifications import NotificationRule, NotificationTemplate, NotificationStatus, NotificationPriority
from models import User, Project, Employee, Dog, VeterinaryVisit, HeatCycle
from app import db, app
import logging

logger = logging.getLogger(__name__)

class NotificationScheduler:
    """جدولة الإشعارات التلقائية"""
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        self.monitor = NotificationMonitor(notification_service)
        self.running = False
        self.thread = None
        
    def start(self):
        """بدء جدولة الإشعارات"""
        if self.running:
            logger.warning("Notification scheduler already running")
            return
        
        self.running = True
        
        # جدولة المهام
        self._schedule_tasks()
        
        # بدء الخيط المنفصل
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        logger.info("Notification scheduler started")
    
    def stop(self):
        """إيقاف جدولة الإشعارات"""
        self.running = False
        schedule.clear()
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("Notification scheduler stopped")
    
    def _schedule_tasks(self):
        """جدولة المهام المختلفة"""
        
        # فحص الحضور كل 15 دقيقة خلال ساعات العمل
        schedule.every(15).minutes.do(self._safe_run, self.monitor.check_attendance_alerts)
        
        # فحص مواعيد انتهاء المشاريع يومياً في الساعة 9 صباحاً
        schedule.every().day.at("09:00").do(self._safe_run, self.monitor.check_project_deadlines)
        
        # فحص دورات الحرارة يومياً في الساعة 8 صباحاً
        schedule.every().day.at("08:00").do(self._safe_run, self.monitor.check_heat_cycles)
        
        # فحص التطعيمات يومياً في الساعة 10 صباحاً
        schedule.every().day.at("10:00").do(self._safe_run, self.monitor.check_vaccination_reminders)
        
        # تنظيف الإشعارات القديمة أسبوعياً
        schedule.every().sunday.at("02:00").do(self._safe_run, self._cleanup_old_notifications)
        
        # تحديث إحصائيات الإشعارات يومياً
        schedule.every().day.at("23:30").do(self._safe_run, self._update_notification_stats)
        
        # معالجة الإشعارات المجدولة كل دقيقة
        schedule.every().minute.do(self._safe_run, self._process_scheduled_notifications)
        
        # فحص القواعد التلقائية كل ساعة
        schedule.every().hour.do(self._safe_run, self._process_notification_rules)
    
    def _run_scheduler(self):
        """تشغيل الجدولة في خيط منفصل"""
        with app.app_context():
            while self.running:
                try:
                    schedule.run_pending()
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Error in scheduler loop: {e}")
                    time.sleep(5)
    
    def _safe_run(self, func):
        """تشغيل آمن للمهام مع معالجة الأخطاء"""
        try:
            with app.app_context():
                func()
        except Exception as e:
            logger.error(f"Error running scheduled task {func.__name__}: {e}")
    
    def _process_scheduled_notifications(self):
        """معالجة الإشعارات المجدولة"""
        try:
            from models_notifications import Notification, NotificationStatus
            
            # البحث عن الإشعارات المجدولة التي حان وقتها
            now = datetime.utcnow()
            pending_notifications = Notification.query.filter(
                Notification.status == NotificationStatus.PENDING,
                Notification.scheduled_for <= now
            ).all()
            
            for notification in pending_notifications:
                try:
                    self.notification_service._send_notification(notification)
                    logger.info(f"Sent scheduled notification {notification.id}")
                except Exception as e:
                    logger.error(f"Error sending scheduled notification {notification.id}: {e}")
                    notification.status = NotificationStatus.FAILED
                    db.session.commit()
            
        except Exception as e:
            logger.error(f"Error processing scheduled notifications: {e}")
    
    def _process_notification_rules(self):
        """معالجة قواعد الإشعارات التلقائية"""
        try:
            # البحث عن القواعد النشطة التي تحتاج تشغيل
            now = datetime.utcnow()
            
            active_rules = NotificationRule.query.filter(
                NotificationRule.is_active == True,
                NotificationRule.next_run <= now
            ).all()
            
            for rule in active_rules:
                try:
                    self._execute_notification_rule(rule)
                    
                    # تحديث موعد التشغيل التالي
                    rule.last_run = now
                    if rule.run_frequency == 'daily':
                        rule.next_run = now + timedelta(days=1)
                    elif rule.run_frequency == 'hourly':
                        rule.next_run = now + timedelta(hours=1)
                    elif rule.run_frequency == 'weekly':
                        rule.next_run = now + timedelta(weeks=1)
                    
                    db.session.commit()
                    
                except Exception as e:
                    logger.error(f"Error executing notification rule {rule.id}: {e}")
            
        except Exception as e:
            logger.error(f"Error processing notification rules: {e}")
    
    def _execute_notification_rule(self, rule: NotificationRule):
        """تنفيذ قاعدة إشعار محددة"""
        try:
            # تحليل شروط التشغيل
            conditions = rule.trigger_condition
            event_type = rule.event_type
            
            # تنفيذ الشروط حسب نوع الحدث
            if event_type == 'attendance':
                self._check_attendance_rule(rule, conditions)
            elif event_type == 'project':
                self._check_project_rule(rule, conditions)
            elif event_type == 'veterinary':
                self._check_veterinary_rule(rule, conditions)
            elif event_type == 'breeding':
                self._check_breeding_rule(rule, conditions)
            
        except Exception as e:
            logger.error(f"Error executing rule {rule.name}: {e}")
    
    def _check_attendance_rule(self, rule: NotificationRule, conditions: dict):
        """فحص قواعد الحضور"""
        # TODO: تنفيذ منطق فحص قواعد الحضور
        pass
    
    def _check_project_rule(self, rule: NotificationRule, conditions: dict):
        """فحص قواعد المشاريع"""
        try:
            # مثال: المشاريع التي تنتهي خلال X أيام
            if 'days_before_end' in conditions:
                days_ahead = conditions['days_before_end']
                target_date = date.today() + timedelta(days=days_ahead)
                
                ending_projects = Project.query.filter(
                    Project.end_date == target_date,
                    Project.status.in_(['ACTIVE', 'PLANNED'])
                ).all()
                
                for project in ending_projects:
                    # إرسال إشعار للمديرين
                    if rule.target_roles:
                        for role in rule.target_roles:
                            self.notification_service.send_to_role(
                                notification_type=rule.notification_type,
                                role=role,
                                title=f"تنبيه انتهاء المشروع",
                                message=f"سينتهي المشروع '{project.name}' خلال {days_ahead} أيام",
                                priority=rule.template.priority if rule.template else NotificationPriority.MEDIUM,
                                related_type='Project',
                                related_id=project.id
                            )
        
        except Exception as e:
            logger.error(f"Error checking project rule: {e}")
    
    def _check_veterinary_rule(self, rule: NotificationRule, conditions: dict):
        """فحص قواعد الطب البيطري"""
        # TODO: تنفيذ منطق فحص قواعد الطب البيطري
        pass
    
    def _check_breeding_rule(self, rule: NotificationRule, conditions: dict):
        """فحص قواعد التربية"""
        try:
            # مثال: دورات الحرارة المتوقعة
            if 'heat_cycle_prediction' in conditions:
                # البحث عن الإناث التي من المتوقع بدء دورة حرارة لها
                female_dogs = Dog.query.filter_by(gender='FEMALE', status='ACTIVE').all()
                
                for dog in female_dogs:
                    # الحصول على آخر دورة حرارة
                    last_cycle = HeatCycle.query.filter_by(dog_id=dog.id).order_by(
                        HeatCycle.start_date.desc()
                    ).first()
                    
                    if last_cycle and last_cycle.end_date:
                        # حساب الدورة المتوقعة التالية (افتراض كل 6 شهور)
                        expected_next = last_cycle.end_date + timedelta(days=180)
                        days_until = (expected_next - date.today()).days
                        
                        # إرسال تنبيه قبل أسبوع
                        if days_until == 7:
                            self.notification_service.send_to_role(
                                notification_type=rule.notification_type,
                                role='BREEDER',
                                title=f"دورة حرارة متوقعة",
                                message=f"من المتوقع بدء دورة حرارة للكلبة {dog.name} خلال أسبوع",
                                related_type='Dog',
                                related_id=dog.id
                            )
        
        except Exception as e:
            logger.error(f"Error checking breeding rule: {e}")
    
    def _cleanup_old_notifications(self):
        """تنظيف الإشعارات القديمة"""
        try:
            from models_notifications import Notification
            
            # حذف الإشعارات المقروءة التي تزيد عن 30 يوم
            month_ago = datetime.utcnow() - timedelta(days=30)
            old_read_notifications = Notification.query.filter(
                Notification.status == NotificationStatus.READ,
                Notification.read_at <= month_ago
            )
            
            count = old_read_notifications.count()
            old_read_notifications.delete()
            
            # حذف الإشعارات الفاشلة التي تزيد عن 7 أيام
            week_ago = datetime.utcnow() - timedelta(days=7)
            old_failed_notifications = Notification.query.filter(
                Notification.status == NotificationStatus.FAILED,
                Notification.created_at <= week_ago
            )
            
            failed_count = old_failed_notifications.count()
            old_failed_notifications.delete()
            
            db.session.commit()
            
            logger.info(f"Cleaned up {count} old read and {failed_count} failed notifications")
            
        except Exception as e:
            logger.error(f"Error cleaning up old notifications: {e}")
    
    def _update_notification_stats(self):
        """تحديث إحصائيات الإشعارات"""
        try:
            # TODO: تنفيذ تحديث الإحصائيات اليومية
            # يمكن حفظ إحصائيات يومية في جدول منفصل للتقارير
            pass
            
        except Exception as e:
            logger.error(f"Error updating notification stats: {e}")

# إنشاء مثيل المجدول العام
scheduler = None

def init_notification_scheduler(notification_service: NotificationService):
    """تهيئة مجدول الإشعارات"""
    global scheduler
    if scheduler is None:
        scheduler = NotificationScheduler(notification_service)
        scheduler.start()
    return scheduler

def get_notification_scheduler():
    """الحصول على مجدول الإشعارات"""
    return scheduler