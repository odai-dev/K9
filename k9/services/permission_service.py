"""
Unified Permission Service V2
=============================
Single source of truth for all permission checks
"""
import fnmatch
from functools import wraps
from flask import g, abort, request, flash, redirect, url_for
from flask_login import current_user
from app import db
from k9.models.permissions_v2 import (
    Role, UserRoleAssignment, PermissionOverride, PermissionAuditLog,
    RoleType, ROLE_PERMISSIONS, PermissionKey
)
from datetime import datetime


class PermissionService:
    """
    Centralized permission checking service with caching
    """
    
    _cache = {}
    _cache_timeout = 300
    
    @classmethod
    def clear_cache(cls, user_id=None):
        """Clear permission cache for a user or all users"""
        if user_id:
            keys_to_remove = [k for k in cls._cache if k.startswith(str(user_id))]
            for key in keys_to_remove:
                del cls._cache[key]
        else:
            cls._cache.clear()
    
    @classmethod
    def get_user_roles(cls, user_id, project_id=None):
        """Get all active roles for a user, optionally for a specific project"""
        query = UserRoleAssignment.query.filter(
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.is_active == True
        ).join(Role)
        
        if project_id:
            query = query.filter(
                db.or_(
                    UserRoleAssignment.project_id == project_id,
                    UserRoleAssignment.project_id.is_(None)
                )
            )
        
        now = datetime.utcnow()
        assignments = query.all()
        
        return [
            a for a in assignments
            if a.expires_at is None or a.expires_at > now
        ]
    
    @classmethod
    def get_role_permissions(cls, role_name):
        """Get all permission keys for a role"""
        return ROLE_PERMISSIONS.get(role_name, [])
    
    @classmethod
    def expand_permission_pattern(cls, pattern, permission_key):
        """
        Check if a permission pattern matches a permission key
        Supports wildcards: * matches everything, module.* matches module.anything
        """
        if pattern == "*":
            return True
        if pattern.endswith(".*"):
            module = pattern[:-2]
            return permission_key.startswith(module + ".")
        return pattern == permission_key
    
    @classmethod
    def has_permission(cls, user_id, permission_key, project_id=None):
        """
        Check if a user has a specific permission
        
        Logic:
        1. Check for explicit override (grant or revoke)
        2. If no override, check user's roles
        3. Super admin has all permissions
        """
        import logging
        logger = logging.getLogger(__name__)
        
        cache_key = f"{user_id}:{permission_key}:{project_id or 'global'}"
        if cache_key in cls._cache:
            cached = cls._cache[cache_key]
            if datetime.utcnow().timestamp() - cached['time'] < cls._cache_timeout:
                return cached['value']
        
        override = PermissionOverride.query.filter(
            PermissionOverride.user_id == user_id,
            PermissionOverride.permission_key == permission_key,
            db.or_(
                PermissionOverride.project_id == project_id,
                PermissionOverride.project_id.is_(None)
            )
        ).first()
        
        if override:
            if override.expires_at and override.expires_at < datetime.utcnow():
                pass
            else:
                logger.debug(f"Permission check: user={user_id}, key={permission_key}, override={override.is_granted}")
                cls._cache[cache_key] = {'value': override.is_granted, 'time': datetime.utcnow().timestamp()}
                return override.is_granted
        
        role_assignments = cls.get_user_roles(user_id, project_id)
        logger.debug(f"Permission check: user={user_id}, key={permission_key}, roles={[a.role.name for a in role_assignments]}")
        
        for assignment in role_assignments:
            role_name = assignment.role.name
            role_permissions = cls.get_role_permissions(role_name)
            logger.debug(f"Role {role_name} has {len(role_permissions)} permissions, looking for {permission_key}")
            
            for perm_pattern in role_permissions:
                if cls.expand_permission_pattern(perm_pattern, permission_key):
                    logger.debug(f"Permission GRANTED: {permission_key} matched by {perm_pattern}")
                    cls._cache[cache_key] = {'value': True, 'time': datetime.utcnow().timestamp()}
                    return True
        
        logger.warning(f"Permission DENIED: user={user_id}, key={permission_key}, roles={[a.role.name for a in role_assignments]}")
        cls._cache[cache_key] = {'value': False, 'time': datetime.utcnow().timestamp()}
        return False
    
    @classmethod
    def has_any_permission(cls, user_id, permission_keys, project_id=None):
        """Check if user has any of the given permissions"""
        return any(cls.has_permission(user_id, key, project_id) for key in permission_keys)
    
    @classmethod
    def has_all_permissions(cls, user_id, permission_keys, project_id=None):
        """Check if user has all of the given permissions"""
        return all(cls.has_permission(user_id, key, project_id) for key in permission_keys)
    
    @classmethod
    def get_user_permissions(cls, user_id, project_id=None):
        """Get all effective permissions for a user"""
        permissions = set()
        
        role_assignments = cls.get_user_roles(user_id, project_id)
        
        for assignment in role_assignments:
            role_name = assignment.role.name
            role_permissions = cls.get_role_permissions(role_name)
            
            for perm in role_permissions:
                if perm == "*":
                    permissions.add("*")
                elif perm.endswith(".*"):
                    permissions.add(perm)
                else:
                    permissions.add(perm)
        
        overrides = PermissionOverride.query.filter(
            PermissionOverride.user_id == user_id,
            db.or_(
                PermissionOverride.project_id == project_id,
                PermissionOverride.project_id.is_(None)
            )
        ).all()
        
        now = datetime.utcnow()
        for override in overrides:
            if override.expires_at and override.expires_at < now:
                continue
            if override.is_granted:
                permissions.add(override.permission_key)
            else:
                permissions.discard(override.permission_key)
        
        return permissions
    
    @classmethod
    def grant_role(cls, user_id, role_name, project_id=None, granted_by_id=None, expires_at=None):
        """Assign a role to a user"""
        role = Role.query.filter_by(name=role_name, is_active=True).first()
        if not role:
            raise ValueError(f"Role '{role_name}' not found or inactive")
        
        existing = UserRoleAssignment.query.filter_by(
            user_id=user_id,
            role_id=role.id,
            project_id=project_id
        ).first()
        
        if existing:
            existing.is_active = True
            existing.granted_at = datetime.utcnow()
            existing.granted_by_id = granted_by_id
            existing.expires_at = expires_at
        else:
            assignment = UserRoleAssignment(
                user_id=user_id,
                role_id=role.id,
                project_id=project_id,
                granted_by_id=granted_by_id,
                expires_at=expires_at
            )
            db.session.add(assignment)
        
        cls._log_audit(
            target_user_id=user_id,
            changed_by_id=granted_by_id,
            action='role_granted',
            entity_type='role',
            entity_id=role.id,
            new_value=role_name,
            project_id=project_id
        )
        
        cls.clear_cache(user_id)
        db.session.commit()
    
    @classmethod
    def revoke_role(cls, user_id, role_name, project_id=None, revoked_by_id=None):
        """Remove a role from a user"""
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            return
        
        assignment = UserRoleAssignment.query.filter_by(
            user_id=user_id,
            role_id=role.id,
            project_id=project_id
        ).first()
        
        if assignment:
            assignment.is_active = False
            
            cls._log_audit(
                target_user_id=user_id,
                changed_by_id=revoked_by_id,
                action='role_revoked',
                entity_type='role',
                entity_id=role.id,
                old_value=role_name,
                project_id=project_id
            )
            
            cls.clear_cache(user_id)
            db.session.commit()
    
    @classmethod
    def clear_user_roles(cls, user_id, cleared_by_id=None):
        """Remove all role assignments from a user"""
        assignments = UserRoleAssignment.query.filter_by(
            user_id=user_id,
            is_active=True
        ).all()
        
        for assignment in assignments:
            assignment.is_active = False
            cls._log_audit(
                target_user_id=user_id,
                changed_by_id=cleared_by_id,
                action='role_revoked',
                entity_type='role',
                entity_id=assignment.role_id,
                old_value=assignment.role.name if assignment.role else None,
                details=f"Revoked role: {assignment.role.name if assignment.role else 'unknown'}"
            )
        
        if assignments:
            cls.clear_cache(user_id)
            db.session.commit()
    
    @classmethod
    def clear_user_overrides(cls, user_id, cleared_by_id=None):
        """Remove all permission overrides from a user"""
        overrides = PermissionOverride.query.filter_by(user_id=user_id).all()
        
        for override in overrides:
            cls._log_audit(
                target_user_id=user_id,
                changed_by_id=cleared_by_id,
                action='permission_revoked',
                entity_type='permission_override',
                old_value=override.permission_key
            )
            db.session.delete(override)
        
        if overrides:
            cls.clear_cache(user_id)
            db.session.commit()
    
    @classmethod
    def grant_permission(cls, user_id, permission_key, project_id=None, granted_by_id=None, reason=None, expires_at=None):
        """Grant an individual permission override"""
        existing = PermissionOverride.query.filter_by(
            user_id=user_id,
            permission_key=permission_key,
            project_id=project_id
        ).first()
        
        if existing:
            old_value = existing.is_granted
            existing.is_granted = True
            existing.reason = reason
            existing.granted_at = datetime.utcnow()
            existing.granted_by_id = granted_by_id
            existing.expires_at = expires_at
        else:
            override = PermissionOverride(
                user_id=user_id,
                permission_key=permission_key,
                project_id=project_id,
                is_granted=True,
                reason=reason,
                granted_by_id=granted_by_id,
                expires_at=expires_at
            )
            db.session.add(override)
            old_value = None
        
        cls._log_audit(
            target_user_id=user_id,
            changed_by_id=granted_by_id,
            action='permission_granted',
            entity_type='permission_override',
            old_value=str(old_value) if old_value is not None else None,
            new_value='True',
            details=f"Permission: {permission_key}, Reason: {reason}",
            project_id=project_id
        )
        
        cls.clear_cache(user_id)
        db.session.commit()
    
    @classmethod
    def revoke_permission(cls, user_id, permission_key, project_id=None, revoked_by_id=None, reason=None):
        """Revoke a permission (override to deny)"""
        existing = PermissionOverride.query.filter_by(
            user_id=user_id,
            permission_key=permission_key,
            project_id=project_id
        ).first()
        
        if existing:
            old_value = existing.is_granted
            existing.is_granted = False
            existing.reason = reason
            existing.granted_at = datetime.utcnow()
            existing.granted_by_id = revoked_by_id
        else:
            override = PermissionOverride(
                user_id=user_id,
                permission_key=permission_key,
                project_id=project_id,
                is_granted=False,
                reason=reason,
                granted_by_id=revoked_by_id
            )
            db.session.add(override)
            old_value = None
        
        cls._log_audit(
            target_user_id=user_id,
            changed_by_id=revoked_by_id,
            action='permission_revoked',
            entity_type='permission_override',
            old_value=str(old_value) if old_value is not None else None,
            new_value='False',
            details=f"Permission: {permission_key}, Reason: {reason}",
            project_id=project_id
        )
        
        cls.clear_cache(user_id)
        db.session.commit()
    
    @classmethod
    def _log_audit(cls, target_user_id, changed_by_id, action, entity_type, entity_id=None,
                   old_value=None, new_value=None, details=None, project_id=None):
        """Create an audit log entry"""
        ip_address = None
        try:
            ip_address = request.remote_addr
        except:
            pass
        
        log = PermissionAuditLog(
            target_user_id=target_user_id,
            changed_by_id=changed_by_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            details=details,
            project_id=project_id,
            ip_address=ip_address
        )
        db.session.add(log)
    
    @classmethod
    def is_super_admin(cls, user_id, project_id=None):
        """Check if user has super admin role"""
        return cls.has_role(user_id, RoleType.SUPER_ADMIN, project_id)
    
    @classmethod
    def is_admin(cls, user_id, project_id=None):
        """Check if user has admin role (super or general)"""
        return (
            cls.has_role(user_id, RoleType.SUPER_ADMIN, project_id) or
            cls.has_role(user_id, RoleType.GENERAL_ADMIN, project_id)
        )
    
    @classmethod
    def has_role(cls, user_id, role_name, project_id=None):
        """Check if user has a specific role"""
        role = Role.query.filter_by(name=role_name, is_active=True).first()
        if not role:
            return False
        
        assignment = UserRoleAssignment.query.filter(
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.role_id == role.id,
            UserRoleAssignment.is_active == True,
            db.or_(
                UserRoleAssignment.project_id == project_id,
                UserRoleAssignment.project_id.is_(None)
            )
        ).first()
        
        if not assignment:
            return False
        
        if assignment.expires_at and assignment.expires_at < datetime.utcnow():
            return False
        
        return True


