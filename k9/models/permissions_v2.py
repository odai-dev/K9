"""
Simplified Role-Based Permission System V2
==========================================
A clean, maintainable permission system based on:
- Roles with predefined permission sets
- Project-scoped role assignments
- Individual permission overrides (grant/revoke)
"""
from app import db
from datetime import datetime
from k9.models.model_utils import get_uuid_column, default_uuid


class RoleType:
    """Role type constants - stored as strings for flexibility"""
    SUPER_ADMIN = "super_admin"
    GENERAL_ADMIN = "general_admin"
    PROJECT_MANAGER = "project_manager"
    HANDLER = "handler"
    VETERINARIAN = "veterinarian"
    TRAINER = "trainer"
    BREEDER = "breeder"
    VIEWER = "viewer"


class PermissionKey:
    """
    Simplified permission keys - organized by module
    Format: module.action (e.g., dogs.view, dogs.edit)
    """
    # Dogs module
    DOGS_VIEW = "dogs.view"
    DOGS_CREATE = "dogs.create"
    DOGS_EDIT = "dogs.edit"
    DOGS_DELETE = "dogs.delete"
    DOGS_EXPORT = "dogs.export"
    
    # Employees module
    EMPLOYEES_VIEW = "employees.view"
    EMPLOYEES_CREATE = "employees.create"
    EMPLOYEES_EDIT = "employees.edit"
    EMPLOYEES_DELETE = "employees.delete"
    EMPLOYEES_EXPORT = "employees.export"
    
    # Projects module
    PROJECTS_VIEW = "projects.view"
    PROJECTS_CREATE = "projects.create"
    PROJECTS_EDIT = "projects.edit"
    PROJECTS_DELETE = "projects.delete"
    PROJECTS_MANAGE_TEAM = "projects.manage_team"
    
    # Training module
    TRAINING_VIEW = "training.view"
    TRAINING_CREATE = "training.create"
    TRAINING_EDIT = "training.edit"
    TRAINING_DELETE = "training.delete"
    
    # Veterinary module
    VETERINARY_VIEW = "veterinary.view"
    VETERINARY_CREATE = "veterinary.create"
    VETERINARY_EDIT = "veterinary.edit"
    VETERINARY_DELETE = "veterinary.delete"
    
    # Breeding module
    BREEDING_VIEW = "breeding.view"
    BREEDING_CREATE = "breeding.create"
    BREEDING_EDIT = "breeding.edit"
    BREEDING_DELETE = "breeding.delete"
    
    # Reports module
    REPORTS_VIEW = "reports.view"
    REPORTS_CREATE = "reports.create"
    REPORTS_EDIT = "reports.edit"
    REPORTS_APPROVE = "reports.approve"
    REPORTS_EXPORT = "reports.export"
    REPORTS_FINAL_APPROVE = "reports.final_approve"
    
    # Schedule/Attendance module
    SCHEDULE_VIEW = "schedule.view"
    SCHEDULE_CREATE = "schedule.create"
    SCHEDULE_EDIT = "schedule.edit"
    SCHEDULE_APPROVE = "schedule.approve"
    
    # Users/Accounts module
    USERS_VIEW = "users.view"
    USERS_CREATE = "users.create"
    USERS_EDIT = "users.edit"
    USERS_DELETE = "users.delete"
    USERS_MANAGE_PERMISSIONS = "users.manage_permissions"
    
    # Admin module
    ADMIN_DASHBOARD = "admin.dashboard"
    ADMIN_SETTINGS = "admin.settings"
    ADMIN_BACKUP = "admin.backup"
    ADMIN_AUDIT = "admin.audit"
    
    # Handler daily operations
    HANDLER_DAILY_VIEW = "handler_daily.view"
    HANDLER_DAILY_CREATE = "handler_daily.create"
    HANDLER_DAILY_EDIT = "handler_daily.edit"
    
    # PM operations
    PM_DASHBOARD = "pm.dashboard"
    PM_REVIEW_REPORTS = "pm.review_reports"
    PM_MANAGE_PROJECT = "pm.manage_project"


