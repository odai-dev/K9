import re
import secrets
import pyotp
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta
from flask import current_app
from werkzeug.security import generate_password_hash

class PasswordValidator:
    """Password complexity validation utility."""
    
    @staticmethod
    def validate_password(password):
        """
        Validate password complexity.
        Returns (is_valid, error_message)
        """
        errors = []
        
        # Minimum length check
        if len(password) < 8:
            errors.append("كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل")
        
        # Maximum length check
        if len(password) > 128:
            errors.append("كلمة المرور طويلة جداً (الحد الأقصى 128 حرف)")
        
        # Character requirements
        if not re.search(r'[a-z]', password):
            errors.append("كلمة المرور يجب أن تحتوي على حرف صغير واحد على الأقل")
        
        if not re.search(r'[A-Z]', password):
            errors.append("كلمة المرور يجب أن تحتوي على حرف كبير واحد على الأقل")
        
        if not re.search(r'\d', password):
            errors.append("كلمة المرور يجب أن تحتوي على رقم واحد على الأقل")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("كلمة المرور يجب أن تحتوي على رمز خاص واحد على الأقل (!@#$%^&*)")
        
        # Common passwords check
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'admin', 'admin123', 'password123', '12345678', 'welcome'
        ]
        if password.lower() in common_passwords:
            errors.append("كلمة المرور ضعيفة جداً، يرجى اختيار كلمة مرور أقوى")
        
        if errors:
            return False, " • ".join(errors)
        
        return True, ""

class AccountLockoutManager:
    """Account lockout management utility."""
    
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    
    @staticmethod
    def is_account_locked(user):
        """Check if user account is currently locked."""
        if not user.account_locked_until:
            return False
        
        return datetime.utcnow() < user.account_locked_until
    
    @staticmethod
    def increment_failed_attempts(user):
        """Increment failed login attempts and lock account if needed."""
        from app import db
        
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        
        if user.failed_login_attempts >= AccountLockoutManager.MAX_FAILED_ATTEMPTS:
            user.account_locked_until = datetime.utcnow() + timedelta(
                minutes=AccountLockoutManager.LOCKOUT_DURATION_MINUTES
            )
        
        db.session.commit()
    
    @staticmethod
    def reset_failed_attempts(user):
        """Reset failed login attempts after successful login."""
        from app import db
        
        user.failed_login_attempts = 0
        user.account_locked_until = None
        db.session.commit()
    
    @staticmethod
    def get_lockout_time_remaining(user):
        """Get remaining lockout time in minutes."""
        if not AccountLockoutManager.is_account_locked(user):
            return 0
        
        remaining = user.account_locked_until - datetime.utcnow()
        return max(0, int(remaining.total_seconds() / 60))

class MFAManager:
    """Multi-Factor Authentication management utility."""
    
    @staticmethod
    def generate_secret():
        """Generate a new TOTP secret."""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(user, secret):
        """Generate QR code for TOTP setup."""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="K9 Operations Management"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 string
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def verify_totp(secret, token):
        """Verify TOTP token."""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    @staticmethod
    def generate_backup_codes(count=10):
        """Generate backup codes for MFA recovery."""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()
            codes.append(f"{code[:4]}-{code[4:]}")
        return codes
    
    @staticmethod
    def hash_backup_codes(codes):
        """Hash backup codes for secure storage."""
        return [generate_password_hash(code) for code in codes]
    
    @staticmethod
    def verify_backup_code(hashed_codes, entered_code):
        """Verify backup code and remove it if valid."""
        from werkzeug.security import check_password_hash
        
        for i, hashed_code in enumerate(hashed_codes):
            if check_password_hash(hashed_code, entered_code):
                # Remove used backup code
                del hashed_codes[i]
                return True, hashed_codes
        
        return False, hashed_codes

class SecurityHelper:
    """General security helper functions."""
    
    @staticmethod
    def is_password_expired(user, days=90):
        """Check if password has expired."""
        if not user.password_changed_at:
            return True
        
        expiry_date = user.password_changed_at + timedelta(days=days)
        return datetime.utcnow() > expiry_date
    
    @staticmethod
    def generate_secure_token(length=32):
        """Generate a secure random token."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def log_security_event(user_id, event_type, details):
        """Log security-related events."""
        from k9.utils.utils import log_audit
        
        log_audit(user_id, 'SECURITY_EVENT', 'Security', str(user_id), {
            'event_type': event_type,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        })