# K9 Operations Management System

## Overview
This project is a comprehensive, web-based, and mobile-first K9 operations management system designed for military and police canine units, featuring Arabic RTL compatibility. Its core purpose is to manage the entire lifecycle of K9s, including employee supervision, project management, training, veterinary care, breeding, and operational missions. The system aims to streamline operations, enhance efficiency, and provide robust tracking and reporting for critical canine unit functions, supporting optimized K9 deployment and resource utilization.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
- **UI Framework**: Bootstrap 5 RTL for comprehensive UI components with right-to-left language support.
- **Styling**: Custom CSS optimized for RTL layouts and comprehensive dark mode support with toggle.
- **Fonts**: Google Fonts, specifically Noto Sans Arabic, for appropriate Arabic text rendering.
- **Responsiveness**: Mobile-first design approach ensuring full responsiveness across all device types.
- **Unified Header Design**: Modern gradient hero headers with quick navigation bars across all user roles (Admin, PM, Handler), featuring animated buttons, user dropdowns, and consistent design language.

### Technical Implementations
- **Backend Framework**: Flask (Python) utilizing a modular Blueprint structure.
- **Database**: PostgreSQL, integrated via SQLAlchemy ORM.
- **Authentication**: Flask-Login implements session-based authentication and a permission-first access control system, including a dual-mode `GENERAL_ADMIN` system for flexible access.
- **Database Migrations**: Flask-Migrate, powered by Alembic, for schema versioning and management.
- **File Handling**: Local file system storage for uploads.
- **Security**: Incorporates CSRF protection, configurable session timeouts, input validation, audit logging, and a strict permission-based access control with consolidated decorators.
- **Database Backup & Restore**: Comprehensive backup/restore functionality using pg_dump/psql, automated scheduling via APScheduler, configurable retention, and an admin dashboard for management.
- **Multi-Cloud Backup System**: Advanced cloud backup integration with Google Drive and Dropbox support, featuring secure OAuth 2.0 authentication, storage quota monitoring, distributed backup capabilities, and refresh token preservation.

### Feature Specifications
- **Core Management**: Tracks K9 lifecycle, employee information, training records, veterinary care, and breeding production.
- **Project Operations**: Manages project lifecycle, resource allocation, incident logging, performance evaluations, and project locations.
- **Attendance System**: Comprehensive tracking with shift management, scheduling, project-specific recording, and Arabic RTL PDF export, using an advanced Unified Matrix Attendance System.
- **V2 Role-Based Permission System**: Modern role-based access control with ~50 organized permissions grouped by module. Features 6 predefined roles (super_admin, general_admin, project_manager, handler, veterinarian, trainer, breeder), wildcard permission matching (e.g., `admin.*`), permission overrides, and audit logging. Legacy admin_mode bypass preserved for GENERAL_ADMIN flexibility.
- **Excel Export System**: Comprehensive XLSX export functionality for reports with Arabic RTL support.
- **Modern Reporting Hub**: Centralized dashboard with dynamic statistics, categorized report organization, and integrated chart visualization.
- **Handler Daily System**: Comprehensive daily operations management for K9 handlers including schedule creation, two-tier reporting (Shift and Daily Reports), and a modern notification system.
- **Report Export System**: Unified Minimal Elegant PDF design for all report types (Handler, Shift, PM Daily, Veterinary) with Arabic RTL support and consistent styling.
- **PM Report Review Workflow**: A 2-tier review process for project-based reports with statuses, audit trails, and notifications.
- **Admin Final Approval System**: Two-tier approval workflow (Project Manager review, General Admin final approval/rejection) for all report types, with dual notifications and audit logging.
- **Account Management System**: Streamlined system access control for employees, linking employee records to user accounts, auto-role mapping, and secure password management.
- **Project Manager Dashboard**: Workflow-focused interface for the `PROJECT_MANAGER` role, providing a project overview, pending approvals, team status, and project-scoped data views.
- **Employee Document Management System**: Comprehensive document attachment system for employee records with categorized document types and secure file storage.
- **Employee Geolocation Feature**: Automatic browser-based geolocation capture for employee residence with database storage and Google Maps link generation.

