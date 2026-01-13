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
# Keys must match route decorator keys (canonical 2-part format)
ROLE_PERMISSIONS = {
    RoleType.SUPER_ADMIN: ["*"],  # All permissions
    
    RoleType.GENERAL_ADMIN: [
        # Full access to everything except super admin features
        "dogs.*", "employees.*", "projects.*", "training.*",
        "veterinary.*", "breeding.*", "reports.*", "schedule.*",
        "users.*", "admin.*", "handler_daily.*", "pm.*", "production.*",
        "supervisor.*"
    ],
    
    RoleType.PROJECT_MANAGER: [
        # Dogs module
        "dogs.view", "dogs.create", "dogs.edit", "dogs.export",
        # Employees module
        "employees.view", "employees.create", "employees.edit", "employees.delete",
        # Projects module (includes incidents, suspicions, evaluations)
        "projects.view", "projects.create", "projects.edit", "projects.delete",
        "incidents.view", "incidents.create", "incidents.edit", "incidents.resolve",
        "suspicions.view", "suspicions.create",
        "evaluations.view", "evaluations.create",
        # Training module
        "training.view", "training.create", "training.edit",
        # Veterinary module
        "veterinary.view", "veterinary.create", "veterinary.edit",
        # Breeding module
        "breeding.view", "breeding.create", "breeding.edit",
        # Production module
        "production.view", "production.create",
        # Reports module
        "reports.view", "reports.create", "reports.approve", "reports.export",
        "reports.attendance.view",
        # Schedule module - all schedule operations
        "schedule.view", "schedule.create", "schedule.edit", "schedule.approve",
        "schedule.management.view", "schedule.management.create", 
        "schedule.management.edit", "schedule.management.delete",
        # Shifts module
        "shifts.view", "shifts.create", "shifts.edit",
        # Tasks module
        "tasks.management.view", "tasks.management.create", 
        "tasks.management.edit", "tasks.management.delete",
        "tasks.my_tasks.view", "tasks.my_tasks.start", "tasks.my_tasks.complete",
        # PM operations
        "pm.dashboard", "pm.review_reports", "pm.manage_project",
        # Handler daily
        "handler_daily.view",
        # Supervisor - full access to schedules and reports
        "supervisor.reports.view", "supervisor.reports.approve", "supervisor.reports.reject",
        "supervisor.schedules.view", "supervisor.schedules.create", 
        "supervisor.schedules.lock", "supervisor.schedules.delete"
    ],
    
    RoleType.HANDLER: [
        # Dogs module
        "dogs.view",
        # Training module
        "training.view", "training.create",
        # Veterinary module
        "veterinary.view",
        # Reports module
        "reports.view", "reports.create",
        # Schedule module
        "schedule.view",
        # Handler daily
        "handler_daily.view", "handler_daily.create", "handler_daily.edit"
    ],
    
    RoleType.VETERINARIAN: [
        # Dogs module
        "dogs.view",
        # Veterinary module
        "veterinary.view", "veterinary.create", "veterinary.edit",
        # Reports module
        "reports.view", "reports.create",
        # Handler daily
        "handler_daily.view"
    ],
    
    RoleType.TRAINER: [
        # Dogs module
        "dogs.view",
        # Training module
        "training.view", "training.create", "training.edit",
        # Reports module
        "reports.view", "reports.create",
        # Handler daily
        "handler_daily.view"
    ],
    
    RoleType.BREEDER: [
        # Dogs module
        "dogs.view",
        # Breeding module
        "breeding.view", "breeding.create", "breeding.edit",
        # Production module
        "production.view", "production.create", "production.edit",
        # Reports module
        "reports.view", "reports.create",
        # Handler daily
        "handler_daily.view"
    ],
    
    RoleType.VIEWER: [
        # Dogs module
        "dogs.view",
        # Employees module
        "employees.view",
        # Projects module
        "projects.view",
        # Training module
        "training.view",
        # Veterinary module
        "veterinary.view",
        # Breeding module
        "breeding.view",
        # Reports module
        "reports.view",
        # Schedule module
        "schedule.view"
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