# Role to permissions mapping - defines what each role can do
ROLE_PERMISSIONS = {
    RoleType.SUPER_ADMIN: ["*"],  # All permissions
    
    RoleType.GENERAL_ADMIN: [
        # Full access to everything except super admin features
        "dogs.*", "employees.*", "projects.*", "training.*",
        "veterinary.*", "breeding.*", "reports.*", "schedule.*",
        "users.*", "admin.*", "handler_daily.*", "pm.*"
    ],
    
    RoleType.PROJECT_MANAGER: [
        "dogs.view", "dogs.export",
        "employees.view",
        "projects.view", "projects.edit", "projects.manage_team",
        "training.view",
        "veterinary.view",
        "breeding.view",
        "reports.view", "reports.approve", "reports.export",
        "schedule.view", "schedule.approve",
        "pm.dashboard", "pm.review_reports", "pm.manage_project",
        "handler_daily.view"
    ],
    
    RoleType.HANDLER: [
        "dogs.view",
        "training.view", "training.create",
        "veterinary.view",
        "reports.view", "reports.create",
        "schedule.view",
        "handler_daily.view", "handler_daily.create", "handler_daily.edit"
    ],
    
    RoleType.VETERINARIAN: [
        "dogs.view",
        "veterinary.view", "veterinary.create", "veterinary.edit",
        "reports.view", "reports.create",
        "handler_daily.view"
    ],
    
    RoleType.TRAINER: [
        "dogs.view",
        "training.view", "training.create", "training.edit",
        "reports.view", "reports.create",
        "handler_daily.view"
    ],
    
    RoleType.BREEDER: [
        "dogs.view",
        "breeding.view", "breeding.create", "breeding.edit",
        "reports.view", "reports.create",
        "handler_daily.view"
    ],
    
    RoleType.VIEWER: [
        "dogs.view", "employees.view", "projects.view",
        "training.view", "veterinary.view", "breeding.view",
        "reports.view", "schedule.view"
    ]
}


class Role(db.Model):
    """
    System roles - predefined or custom
    """
    __tablename__ = 'roles_v2'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name_ar = db.Column(db.String(100))
    description = db.Column(db.Text)
    
    is_system = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Role {self.name}>'


class UserRoleAssignment(db.Model):
    """
    Assigns roles to users, optionally scoped to a project
    """
    __tablename__ = 'user_role_assignments_v2'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    role_id = db.Column(get_uuid_column(), db.ForeignKey('roles_v2.id', ondelete='CASCADE'), nullable=False, index=True)
    
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id', ondelete='CASCADE'), nullable=True, index=True)
    
    is_active = db.Column(db.Boolean, default=True)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    granted_by_id = db.Column(get_uuid_column(), db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='role_assignments_v2')
    role = db.relationship('Role', backref='user_assignments')
    project = db.relationship('Project', backref='role_assignments')
    granted_by = db.relationship('User', foreign_keys=[granted_by_id])
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'role_id', 'project_id', name='unique_user_role_project'),
        db.Index('idx_user_role_project', 'user_id', 'role_id', 'project_id'),
    )
    
    def __repr__(self):
        project_str = f" for project {self.project_id}" if self.project_id else " (global)"
        return f'<UserRoleAssignment {self.user_id} -> {self.role.name if self.role else self.role_id}{project_str}>'


class PermissionOverride(db.Model):
    """
    Individual permission overrides for users
    Use sparingly - for exceptions only
    """
    __tablename__ = 'permission_overrides_v2'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    permission_key = db.Column(db.String(100), nullable=False, index=True)
    
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id', ondelete='CASCADE'), nullable=True, index=True)
    
    is_granted = db.Column(db.Boolean, nullable=False)
    reason = db.Column(db.Text)
    
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    granted_by_id = db.Column(get_uuid_column(), db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='permission_overrides_v2')
    project = db.relationship('Project', backref='permission_overrides')
    granted_by = db.relationship('User', foreign_keys=[granted_by_id])
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'permission_key', 'project_id', name='unique_user_permission_override'),
        db.Index('idx_user_permission_override', 'user_id', 'permission_key', 'project_id'),
    )
    
    def __repr__(self):
        action = "granted" if self.is_granted else "revoked"
        return f'<PermissionOverride {self.permission_key} {action} for user {self.user_id}>'


class PermissionAuditLog(db.Model):
    """
    Audit trail for all permission changes
    """
    __tablename__ = 'permission_audit_logs_v2'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    
    target_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    changed_by_id = db.Column(get_uuid_column(), db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    
    action = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(get_uuid_column(), nullable=True)
    
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    details = db.Column(db.Text)
    
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id', ondelete='SET NULL'), nullable=True)
    ip_address = db.Column(db.String(45))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    target_user = db.relationship('User', foreign_keys=[target_user_id])
    changed_by = db.relationship('User', foreign_keys=[changed_by_id])
    project = db.relationship('Project')
    
    __table_args__ = (
        db.Index('idx_audit_target_user', 'target_user_id'),
        db.Index('idx_audit_changed_by', 'changed_by_id'),
        db.Index('idx_audit_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f'<PermissionAuditLog {self.action} by {self.changed_by_id} at {self.created_at}>'