### System Design Choices
- **Client/Server Separation**: Clear distinction between frontend and backend.
- **Data Integrity**: Uses Enum-based status management.
- **Secure Identification**: UUID fields for object identification.
- **Flexible Data Storage**: JSON fields for metadata and audit logs.
- **Performance**: Optimized with database connection pooling and file size limits.
- **Scalability**: Modular architecture and permission-based data isolation.
- **Employee vs User/Handler Architecture**: Distinct `Employee` table for general workforce management and `User` table with `HANDLER` role for system access and daily operations, with mandatory linking.
- **Unified Permission Decorators**: All access decorators consolidated with consistent admin_mode enforcement.
- **Navbar Access Control**: Template-level permission checking ensures users see only relevant navigation options.
- **Production Readiness**: Complete removal of debug code, comprehensive error handling with structured logging, and robust security hardening including CSRF protection and file upload security.
- **Unified PDF Design**: Minimal Elegant design system implemented across all PDF reports for consistent professional document generation.

## Recent Maintenance (2026-01-13)
- **V2 Permission System Complete Migration**: Full decoupling from V1 flat permission tables.
  - **V1 Interface Wrapper Updated**: `k9/utils/permissions_new.py` now fully delegates to V2 PermissionService
    - `load_user_permissions()` - Uses PermissionService.get_user_permissions()
    - `get_user_permissions()` - Falls back to PermissionService if session empty
    - `get_sections_for_user()` - Uses PermissionService directly
    - `grant_permission()` - Calls PermissionService.grant_permission() (uses PermissionOverride)
    - `revoke_permission()` - Calls PermissionService.revoke_permission() (uses PermissionOverride)
    - `batch_grant_permissions()` / `batch_revoke_permissions()` - Use V2 PermissionService
  - **Admin Routes V2 Migration**:
    - Dashboard stats use V2 Role/UserRoleAssignment counts
    - Audit logs use V2 PermissionAuditLog
    - Template assignment maps to V2 roles (8 templates: full_access, pm_access, view_only, handler_access, security_access, vet_access, breeding_manager, trainer_access)
    - Added PermissionService.clear_user_roles() and clear_user_overrides() methods
  - **V1 Scripts Removed**: 9 obsolete V1 seed scripts deleted from scripts/ directory
  - **V1 Tables Deprecated**: UserPermission/Permission tables no longer source of truth
  - **V2 is Single Source of Truth**: All permission data flows through V2 Role/PermissionOverride tables

## Recent Maintenance (2026-01-10)
- **V2 Permission System Finalization**: Complete integration of role-based permission system across all components.
  - **Admin UI for Role Management**: Added `/admin/roles` and `/admin/roles/users` for managing V2 roles
    - Role listing with permission display
    - Interactive role assignment/revocation for users
    - AJAX-based operations with CSRF protection
  - **User Permissions Dashboard**: Updated `/my-permissions` to display V2 roles and wildcard permissions
    - Shows user's assigned roles with Arabic names
    - Displays permission patterns with wildcard badges
    - Quick access links based on V2 permissions
  - **Template Integration**: All templates use V2 context processor functions
    - `has_permission()`, `can()`, `can_any()`, `can_all()`, `is_admin()`, `has_role()`
    - Removed legacy `get_user_permissions()` calls from base templates
  - **Key Routes Added**:
    - `GET /admin/roles` - List all V2 roles
    - `GET /admin/roles/users` - User role management interface
    - `POST /admin/roles/assign` - Assign role to user
    - `POST /admin/roles/revoke` - Revoke role from user
    - `GET /admin/roles/user/<id>` - Get user's V2 roles (API)

