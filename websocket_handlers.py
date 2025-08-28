from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_login import current_user
from flask import request
import logging
from notification_service import NotificationService

logger = logging.getLogger(__name__)

def init_socketio_handlers(socketio: SocketIO, notification_service: NotificationService):
    """تهيئة معالجات WebSocket"""
    
    @socketio.on('connect')
    def handle_connect():
        """عند اتصال المستخدم"""
        try:
            if current_user.is_authenticated:
                user_room = f"user_{current_user.id}"
                join_room(user_room)
                
                logger.info(f"User {current_user.id} connected to WebSocket")
                
                # إرسال الإشعارات غير المقروءة
                unread_notifications = notification_service.get_user_notifications(
                    current_user.id, 
                    limit=10, 
                    unread_only=True
                )
                
                emit('unread_notifications', {
                    'notifications': unread_notifications,
                    'count': len(unread_notifications)
                })
                
            else:
                logger.warning("Unauthenticated user attempted WebSocket connection")
                disconnect()
                
        except Exception as e:
            logger.error(f"Error in WebSocket connect: {e}")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """عند قطع الاتصال"""
        try:
            if current_user.is_authenticated:
                user_room = f"user_{current_user.id}"
                leave_room(user_room)
                logger.info(f"User {current_user.id} disconnected from WebSocket")
                
        except Exception as e:
            logger.error(f"Error in WebSocket disconnect: {e}")
    
    @socketio.on('mark_notification_read')
    def handle_mark_read(data):
        """تحديد الإشعار كمقروء"""
        try:
            if not current_user.is_authenticated:
                emit('error', {'message': 'غير مصرح'})
                return
            
            notification_id = data.get('notification_id')
            if not notification_id:
                emit('error', {'message': 'معرف الإشعار مطلوب'})
                return
            
            success = notification_service.mark_as_read(notification_id, current_user.id)
            
            if success:
                emit('notification_marked_read', {'notification_id': notification_id})
            else:
                emit('error', {'message': 'فشل في تحديد الإشعار كمقروء'})
                
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            emit('error', {'message': 'حدث خطأ في النظام'})
    
    @socketio.on('get_notifications')
    def handle_get_notifications(data):
        """الحصول على الإشعارات"""
        try:
            if not current_user.is_authenticated:
                emit('error', {'message': 'غير مصرح'})
                return
            
            limit = data.get('limit', 20)
            unread_only = data.get('unread_only', False)
            
            notifications = notification_service.get_user_notifications(
                current_user.id,
                limit=limit,
                unread_only=unread_only
            )
            
            emit('notifications_list', {
                'notifications': notifications,
                'count': len(notifications)
            })
            
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            emit('error', {'message': 'فشل في تحميل الإشعارات'})
    
    @socketio.on('update_notification_settings')
    def handle_update_settings(data):
        """تحديث إعدادات الإشعارات"""
        try:
            if not current_user.is_authenticated:
                emit('error', {'message': 'غير مصرح'})
                return
            
            # تنظيف البيانات
            allowed_fields = [
                'enabled', 'quiet_hours_start', 'quiet_hours_end',
                'attendance_alerts', 'vaccination_reminders', 'project_updates',
                'heat_cycle_alerts', 'training_reminders', 'vet_checkup_reminders',
                'emergency_alerts', 'system_updates', 'browser_notifications',
                'push_notifications', 'email_notifications'
            ]
            
            update_data = {k: v for k, v in data.items() if k in allowed_fields}
            
            settings = notification_service.update_user_settings(current_user.id, **update_data)
            
            emit('settings_updated', {
                'success': True,
                'message': 'تم تحديث الإعدادات بنجاح'
            })
            
        except Exception as e:
            logger.error(f"Error updating notification settings: {e}")
            emit('error', {'message': 'فشل في تحديث الإعدادات'})
    
    @socketio.on('subscribe_push_notifications')
    def handle_push_subscription(data):
        """تسجيل اشتراك Push Notifications"""
        try:
            if not current_user.is_authenticated:
                emit('error', {'message': 'غير مصرح'})
                return
            
            subscription = data.get('subscription')
            if not subscription:
                emit('error', {'message': 'بيانات الاشتراك مطلوبة'})
                return
            
            # حفظ بيانات الاشتراك
            notification_service.update_user_settings(
                current_user.id,
                push_subscription=subscription,
                push_notifications=True
            )
            
            emit('push_subscription_saved', {
                'success': True,
                'message': 'تم تفعيل الإشعارات الفورية بنجاح'
            })
            
        except Exception as e:
            logger.error(f"Error saving push subscription: {e}")
            emit('error', {'message': 'فشل في تفعيل الإشعارات الفورية'})
    
    @socketio.on('test_notification')
    def handle_test_notification():
        """إرسال إشعار تجريبي"""
        try:
            if not current_user.is_authenticated:
                emit('error', {'message': 'غير مصرح'})
                return
            
            from models_notifications import NotificationType, NotificationPriority
            
            notification_service.create_notification(
                notification_type=NotificationType.SYSTEM_MAINTENANCE,
                user_id=current_user.id,
                title="إشعار تجريبي",
                message="هذا إشعار تجريبي للتأكد من عمل النظام بشكل صحيح",
                priority=NotificationPriority.LOW,
                action_url="/dashboard"
            )
            
            emit('test_notification_sent', {
                'success': True,
                'message': 'تم إرسال الإشعار التجريبي'
            })
            
        except Exception as e:
            logger.error(f"Error sending test notification: {e}")
            emit('error', {'message': 'فشل في إرسال الإشعار التجريبي'})

    return socketio