def require_permission(*permission_keys, require_all=False):
    """
    Decorator to require permission(s) for a route
    
    Usage:
        @require_permission('dogs.view')
        def view_dogs():
            ...
        
        @require_permission('dogs.edit', 'dogs.delete', require_all=True)
        def manage_dogs():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('يجب تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
                return redirect(url_for('auth.login'))
            
            project_id = kwargs.get('project_id') or request.args.get('project_id')
            
            if require_all:
                has_access = PermissionService.has_all_permissions(
                    current_user.id, permission_keys, project_id
                )
            else:
                has_access = PermissionService.has_any_permission(
                    current_user.id, permission_keys, project_id
                )
            
            if not has_access:
                flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('يجب تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
            return redirect(url_for('auth.login'))
        
        if not PermissionService.is_admin(current_user.id):
            flash('هذه الصفحة للمشرفين فقط', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def require_role(*role_names, require_all=False):
    """
    Decorator to require specific role(s)
    
    Usage:
        @require_role(RoleType.PROJECT_MANAGER)
        def pm_dashboard():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('يجب تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
                return redirect(url_for('auth.login'))
            
            project_id = kwargs.get('project_id') or request.args.get('project_id')
            
            if require_all:
                has_access = all(
                    PermissionService.has_role(current_user.id, role, project_id)
                    for role in role_names
                )
            else:
                has_access = any(
                    PermissionService.has_role(current_user.id, role, project_id)
                    for role in role_names
                )
            
            if not has_access:
                flash('ليس لديك الدور المطلوب للوصول إلى هذه الصفحة', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def init_permission_context_processor(app):
    """
    Register template context processor for permission checking
    """
    @app.context_processor
    def inject_permission_helpers():
        def can(permission_key, project_id=None):
            """Check if current user has a permission"""
            if not current_user.is_authenticated:
                return False
            return PermissionService.has_permission(current_user.id, permission_key, project_id)
        
        def can_any(*permission_keys, project_id=None):
            """Check if current user has any of the permissions"""
            if not current_user.is_authenticated:
                return False
            return PermissionService.has_any_permission(current_user.id, list(permission_keys), project_id)
        
        def can_all(*permission_keys, project_id=None):
            """Check if current user has all permissions"""
            if not current_user.is_authenticated:
                return False
            return PermissionService.has_all_permissions(current_user.id, list(permission_keys), project_id)
        
        def is_admin():
            """Check if current user is an admin"""
            if not current_user.is_authenticated:
                return False
            return PermissionService.is_admin(current_user.id)
        
        def has_role(role_name, project_id=None):
            """Check if current user has a specific role"""
            if not current_user.is_authenticated:
                return False
            return PermissionService.has_role(current_user.id, role_name, project_id)
        
        return {
            'can': can,
            'can_any': can_any,
            'can_all': can_all,
            'is_admin': is_admin,
            'has_role': has_role,
            'PermissionKey': PermissionKey,
            'RoleType': RoleType
        }
    
    return app


def seed_default_roles():
    """Create default system roles"""
    default_roles = [
        (RoleType.SUPER_ADMIN, "المشرف الأعلى", "صلاحيات كاملة على النظام"),
        (RoleType.GENERAL_ADMIN, "المشرف العام", "إدارة كاملة للنظام"),
        (RoleType.PROJECT_MANAGER, "مسؤول المشروع", "إدارة مشروع معين"),
        (RoleType.HANDLER, "سائس", "العمليات اليومية للكلاب"),
        (RoleType.VETERINARIAN, "طبيب بيطري", "السجلات الطبية"),
        (RoleType.TRAINER, "مدرب", "التدريب"),
        (RoleType.BREEDER, "مربي", "التربية والإنتاج"),
        (RoleType.VIEWER, "مشاهد", "عرض فقط"),
    ]
    
    for name, name_ar, description in default_roles:
        existing = Role.query.filter_by(name=name).first()
        if not existing:
            role = Role(
                name=name,
                name_ar=name_ar,
                description=description,
                is_system=True,
                is_active=True
            )
            db.session.add(role)
    
    db.session.commit()
