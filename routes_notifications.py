from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from notifications_api import notification_service

bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@bp.route('/')
@login_required
def notifications_list():
    """صفحة قائمة الإشعارات"""
    return render_template('notifications/list.html')

@bp.route('/settings')
@login_required
def notifications_settings():
    """صفحة إعدادات الإشعارات"""
    return render_template('notifications/settings.html')

@bp.route('/dashboard')
@login_required
def notifications_dashboard():
    """لوحة تحكم الإشعارات (للمديرين فقط)"""
    if current_user.role.value != 'GENERAL_ADMIN':
        return redirect(url_for('notifications.notifications_list'))
    
    return render_template('notifications/dashboard.html')