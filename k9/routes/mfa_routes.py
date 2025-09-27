from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app import db, csrf
from k9.utils.security_utils import MFAManager, SecurityHelper, PasswordValidator
from datetime import datetime

mfa_bp = Blueprint('mfa', __name__, url_prefix='/mfa')

@mfa_bp.route('/setup', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def setup():
    """MFA setup page."""
    if current_user.mfa_enabled:
        flash('المصادقة الثنائية مفعلة بالفعل', 'info')
        return redirect(url_for('mfa.status'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'generate_secret':
            # Generate new secret and QR code
            secret = MFAManager.generate_secret()
            qr_code = MFAManager.generate_qr_code(current_user, secret)
            
            # Store secret temporarily in session
            session['temp_mfa_secret'] = secret
            
            return render_template('auth/mfa_setup.html', 
                                 qr_code=qr_code, 
                                 secret=secret,
                                 step='verify')
        
        elif action == 'verify_and_enable':
            # Verify TOTP token and enable MFA
            token = request.form.get('token', '').strip()
            secret = session.get('temp_mfa_secret')
            
            if not secret:
                flash('انتهت صلاحية العملية، يرجى البدء من جديد', 'error')
                return redirect(url_for('mfa.setup'))
            
            if MFAManager.verify_totp(secret, token):
                # Generate backup codes
                backup_codes = MFAManager.generate_backup_codes()
                hashed_codes = MFAManager.hash_backup_codes(backup_codes)
                
                # Enable MFA
                current_user.mfa_enabled = True
                current_user.mfa_secret = secret
                current_user.backup_codes = hashed_codes
                db.session.commit()
                
                # Clear temporary secret
                session.pop('temp_mfa_secret', None)
                
                # Log security event
                SecurityHelper.log_security_event(current_user.id, 'MFA_ENABLED', {
                    'username': current_user.username
                })
                
                flash('تم تفعيل المصادقة الثنائية بنجاح', 'success')
                
                return render_template('auth/mfa_backup_codes.html', 
                                     backup_codes=backup_codes)
            else:
                flash('رمز التحقق غير صحيح، يرجى المحاولة مرة أخرى', 'error')
                secret = session.get('temp_mfa_secret')
                qr_code = MFAManager.generate_qr_code(current_user, secret)
                return render_template('auth/mfa_setup.html',
                                     qr_code=qr_code,
                                     secret=secret,
                                     step='verify')
    
    return render_template('auth/mfa_setup.html', step='start')

@mfa_bp.route('/status')
@login_required
def status():
    """MFA status and management page."""
    return render_template('auth/mfa_status.html')

@mfa_bp.route('/disable', methods=['POST'])
@login_required
@csrf.exempt
def disable():
    """Disable MFA."""
    if not current_user.mfa_enabled:
        flash('المصادقة الثنائية غير مفعلة', 'info')
        return redirect(url_for('mfa.status'))
    
    # Verify current password
    password = request.form.get('password', '')
    from werkzeug.security import check_password_hash
    
    if not check_password_hash(current_user.password_hash, password):
        flash('كلمة المرور غير صحيحة', 'error')
        return redirect(url_for('mfa.status'))
    
    # Disable MFA
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    current_user.backup_codes = []
    db.session.commit()
    
    # Log security event
    SecurityHelper.log_security_event(current_user.id, 'MFA_DISABLED', {
        'username': current_user.username
    })
    
    flash('تم إلغاء تفعيل المصادقة الثنائية', 'success')
    return redirect(url_for('mfa.status'))

@mfa_bp.route('/regenerate-backup-codes', methods=['POST'])
@login_required
@csrf.exempt
def regenerate_backup_codes():
    """Regenerate backup codes."""
    if not current_user.mfa_enabled:
        flash('المصادقة الثنائية غير مفعلة', 'error')
        return redirect(url_for('mfa.status'))
    
    # Verify MFA token
    token = request.form.get('token', '').strip()
    if not MFAManager.verify_totp(current_user.mfa_secret, token):
        flash('رمز المصادقة الثنائية غير صحيح', 'error')
        return redirect(url_for('mfa.status'))
    
    # Generate new backup codes
    backup_codes = MFAManager.generate_backup_codes()
    hashed_codes = MFAManager.hash_backup_codes(backup_codes)
    
    current_user.backup_codes = hashed_codes
    db.session.commit()
    
    # Log security event
    SecurityHelper.log_security_event(current_user.id, 'BACKUP_CODES_REGENERATED', {
        'username': current_user.username
    })
    
    flash('تم إنشاء رموز احتياطية جديدة', 'success')
    return render_template('auth/mfa_backup_codes.html', backup_codes=backup_codes)

@mfa_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def change_password():
    """Change password with complexity validation."""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Verify current password
        from werkzeug.security import check_password_hash
        if not check_password_hash(current_user.password_hash, current_password):
            flash('كلمة المرور الحالية غير صحيحة', 'error')
            return render_template('auth/change_password.html')
        
        # Check password confirmation
        if new_password != confirm_password:
            flash('كلمة المرور الجديدة وتأكيد كلمة المرور غير متطابقين', 'error')
            return render_template('auth/change_password.html')
        
        # Validate password complexity
        is_valid, error_msg = PasswordValidator.validate_password(new_password)
        if not is_valid:
            flash(f'كلمة المرور لا تتوافق مع متطلبات الأمان: {error_msg}', 'error')
            return render_template('auth/change_password.html')
        
        # Check if new password is same as current
        if check_password_hash(current_user.password_hash, new_password):
            flash('كلمة المرور الجديدة يجب أن تكون مختلفة عن الحالية', 'error')
            return render_template('auth/change_password.html')
        
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        current_user.password_changed_at = datetime.utcnow()
        current_user.failed_login_attempts = 0  # Reset failed attempts
        current_user.account_locked_until = None  # Unlock account if locked
        db.session.commit()
        
        # Log security event
        SecurityHelper.log_security_event(current_user.id, 'PASSWORD_CHANGED', {
            'username': current_user.username
        })
        
        flash('تم تغيير كلمة المرور بنجاح', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/change_password.html')