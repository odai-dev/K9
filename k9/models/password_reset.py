from app import db
from datetime import datetime, timedelta
from k9.models.models import get_uuid_column, default_uuid
import secrets

class PasswordResetToken(db.Model):
    """Model for secure password reset tokens."""
    
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    ip_address = db.Column(db.String(45))  # Supports IPv6
    user_agent = db.Column(db.Text)
    
    # Relationship
    user = db.relationship('User', backref='password_reset_tokens')
    
    def __init__(self, user_id, hours_valid=24, ip_address=None, user_agent=None):
        self.user_id = user_id
        self.token = secrets.token_urlsafe(32)
        self.expires_at = datetime.utcnow() + timedelta(hours=hours_valid)
        self.ip_address = ip_address
        self.user_agent = user_agent
    
    @property
    def is_expired(self):
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid (not used and not expired)."""
        return not self.used and not self.is_expired
    
    def mark_as_used(self):
        """Mark token as used."""
        self.used = True
        self.used_at = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired tokens from database."""
        expired_tokens = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
        for token in expired_tokens:
            db.session.delete(token)
        db.session.commit()
        return len(expired_tokens)
    
    def __repr__(self):
        return f'<PasswordResetToken {self.id} for user {self.user_id}>'