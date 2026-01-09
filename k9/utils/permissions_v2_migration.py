"""
Migration script for Permissions V2
====================================
Migrates existing users from old permission system to new role-based system
"""
from app import db
from k9.models.models import User, UserRole
from k9.models.permissions_v2 import Role, UserRoleAssignment, RoleType
from k9.services.permission_service import seed_default_roles
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def get_role_for_user_role(user_role: UserRole) -> str:
    """Map old UserRole enum to new RoleType"""
    mapping = {
        UserRole.GENERAL_ADMIN: RoleType.GENERAL_ADMIN,
        UserRole.PROJECT_MANAGER: RoleType.PROJECT_MANAGER,
        UserRole.HANDLER: RoleType.HANDLER,
        UserRole.TRAINER: RoleType.TRAINER,
        UserRole.BREEDER: RoleType.BREEDER,
        UserRole.VET: RoleType.VETERINARIAN,
    }
    return mapping.get(user_role, RoleType.VIEWER)


def migrate_users_to_v2():
    """
    Migrate all existing users to the new permission system
    """
    seed_default_roles()
    
    users = User.query.filter_by(active=True).all()
    migrated = 0
    skipped = 0
    
    for user in users:
        role_name = get_role_for_user_role(user.role)
        
        role = Role.query.filter_by(name=role_name, is_active=True).first()
        if not role:
            logger.warning(f"Role {role_name} not found for user {user.username}")
            skipped += 1
            continue
        
        existing = UserRoleAssignment.query.filter_by(
            user_id=user.id,
            role_id=role.id,
            project_id=None
        ).first()
        
        if existing:
            logger.info(f"User {user.username} already has role {role_name}")
            skipped += 1
            continue
        
        if user.role == UserRole.PROJECT_MANAGER and user.project_id:
            pm_role = Role.query.filter_by(name=RoleType.PROJECT_MANAGER, is_active=True).first()
            if pm_role:
                assignment = UserRoleAssignment(
                    user_id=user.id,
                    role_id=pm_role.id,
                    project_id=user.project_id,
                    is_active=True
                )
                db.session.add(assignment)
        else:
            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                project_id=None,
                is_active=True
            )
            db.session.add(assignment)
        
        migrated += 1
        logger.info(f"Migrated user {user.username} to role {role_name}")
    
    db.session.commit()
    
    logger.info(f"Migration complete: {migrated} users migrated, {skipped} skipped")
    return migrated, skipped


def check_migration_status():
    """Check if migration has been completed"""
    roles_count = Role.query.filter_by(is_system=True).count()
    assignments_count = UserRoleAssignment.query.count()
    
    return {
        'roles_seeded': roles_count >= 7,
        'roles_count': roles_count,
        'assignments_count': assignments_count,
        'needs_migration': assignments_count == 0 and User.query.filter_by(active=True).count() > 0
    }


def run_migration_if_needed():
    """Run migration only if needed"""
    status = check_migration_status()
    
    if not status['roles_seeded']:
        logger.info("Seeding default roles...")
        seed_default_roles()
    
    if status['needs_migration']:
        logger.info("Running user migration...")
        migrate_users_to_v2()
    else:
        logger.info("Migration not needed or already complete")
    
    return status
