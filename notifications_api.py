from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from notification_service import NotificationService, NotificationMonitor
from models_notifications import *
from models import User
from app import db
from datetime import datetime, time
import os
import json

bp = Blueprint('notifications_api', __name__)

# إنشاء خدمة الإشعارات
notification_service = NotificationService()

@bp.route('/api/notifications/settings', methods=['GET'])
@login_required
def get_settings():
    """الحصول على إعدادات الإشعارات للمستخدم"""
    try:
        settings = notification_service.get_user_settings(current_user.id)
        
        return jsonify({
            'enabled': settings.enabled,
            'quiet_hours_start': settings.quiet_hours_start.strftime('%H:%M') if settings.quiet_hours_start else None,
            'quiet_hours_end': settings.quiet_hours_end.strftime('%H:%M') if settings.quiet_hours_end else None,
            'attendance_alerts': settings.attendance_alerts,
            'vaccination_reminders': settings.vaccination_reminders,
            'project_updates': settings.project_updates,
            'heat_cycle_alerts': settings.heat_cycle_alerts,
            'training_reminders': settings.training_reminders,
            'vet_checkup_reminders': settings.vet_checkup_reminders,
            'emergency_alerts': settings.emergency_alerts,
            'system_updates': settings.system_updates,
            'browser_notifications': settings.browser_notifications,
            'push_notifications': settings.push_notifications,
            'email_notifications': settings.email_notifications
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting notification settings: {e}")
        return jsonify({'error': 'فشل في تحميل الإعدادات'}), 500

@bp.route('/api/notifications/settings', methods=['POST'])
@login_required
def update_settings():
    """تحديث إعدادات الإشعارات"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'البيانات مطلوبة'}), 400
        
        # تحويل أوقات الساعات الهادئة
        if 'quiet_hours_start' in data and data['quiet_hours_start']:
            try:
                data['quiet_hours_start'] = datetime.strptime(data['quiet_hours_start'], '%H:%M').time()
            except ValueError:
                data['quiet_hours_start'] = None
        
        if 'quiet_hours_end' in data and data['quiet_hours_end']:
            try:
                data['quiet_hours_end'] = datetime.strptime(data['quiet_hours_end'], '%H:%M').time()
            except ValueError:
                data['quiet_hours_end'] = None
        
        settings = notification_service.update_user_settings(current_user.id, **data)
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث الإعدادات بنجاح'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error updating notification settings: {e}")
        return jsonify({'error': 'فشل في تحديث الإعدادات'}), 500

@bp.route('/api/notifications/vapid-key', methods=['GET'])
@login_required
def get_vapid_key():
    """الحصول على مفتاح VAPID العام"""
    try:
        public_key = os.environ.get('VAPID_PUBLIC_KEY', '')
        if not public_key:
            # إنشاء مفاتيح VAPID إذا لم تكن موجودة
            from py_vapid import Vapid
            vapid = Vapid()
            vapid.generate_keys()
            
            # TODO: حفظ المفاتيح في متغيرات البيئة
            public_key = vapid.public_key
        
        return jsonify({
            'public_key': public_key
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting VAPID key: {e}")
        return jsonify({'error': 'فشل في تحميل مفتاح VAPID'}), 500

@bp.route('/api/notifications/list', methods=['GET'])
@login_required
def get_notifications():
    """الحصول على قائمة الإشعارات"""
    try:
        limit = request.args.get('limit', 20, type=int)
        unread_only = request.args.get('unread_only', False, type=bool)
        
        notifications = notification_service.get_user_notifications(
            current_user.id,
            limit=limit,
            unread_only=unread_only
        )
        
        return jsonify({
            'notifications': notifications,
            'count': len(notifications)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting notifications: {e}")
        return jsonify({'error': 'فشل في تحميل الإشعارات'}), 500

@bp.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def mark_notification_read():
    """تحديد الإشعار كمقروء"""
    try:
        data = request.get_json()
        if not data or 'notification_id' not in data:
            return jsonify({'error': 'معرف الإشعار مطلوب'}), 400
        
        notification_id = data['notification_id']
        success = notification_service.mark_as_read(notification_id, current_user.id)
        
        if success:
            return jsonify({'success': True, 'message': 'تم تحديد الإشعار كمقروء'})
        else:
            return jsonify({'error': 'الإشعار غير موجود'}), 404
            
    except Exception as e:
        current_app.logger.error(f"Error marking notification as read: {e}")
        return jsonify({'error': 'فشل في تحديث الإشعار'}), 500

@bp.route('/api/notifications/mark-clicked', methods=['POST'])
def mark_notification_clicked():
    """تسجيل النقر على الإشعار (من Service Worker)"""
    try:
        data = request.get_json()
        if not data or 'notification_id' not in data:
            return jsonify({'error': 'معرف الإشعار مطلوب'}), 400
        
        notification_id = data['notification_id']
        action = data.get('action', 'click')
        
        # البحث عن الإشعار
        notification = Notification.query.get(notification_id)
        if notification:
            # تحديث البيانات الوصفية
            if not notification.metadata:
                notification.metadata = {}
            
            notification.metadata['clicked'] = True
            notification.metadata['click_action'] = action
            notification.metadata['clicked_at'] = datetime.utcnow().isoformat()
            
            # تحديد كمقروء إذا لم يكن كذلك
            if notification.status != NotificationStatus.READ:
                notification.status = NotificationStatus.READ
                notification.read_at = datetime.utcnow()
            
            db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        current_app.logger.error(f"Error marking notification as clicked: {e}")
        return jsonify({'error': 'فشل في تسجيل النقر'}), 500

@bp.route('/api/notifications/mark-dismissed', methods=['POST'])
def mark_notification_dismissed():
    """تسجيل إغلاق الإشعار (من Service Worker)"""
    try:
        data = request.get_json()
        if not data or 'notification_id' not in data:
            return jsonify({'error': 'معرف الإشعار مطلوب'}), 400
        
        notification_id = data['notification_id']
        
        # البحث عن الإشعار
        notification = Notification.query.get(notification_id)
        if notification:
            # تحديث البيانات الوصفية
            if not notification.metadata:
                notification.metadata = {}
            
            notification.metadata['dismissed'] = True
            notification.metadata['dismissed_at'] = datetime.utcnow().isoformat()
            
            db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        current_app.logger.error(f"Error marking notification as dismissed: {e}")
        return jsonify({'error': 'فشل في تسجيل الإغلاق'}), 500

@bp.route('/api/notifications/test', methods=['POST'])
@login_required
def send_test_notification():
    """إرسال إشعار تجريبي"""
    try:
        notification = notification_service.create_notification(
            notification_type=NotificationType.SYSTEM_MAINTENANCE,
            user_id=current_user.id,
            title="إشعار تجريبي",
            message="هذا إشعار تجريبي للتأكد من عمل النظام بشكل صحيح",
            priority=NotificationPriority.LOW,
            action_url="/dashboard"
        )
        
        if notification:
            return jsonify({
                'success': True,
                'message': 'تم إرسال الإشعار التجريبي بنجاح',
                'notification_id': notification.id
            })
        else:
            return jsonify({'error': 'فشل في إرسال الإشعار التجريبي'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error sending test notification: {e}")
        return jsonify({'error': 'فشل في إرسال الإشعار التجريبي'}), 500

@bp.route('/api/notifications/send', methods=['POST'])
@login_required
def send_notification():
    """إرسال إشعار (للمديرين فقط)"""
    try:
        # التحقق من الصلاحيات
        if current_user.role.value != 'GENERAL_ADMIN':
            return jsonify({'error': 'غير مصرح لك بإرسال الإشعارات'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'البيانات مطلوبة'}), 400
        
        required_fields = ['type', 'title', 'message', 'recipients']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'الحقل {field} مطلوب'}), 400
        
        # تحديد نوع الإشعار
        try:
            notification_type = NotificationType(data['type'])
        except ValueError:
            return jsonify({'error': 'نوع الإشعار غير صحيح'}), 400
        
        # تحديد الأولوية
        priority = NotificationPriority.MEDIUM
        if 'priority' in data:
            try:
                priority = NotificationPriority(data['priority'])
            except ValueError:
                pass
        
        notifications = []
        recipients = data['recipients']
        
        # إرسال للمستخدمين المحددين
        if 'user_ids' in recipients:
            for user_id in recipients['user_ids']:
                notification = notification_service.create_notification(
                    notification_type=notification_type,
                    user_id=user_id,
                    title=data['title'],
                    message=data['message'],
                    priority=priority,
                    action_url=data.get('action_url'),
                    metadata=data.get('metadata')
                )
                if notification:
                    notifications.append(notification)
        
        # إرسال للأدوار
        if 'roles' in recipients:
            for role in recipients['roles']:
                role_notifications = notification_service.send_to_role(
                    notification_type=notification_type,
                    role=role,
                    title=data['title'],
                    message=data['message'],
                    priority=priority,
                    action_url=data.get('action_url'),
                    metadata=data.get('metadata')
                )
                notifications.extend(role_notifications)
        
        return jsonify({
            'success': True,
            'message': f'تم إرسال {len(notifications)} إشعار بنجاح',
            'sent_count': len(notifications)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error sending notification: {e}")
        return jsonify({'error': 'فشل في إرسال الإشعار'}), 500

@bp.route('/api/notifications/bulk-mark-read', methods=['POST'])
@login_required
def bulk_mark_read():
    """تحديد عدة إشعارات كمقروءة"""
    try:
        data = request.get_json()
        if not data or 'notification_ids' not in data:
            return jsonify({'error': 'معرفات الإشعارات مطلوبة'}), 400
        
        notification_ids = data['notification_ids']
        success_count = 0
        
        for notification_id in notification_ids:
            if notification_service.mark_as_read(notification_id, current_user.id):
                success_count += 1
        
        return jsonify({
            'success': True,
            'message': f'تم تحديد {success_count} إشعار كمقروء',
            'marked_count': success_count
        })
        
    except Exception as e:
        current_app.logger.error(f"Error bulk marking notifications as read: {e}")
        return jsonify({'error': 'فشل في تحديث الإشعارات'}), 500

@bp.route('/api/notifications/stats', methods=['GET'])
@login_required
def get_notification_stats():
    """الحصول على إحصائيات الإشعارات"""
    try:
        # إحصائيات المستخدم الحالي
        user_notifications = Notification.query.filter_by(user_id=current_user.id)
        
        total_count = user_notifications.count()
        unread_count = user_notifications.filter(Notification.status != NotificationStatus.READ).count()
        
        # إحصائيات الأسبوع الماضي
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_count = user_notifications.filter(Notification.created_at >= week_ago).count()
        
        # إحصائيات حسب النوع
        type_stats = {}
        for notification_type in NotificationType:
            count = user_notifications.filter_by(type=notification_type).count()
            if count > 0:
                type_stats[notification_type.value] = count
        
        return jsonify({
            'total_notifications': total_count,
            'unread_notifications': unread_count,
            'week_notifications': week_count,
            'type_breakdown': type_stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting notification stats: {e}")
        return jsonify({'error': 'فشل في تحميل الإحصائيات'}), 500

# تصدير خدمة الإشعارات للاستخدام في أجزاء أخرى من التطبيق
__all__ = ['bp', 'notification_service']