## Recent Maintenance (2026-01-09)
- **V2 Permission System Implementation**: Complete rebuild of the permission system from flat 385-key structure to role-based architecture.
  - **New Models**: `Role`, `UserRoleAssignment`, `PermissionOverride`, `PermissionAuditLog` in `k9/models/permissions_v2.py`
  - **PermissionService**: Unified permission service with caching and wildcard support in `k9/services/permission_service.py`
  - **Role-Based Access**: 7 predefined roles (super_admin, general_admin, project_manager, handler, veterinarian, trainer, breeder, viewer)
  - **~50 Organized Permissions**: Grouped by module (dogs.*, employees.*, projects.*, reports.*, etc.)
  - **Wildcard Support**: Pattern matching for permissions (e.g., `admin.*` grants all admin permissions)
  - **Template Helpers**: Context processor provides `can()`, `can_any()`, `can_all()`, `is_admin()`, `has_role()` functions
  - **Legacy Compatibility**: Updated decorators delegate to V2 while preserving admin_mode bypass for GENERAL_ADMIN users
  - **Auto Migration**: All existing users automatically migrated to V2 role assignments on startup
  - **Key Files**: 
    - Models: `k9/models/permissions_v2.py`
    - Service: `k9/services/permission_service.py`
    - Migration: `k9/utils/permissions_v2_migration.py`
    - Decorators: `k9/utils/permissions_new.py` (updated to use V2)

## Recent Maintenance (2025-12-02)
- **Automatic Permission Seeding**: Implemented automatic permission seeding on every app startup.
  - Created `k9/utils/permission_seeder.py` - reusable seeding module
  - Permissions are auto-seeded during `app.app_context()` initialization
  - Idempotent design: safe to run on every startup (no duplicates)
  - Reads from `permissions_map.json` plus additional permissions list
  - Total permissions: 302 across 29 categories
  - **Permissions will NEVER be empty** - they are seeded before any other initialization

## Recent Maintenance (2025-12-01)
- **Permission System Complete Overhaul**: Fixed critical permission key format mismatch where database stored verbose keys but code checked simple keys.
  - Added 83 missing permissions (45 from decorators + 38 from template checks)
  - All 164 code-referenced permission keys now exist in database
  - Categories: account, admin, api, assignments, audit, auth, backup, breeding, cleaning, dashboard, deworming, dictionaries, dogs, employees, evaluations, excretion, general, grooming, handlers, home, incidents, locations, mfa, notifications, password_reset, pm, production, projects, reports, schedule, search, settings, shifts, supervisor, suspicions, tasks, training, users, veterinary

## Recent Maintenance (2025-11-30)
- **Template Cleanup**: Removed 15 deprecated/orphaned templates that were replaced by modern versions:
  - Admin: `admin_panel.html`, `permission_management.html` (replaced by new dashboard and permission system)
  - Training: `add.html`, `list.html` (merged into breeding training activity)
  - Projects: `list.html`, `dashboard.html`, `assignment_add.html`, `dog_add.html`, `sections_overview.html` (replaced by modern_list and modern_dashboard)
  - Production: `list.html` (unused legacy)
  - Reports: `trainer_daily.html`, `veterinary/daily.html`, breeding daily/weekly variants (replaced by unified report system)

## External Dependencies

### Python Packages
- **Flask Ecosystem**: Flask, Flask-SQLAlchemy, Flask-Login, Flask-Migrate.
- **Security**: Werkzeug.
- **Database**: psycopg2-binary.
- **PDF Generation**: ReportLab.
- **Excel Export**: openpyxl.
- **Scheduling**: APScheduler.
- **Google API**: google-api-python-client.

### Frontend Dependencies
- **UI Framework**: Bootstrap 5 RTL.
- **Icon Library**: Font Awesome 6.
- **Fonts**: Google Fonts (Noto Sans Arabic).
- **Charting**: Chart.js.

### Database Requirements
- **Primary Database**: PostgreSQL.
- **UUID Compatibility**: Native UUID support for PostgreSQL.
- **Connection Pooling**: Configured for production PostgreSQL.
- **Migration Support**: Flask-Migrate with Alembic.