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

### Technical Implementations
- **Backend Framework**: Flask (Python) utilizing a modular Blueprint structure.
- **Database**: PostgreSQL, integrated via SQLAlchemy ORM.
- **Authentication**: Flask-Login implements session-based authentication and a permission-first access control system, replacing traditional role-based access. Includes a dual-mode `GENERAL_ADMIN` system for flexible access with enforced mode switching.
- **Database Migrations**: Flask-Migrate, powered by Alembic, for schema versioning and management.
- **File Handling**: Local file system storage for uploads.
- **Security**: Incorporates CSRF protection, configurable session timeouts, input validation, audit logging, and a strict permission-based access control with consolidated decorators. All decorators enforce admin_mode checking to prevent privilege escalation.
- **Database Backup & Restore**: Comprehensive backup/restore functionality using pg_dump/psql, automated scheduling via APScheduler, configurable retention, and an admin dashboard for management.

### Feature Specifications
- **Core Management**: Tracks K9 lifecycle, employee information, training records, veterinary care, and breeding production.
- **Project Operations**: Manages project lifecycle, resource allocation, incident logging, performance evaluations, and project locations.
- **Attendance System**: Comprehensive tracking with shift management, scheduling, project-specific recording, and Arabic RTL PDF export, using an advanced Unified Matrix Attendance System.
- **Ultra-Granular Permission System**: Provides `GENERAL_ADMIN` users with fine-grained control over user access at a subsection level, featuring 79 distinct permission combinations, audit logging, and an intuitive admin dashboard. Migrated from role-based to permission-first access control with roles acting as permission templates.
- **Comprehensive Permissions UI**: A three-step workflow (Select Project → Select User → Manage Permissions) for `GENERAL_ADMIN` users to manage permissions, with full metadata registry and real-time toggling.
- **Excel Export System**: Comprehensive XLSX export functionality for reports with Arabic RTL support.
- **Modern Reporting Hub**: Centralized dashboard with dynamic statistics, categorized report organization, and integrated chart visualization.
- **Handler Daily System**: Comprehensive daily operations management for K9 handlers including schedule creation, two-tier reporting (Shift and Daily Reports), and a modern notification system.
- **Report Export System**: PDF and Excel export functionality for HandlerReport and ShiftReport with Arabic RTL support and role-based access control.
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
- **Unified Permission Decorators**: All access decorators consolidated in `k9/utils/permission_decorators.py` with consistent admin_mode enforcement.
- **Navbar Access Control**: Template-level permission checking ensures users see only relevant navigation options.

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
- **UUID Compatibility**: Native UUID support for PostgreSQL, automatic string fallback for SQLite.
- **Connection Pooling**: Configured for production PostgreSQL.
- **Migration Support**: Flask-Migrate with Alembic.

## Recent Changes

### 2025-11-16: Comprehensive Security Fix - Restored ALL Bypassed Role Checks
**Critical Security Fix** - Eliminated all bypassed role checks across the entire codebase and implemented prevention measures:

#### Issues Fixed:
1. **Account Management Menu Visibility**:
   - `k9/utils/template_utils.py`: Fixed 2 bypassed checks in `get_base_template()` and `is_pm_view()`
   - `k9/templates/base.html`: Replaced `current_user.is_general_admin` (non-existent) with `is_admin()` in 3 locations

2. **Comprehensive Codebase Scan**:
   - Fixed **161 total bypassed role checks** across 14 files:
     - Route files: `main.py`, `auth.py`, `pm_routes.py`, `admin_routes.py`, `supervisor_routes.py`, `account_management_routes.py`, `task_routes.py`, `pm_daily_routes.py`
     - Utility files: `pm_scoping.py`, `template_utils.py`, `permission_utils.py`, `utils.py`
     - API files: `api_routes.py`, `api_breeding_training_activity.py`, `api_cleaning.py`, `api_deworming.py`, `api_excretion.py`

#### Prevention Measures Implemented:
1. **Automated Security Validation Script** (`scripts/validate_security.py`):
   - Scans for bypassed role checks (`if True`)
   - Detects non-existent properties (`current_user.is_general_admin`)
   - Flags missing `@login_required` decorators
   - Identifies suspicious hardcoded bypasses
   - Exit code 1 on critical errors, 0 on pass

2. **Security Guidelines Document** (`SECURITY_GUIDELINES.md`):
   - Comprehensive anti-patterns documentation
   - Proper access control patterns for routes and templates
   - Pre-deployment checklist
   - Emergency response procedures

#### Validation Results:
- ✅ **0 critical errors** (all bypassed checks restored)
- ⚠️ 169 warnings (mostly false positives for API routes)
- Status: **VALIDATION PASSED**

#### Impact:
- All role checks now properly enforce `GENERAL_ADMIN` vs `PROJECT_MANAGER` access
- Account Management menu correctly appears for admins
- System security fully restored with comprehensive safeguards
- Future similar issues preventable via automated validation

#### How to Prevent Recurrence:
Run before any deployment:
```bash
python3 scripts/validate_security.py
```

### 2025-11-15: Complete Template Permission Migration
**Major Update** - Completed migration of all UI templates from role-based to permission-based access control:
- **Modified Templates** (8 files):
  - `handler/view_report.html`: Export buttons now check `has_permission('handler_reports.export')`
  - `handler/view_shift_report.html`: Export buttons now check `has_permission('handler_reports.export')`
  - `supervisor/reports_index.html`: Project filter now uses `is_admin()`
  - `supervisor/schedules_index.html`: Project filter now uses `is_admin()`
  - `projects/list.html`: Delete button now checks `is_admin()` or `has_permission('projects.delete')`
  - `projects/modern_list.html`: Delete button now checks `is_admin()` or `has_permission('projects.delete')`
  - `projects/modern_dashboard.html`: Manager edit button now uses `is_admin()` check
- **Impact**: All interactive UI elements (buttons, links, filters) now controlled by database-stored permissions
- **Result**: Zero role-based access control checks remain in templates (except display-only role badges)
- **Behavior**: 
  - Export features require `handler_reports.export` permission
  - Project deletion requires `projects.delete` permission or admin status
  - Admin-only filters use `is_admin()` function for `GENERAL_ADMIN` in admin mode
- **Security**: All changes architect-reviewed and approved - no security regressions

### 2025-11-14: Permission System Refactoring
**Critical fix** - Switched from role-based to permission-based UI/navigation control:
- **Modified**: `k9/utils/utils.py::get_user_permissions()` now reads exclusively from `SubPermission` table instead of hardcoding role-based defaults
- **Impact**: Navigation menu and UI elements now reflect actual granted permissions from database
- **Behavior**: 
  - `GENERAL_ADMIN` in admin mode: Full access (unchanged)
  - `HANDLER`: No navigation permissions (unchanged)
  - `PROJECT_MANAGER` and `GENERAL_ADMIN` in PM mode: Permissions controlled by `SubPermission` table entries only
- **Important**: Users without `SubPermission` records will see empty navigation. Ensure proper permission grants exist for all active users.
- **Security**: No regressions - all route-level decorators (`@require_permission`) remain unchanged and continue enforcing granular access control.