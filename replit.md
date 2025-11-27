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
- **Multi-Cloud Backup System**: Advanced cloud backup integration with Google Drive and Dropbox support, featuring secure OAuth 2.0 authentication with CSRF state validation, storage quota monitoring, distributed backup capabilities, refresh token preservation, and unified BackupManager coordinating multiple cloud providers.

### Feature Specifications
- **Core Management**: Tracks K9 lifecycle, employee information, training records, veterinary care, and breeding production.
- **Project Operations**: Manages project lifecycle, resource allocation, incident logging, performance evaluations, and project locations.
- **Attendance System**: Comprehensive tracking with shift management, scheduling, project-specific recording, and Arabic RTL PDF export, using an advanced Unified Matrix Attendance System.
- **Ultra-Granular Permission System**: Provides `GENERAL_ADMIN` users with fine-grained control over user access at a subsection level, featuring 79 distinct permission combinations, audit logging, and an intuitive admin dashboard. Migrated from role-based to permission-first access control with roles acting as permission templates.
- **Comprehensive Permissions UI**: A three-step workflow (Select Project → Select User → Manage Permissions) for `GENERAL_ADMIN` users to manage permissions, with full metadata registry and real-time toggling.
- **Excel Export System**: Comprehensive XLSX export functionality for reports with Arabic RTL support.
- **Modern Reporting Hub**: Centralized dashboard with dynamic statistics, categorized report organization, and integrated chart visualization.
- **Handler Daily System**: Comprehensive daily operations management for K9 handlers including schedule creation, two-tier reporting (Shift and Daily Reports), and a modern notification system.
- **Report Export System**: Unified Minimal Elegant PDF design for all report types (Handler, Shift, PM Daily, Veterinary) with Arabic RTL support, clean typography (Tajawal/Cairo fonts), calm color palette (#3A6EA5 blue, #333333 gray), and consistent table styling.
- **PM Report Review Workflow**: A 2-tier review process for project-based reports with statuses, audit trails, and notifications.
- **Admin Final Approval System**: Two-tier approval workflow (Project Manager review, General Admin final approval/rejection) for all report types, with dual notifications and audit logging.
- **Account Management System**: Streamlined system access control for employees, linking employee records to user accounts, auto-role mapping, and secure password management.
- **Project Manager Dashboard**: Workflow-focused interface for the `PROJECT_MANAGER` role, providing a project overview, pending approvals, team status, and project-scoped data views.
- **Employee Document Management System**: Comprehensive document attachment system for employee records with categorized document types and secure file storage.
- **Employee Geolocation Feature**: Automatic browser-based geolocation capture for employee residence with database storage and Google Maps link generation.
- **Multi-Cloud Backup Integration**: Integrated cloud backup system supporting Google Drive and Dropbox with secure OAuth 2.0 authentication flow (CSRF state validation using Flow-generated state for Google Drive and cryptographically strong secrets.token_urlsafe for Dropbox), storage quota visualization, distributed backup across multiple providers, refresh token preservation to prevent authentication failures, and secure token management in UserCloudIntegration table.
  - **OAuth Setup Requirements**: Requires environment secrets GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, DROPBOX_APP_KEY, DROPBOX_APP_SECRET. OAuth redirect URIs must be configured in respective provider consoles pointing to application callback URLs.

### System Design Choices
- **Client/Server Separation**: Clear distinction between frontend and backend.
- **Data Integrity**: Uses Enum-based status management.
- **Secure Identification**: UUID fields for object identification.
- **Flexible Data Storage**: JSON fields for metadata and audit logs.
- **Performance**: Optimized with database connection pooling and file size limits.
- **Scalability**: Modular architecture and permission-based data isolation.
- **Employee vs User/Handler Architecture**: Distinct `Employee` table for general workforce management and `User` table with `HANDLER` role for system access and daily operations, with mandatory linking.
- **Unified Permission Decorators**: All access decorators consolidated in `k9/utils/permissions_new.py` with consistent admin_mode enforcement.
- **Navbar Access Control**: Template-level permission checking ensures users see only relevant navigation options.

### Production Readiness & Code Quality
- **Runtime Hygiene**: Complete removal of debug code including 50+ print statements from backend routes/services/APIs, 6 utility files converted to structured logging using `current_app.logger`, zero traceback debugging, and comprehensive error handling with proper logging levels.
- **Frontend Cleanup**: Removal of 138+ console.log statements from 158 HTML templates and 12 JavaScript files for production-ready client-side code.
- **Security Hardening**: 
  - CSRF protection with proper exemptions for GET API endpoints
  - File upload security with multi-layer defense: 2MB per-file limits, 16MB global MAX_CONTENT_LENGTH, allowed_file() validation, secure_filename() sanitization, and UUID-based naming
  - 162+ authorization decorators verified across all routes
  - Comprehensive permission checks throughout the application
- **Structured Logging**: All error handling uses Flask's current_app.logger with appropriate levels (DEBUG, INFO, WARNING, ERROR) instead of print statements for production monitoring.
- **Code Standards**: Clean, maintainable codebase ready for deployment with zero runtime errors, proper error handling, and production-grade security measures.
- **Unified PDF Design**: Minimal Elegant design system implemented across all PDF reports with `k9/utils/pdf_minimal_elegant.py` template providing consistent headers, typography, color scheme, and table styling for professional document generation.
- **Permissions System Verification (Nov 2025)**: 
  - Fixed `has_permission()` project_id filter logic to correctly check project-specific AND global permissions
  - Added comprehensive logging to permission update route for debugging
  - Verified complete permission lifecycle: save to DB → read from DB → check permissions → display in UI
  - All automated tests passing: save, read, verify, and display permissions work correctly
  - System reads permissions directly from database (no stale cache issues)
- **Permission-UI Connection Fix (Nov 22, 2025)**:
  - **Dashboard Routing**: Replaced hard-coded role checks with `get_sections_for_user()` - users with granted permissions now reach the correct dashboard regardless of role
  - **Route Handler Refactor**: Eliminated 8+ hard-coded role checks in `k9/routes/main.py` - all routes now use permission-aware helpers (`get_user_accessible_dogs`, `get_user_accessible_employees`, `get_user_assigned_projects`)
  - **Report Generation Fix**: PDF/Excel exports in `k9/utils/utils.py` now use permission-aware helpers instead of role-based filtering
  - **PM Scoping Critical Fix**: Updated `get_scoped_dogs` and `get_scoped_employees` in `k9/utils/pm_scoping.py` to support ALL three assignment methods: ProjectDog table (legacy), ProjectAssignment table (current), and assigned_to_user_id field (direct) - ensures complete data visibility for PROJECT_MANAGER users
  - **Template Permission Enforcement**: Removed all hard-coded role checks from UI templates - `unauthorized.html` now uses `is_admin()` and `get_sections_for_user()` for dashboard redirects; `handler/profile.html` displays role badge based on permissions instead of `current_user.role.value`; all navigation already uses `has_permission()` checks ensuring UI visibility matches granted permissions
  - **Impact**: Users with granted permissions can now access data and UI elements immediately upon permission assignment, without role restrictions bypassing the permission system. UI dynamically shows/hides features based solely on permissions - no permissions = minimal handler interface, partial permissions = only assigned features, full permissions = complete interface
- **New Permission System Rebuild (Nov 26-27, 2025)**:
  - **Architecture**: Complete rebuild from ground up replacing legacy SubPermission system with session-cached Permission/UserPermission system
  - **Permission Model**: 89 granular permission keys across 23 categories (admin, users, dogs, projects, assignments, shifts, attendance, training, veterinary, breeding, reports, schedules, supervisor, handler, caretaker, security, audit, notifications, dashboard, cleaning, feeding, health, deworming)
  - **Session Caching**: Permissions loaded into session on login for fast permission checks; GENERAL_ADMIN users in admin mode bypass permission checks entirely
  - **Unified Decorators**: `require_permission` and `require_admin_permission` in `k9/utils/permissions_new.py` with AJAX-aware responses (JSON for fetch, redirect for browser)
  - **Bilingual Support**: Arabic (name_ar) and English (name_en) permission names stored in Permission model
  - **Admin UI**: New permission management interface at `/admin/permissions-new` with user list, permission catalog grouped by category, toggle switches for grant/revoke, bulk category operations, and real-time stats
  - **Audit Trail**: PermissionChangeLog model tracks all permission grants/revokes with timestamps, actor, and IP address
  - **Legacy Cleanup (Nov 27, 2025)**: Removed deprecated files (permission_utils.py, permission_decorators.py, permission_registry.py, default_permissions.py); migrated all imports to permissions_new.py; updated admin_routes.py, main.py, utils.py, api_routes.py to use new models (Permission, UserPermission, PermissionChangeLog)
  - **Key Files**: `k9/utils/permissions_new.py` (core logic, decorators, helper functions), `k9/models/permissions_new.py` (models), `scripts/seed_permissions.py` (seeds 89 permissions), `k9/templates/admin/permissions_new.html` (admin UI)

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