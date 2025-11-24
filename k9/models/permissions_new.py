"""
New Simple Permission System
Each permission is a unique key representing access to a specific feature/screen/action.
Users are granted permissions directly without complex role logic.
"""
from app import db
from datetime import datetime
from k9.models.model_utils import get_uuid_column, default_uuid


class Permission(db.Model):
    """Permission keys in the system - one per feature/screen/action"""
    __tablename__ = 'permissions'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Permission {self.key}: {self.name}>'


class UserPermission(db.Model):
    """Permissions granted to users"""
    __tablename__ = 'user_permissions'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    permission_id = db.Column(get_uuid_column(), db.ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False, index=True)
    
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    granted_by_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='user_permissions_new')
    permission = db.relationship('Permission', backref='user_grants')
    granted_by = db.relationship('User', foreign_keys=[granted_by_user_id], backref='permissions_granted_to_others')
    
    # Ensure unique permission grant per user
    __table_args__ = (
        db.UniqueConstraint('user_id', 'permission_id', name='unique_user_permission'),
        db.Index('idx_user_permission_lookup', 'user_id', 'permission_id'),
    )
    
    def __repr__(self):
        return f'<UserPermission User:{self.user_id} Permission:{self.permission.key}>'


class PermissionChangeLog(db.Model):
    """Audit trail for permission changes"""
    __tablename__ = 'permission_change_logs'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    permission_id = db.Column(get_uuid_column(), db.ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False)
    action = db.Column(db.String(20), nullable=False)  # 'granted' or 'revoked'
    changed_by_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    ip_address = db.Column(db.String(45))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='permission_changes_new')
    permission = db.relationship('Permission', backref='change_logs')
    changed_by = db.relationship('User', foreign_keys=[changed_by_user_id], backref='permission_changes_made_new')
    
    def __repr__(self):
        return f'<PermissionChangeLog {self.action} {self.permission.key} to User:{self.user_id}>'
