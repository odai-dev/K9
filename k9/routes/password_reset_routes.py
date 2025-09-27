from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user
from app import db, csrf
from k9.models.models import User
from k9.models.password_reset import PasswordResetToken
from k9.utils.security_utils import PasswordValidator, SecurityHelper
from k9.utils.email_service import EmailService
from werkzeug.security import generate_password_hash
from datetime import datetime

password_reset_bp = Blueprint('password_reset', __name__, url_prefix='/password-reset')

@password_reset_bp.route('/request', methods=['GET', 'POST'])
@csrf.exempt
def request_reset():
    """Request password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('يرجى إدخال عنوان البريد الإلكتروني', 'error')
            return render_template('auth/password_reset_request.html')
        
        # Always show success message for security (prevent email enumeration)
        success_message = 'إذا كان البريد الإلكتروني مسجلاً في النظام، ستتلقى رسالة تحتوي على تعليمات إعادة تعيين كلمة المرور'
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.active:
            try:
                # Clean up old tokens for this user
                old_tokens = PasswordResetToken.query.filter_by(user_id=user.id).all()
                for token in old_tokens:
                    db.session.delete(token)
                
                # Create new reset token
                reset_token = PasswordResetToken(
                    user_id=user.id,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')
                )
                
                db.session.add(reset_token)
                db.session.commit()
                
                # Send reset email
                email_service = EmailService()
                reset_url = url_for('password_reset.reset_password', 
                                  token=reset_token.token, 
                                  _external=True)
                
                email_sent = email_service.send_password_reset_email(
                    user_email=user.email,
                    user_name=user.full_name,
                    reset_token=reset_token.token,
                    reset_url=reset_url
                )
                
                # Log security event
                SecurityHelper.log_security_event(user.id, 'PASSWORD_RESET_REQUESTED', {
                    'email': email,
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', ''),
                    'email_sent': email_sent
                })
                
                if not email_sent:
                    # Safe environment check for development behavior
                    import os
                    is_development = (current_app.debug or 
                                    current_app.config.get('ENV') == 'development' or 
                                    os.getenv('FLASK_ENV') == 'development' or
                                    os.getenv('APP_SHOW_DEV_RESET_LINK') == '1')
                    
                    if is_development:
                        # Log the token for development/testing only
                        current_app.logger.info(f"Password reset token for {email}: {reset_token.token}")
                        current_app.logger.info(f"Reset URL: {reset_url}")
                        current_app.logger.warning("Development mode: Showing password reset link directly (email service not configured)")
                        flash('تعذر إرسال البريد الإلكتروني - الوضع التطويري', 'warning')
                        return render_template('auth/password_reset_request.html', success=True, reset_url=reset_url, development_mode=True)
                    else:
                        # In production, only log that email failed (no sensitive data)
                        current_app.logger.error("Email service failed to send password reset email - please check email configuration")
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Password reset error: {e}")
        
        flash(success_message, 'info')
        return render_template('auth/password_reset_request.html', success=True)
    
    return render_template('auth/password_reset_request.html')

@password_reset_bp.route('/reset/<token>', methods=['GET', 'POST'])
@csrf.exempt
def reset_password(token):
    """Reset password using token."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Find and validate token
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    
    if not reset_token or not reset_token.is_valid:
        flash('رابط إعادة تعيين كلمة المرور غير صالح أو منتهي الصلاحية', 'error')
        return redirect(url_for('password_reset.request_reset'))
    
    user = reset_token.user
    if not user or not user.active:
        flash('المستخدم غير موجود أو غير نشط', 'error')
        return redirect(url_for('password_reset.request_reset'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate passwords match
        if new_password != confirm_password:
            flash('كلمات المرور غير متطابقة', 'error')
            return render_template('auth/password_reset_form.html', token=token, user=user)
        
        # Validate password complexity
        is_valid, error_msg = PasswordValidator.validate_password(new_password)
        if not is_valid:
            flash(f'كلمة المرور لا تتوافق مع متطلبات الأمان: {error_msg}', 'error')
            return render_template('auth/password_reset_form.html', token=token, user=user)
        
        try:
            # Update password
            user.password_hash = generate_password_hash(new_password)
            user.password_changed_at = datetime.utcnow()
            user.failed_login_attempts = 0  # Reset failed attempts
            user.account_locked_until = None  # Unlock account
            
            # Mark token as used
            reset_token.mark_as_used()
            
            db.session.commit()
            
            # Log security event
            SecurityHelper.log_security_event(user.id, 'PASSWORD_RESET_COMPLETED', {
                'email': user.email,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'token_id': str(reset_token.id)
            })
            
            # Send security alert email
            email_service = EmailService()
            email_service.send_security_alert_email(
                user_email=user.email,
                user_name=user.full_name,
                alert_type='password_changed',
                details={
                    'الوقت': datetime.utcnow().strftime('%Y-%m-%d %H:%M'),
                    'عنوان IP': request.remote_addr,
                    'المتصفح': request.headers.get('User-Agent', 'غير معروف')[:100]
                }
            )
            
            flash('تم تغيير كلمة المرور بنجاح! يمكنك الآن تسجيل الدخول', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.error(f"Password reset completion error: {e}")
            flash('حدث خطأ أثناء تغيير كلمة المرور، يرجى المحاولة مرة أخرى', 'error')
    
    return render_template('auth/password_reset_form.html', token=token, user=user)

@password_reset_bp.route('/cleanup-tokens')
def cleanup_expired_tokens():
    """Clean up expired tokens (admin only)."""
    # Security check: Only allow in development or with explicit admin access
    from flask_login import current_user
    import os
    
    is_development = (current_app.debug or 
                     current_app.config.get('ENV') == 'development' or 
                     os.getenv('FLASK_ENV') == 'development')
    
    if not is_development and not (current_user.is_authenticated and 
                                  getattr(current_user, 'role', None) == 'GENERAL_ADMIN'):
        from flask import abort
        abort(403)
    
    # This would typically be called by a cron job
    try:
        count = PasswordResetToken.cleanup_expired()
        return jsonify({
            'success': True,
            'message': f'Cleaned up {count} expired tokens'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500