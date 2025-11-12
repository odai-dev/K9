# K9 Operations Management System

## Overview
This project is a comprehensive, web-based, and mobile-first K9 operations management system designed for military and police canine units, featuring Arabic RTL compatibility. Its core purpose is to manage the entire lifecycle of K9s, including employee supervision, project management, training, veterinary care, breeding, and operational missions. The system aims to streamline operations, enhance efficiency, and provide robust tracking and reporting for critical canine unit functions, supporting optimized K9 deployment and resource utilization.

## User Preferences
Preferred communication style: Simple, everyday language.

## Recent Updates (November 12, 2025)

### Legacy System Cleanup
- **Project Attendance Removal**: Removed legacy project_attendance link from projects list page (`k9/templates/projects/modern_list.html`)
  - System now exclusively uses the modern DailySchedule workflow for handler and dog scheduling
  - Legacy project attendance routes remain in codebase but are no longer accessible via UI
  
### Permission System Updates
- **Attendance Permission Descriptions**: Updated permission descriptions in `k9/utils/permission_utils.py` to reflect DailySchedule terminology
  - Permission keys remain as "attendance.*" for backward compatibility
  - Descriptions now reference "daily schedules" instead of legacy attendance tracking
  - Changes: "View daily schedules and attendance", "Create and record daily schedules", "Edit daily schedules", "Access daily schedule reports"

### Security Fixes
- **Critical Security Fix**: Removed incorrect admin access grant for PROJECT_MANAGER role
  - Fixed `_is_admin_mode()` in `k9/utils/permission_utils.py` 
  - Fixed `is_admin()` in `k9/utils/pm_scoping.py`
  - PROJECT_MANAGER users now properly restricted to granular permissions only
  - ONLY GENERAL_ADMIN in general admin mode has full administrative access
- **Known Issue**: The `admin_or_pm_required` decorator (~105 usages) still allows PROJECT_MANAGER unrestricted access to certain routes. This requires a comprehensive audit and migration to project-scoped decorators in a future update.

## System Architecture

### UI/UX Decisions
- **UI Framework**: Bootstrap 5 RTL for comprehensive UI components with right-to-left language support.
- **Styling**: Custom CSS optimized for RTL layouts and comprehensive dark mode support with toggle.
- **Fonts**: Google Fonts, specifically Noto Sans Arabic, for appropriate Arabic text rendering.
- **Responsiveness**: Mobile-first design approach ensuring full responsiveness across all device types.

### Technical Implementations
- **Backend Framework**: Flask (Python) utilizing a modular Blueprint structure.
- **Database**: PostgreSQL, integrated via SQLAlchemy ORM.
- **Authentication**: Flask-Login implements session-based authentication and strict role-based access control with `GENERAL_ADMIN`, `PROJECT_MANAGER`, `HANDLER`, `TRAINER`, `BREEDER`, and `VET` tiers. Includes a dual-mode `GENERAL_ADMIN` system for flexible access with enforced mode switching (GENERAL_ADMIN users in PM mode cannot access admin-only routes).
- **Database Migrations**: Flask-Migrate, powered by Alembic, for schema versioning and management.
- **File Handling**: Local file system storage for uploads.
- **Security**: Incorporates CSRF protection, configurable session timeouts, input validation, audit logging, and strict Role-Based Access Control with consolidated permission decorators. All decorators enforce admin_mode checking to prevent privilege escalation.
- **Database Backup & Restore**: Comprehensive backup/restore functionality using pg_dump/psql, automated scheduling via APScheduler, configurable retention, and an admin dashboard for management.

### Feature Specifications
- **Core Management**: Tracks K9 lifecycle, employee information, training records, veterinary care, and breeding production.
- **Project Operations**: Manages project lifecycle, resource allocation, incident logging, and performance evaluations. Includes full project editing capabilities with integrated location management system allowing multiple locations per project with add/edit/delete operations.
- **Attendance System**: Comprehensive tracking with shift management, scheduling, project-specific recording, and Arabic RTL PDF export. Includes an advanced Unified Matrix Attendance System.
- **Ultra-Granular Permission System**: Provides `GENERAL_ADMIN` users with control over `PROJECT_MANAGER` access at a subsection level, featuring 79 distinct permission combinations, audit logging, and an intuitive admin dashboard.
- **Excel Export System**: Comprehensive XLSX export functionality for reports with Arabic RTL support.
- **Modern Reporting Hub**: Centralized dashboard with dynamic statistics, categorized report organization, and integrated chart visualization.
- **Data Visualization Framework**: Chart.js integration with custom RTL-aware utilities.
- **Handler Daily System**: Comprehensive daily operations management for K9 handlers including schedule creation, two-tier reporting (Shift and Daily Reports), duplicate prevention, smart pre-population, visual indicators, and a modern notification system. Schedule locking system uses unified `status` field (OPEN/LOCKED) with optional `locked_at` timestamp for audit purposes.
- **Report Export System**: PDF and Excel export functionality for HandlerReport and ShiftReport with Arabic RTL support, role-based access control (PROJECT_MANAGER and GENERAL_ADMIN only), and automatic formatting using ReportLab and openpyxl libraries.
- **PM Report Review Workflow**: A 2-tier review process for project-based reports (HandlerReport, VeterinaryVisit, BreedingTrainingActivity, CaretakerDailyLog) with statuses, audit trails, and notifications.
- **Admin Final Approval System**: Two-tier approval workflow where Project Managers review and forward reports (SUBMITTED → FORWARDED_TO_ADMIN), followed by General Admin final approval/rejection (FORWARDED_TO_ADMIN → APPROVED_BY_ADMIN/REJECTED_BY_ADMIN). Dual notifications ensure both submitter and responsible PM receive admin decisions. Supports all report types (HANDLER, TRAINER, VET, CARETAKER) with unified interface and audit logging via ReportReview table.
- **Account Management System**: Streamlined system access control for employees, linking employee records to user accounts, auto-role mapping, and secure password management.
- **Project Manager Dashboard**: Workflow-focused interface for the `PROJECT_MANAGER` role, providing a project overview, pending approvals, team status, and project-scoped data views. Features a dedicated PM navigation bar with streamlined access to Dogs, Team, Approvals, Veterinary, Breeding, Production, and Administration modules (task assignment, handler reports, schedules, notifications).
- **Employee Document Management System**: Comprehensive document attachment system for employee records with categorized document types, secure file storage, and user interface for management.
- **Employee Geolocation Feature**: Automatic browser-based geolocation capture for employee residence with database storage and Google Maps link generation.

### System Design Choices
- **Client/Server Separation**: Clear distinction between frontend and backend.
- **Data Integrity**: Uses Enum-based status management.
- **Secure Identification**: UUID fields for object identification.
- **Flexible Data Storage**: JSON fields for metadata and audit logs.
- **Performance**: Optimized with database connection pooling and file size limits.
- **Scalability**: Modular architecture and role-based data isolation.
- **Employee vs User/Handler Architecture**: Distinct `Employee` table for general workforce management and `User` table with `HANDLER` role for system access and daily operations, with **mandatory** linking. All system users must be linked to employee records for enhanced security and data integrity.
- **User-Employee Enforcement**: Required `employee_id` foreign key in User model ensures all users have linked employee records. Includes validation at model level and login security checks.
- **Unified Permission Decorators**: All role-based access decorators consolidated in `k9/utils/permission_decorators.py` with consistent admin_mode enforcement to prevent security bypasses.
- **Navbar Access Control**: Template-level role checking ensures PROJECT_MANAGER users see only PM-specific navbar, GENERAL_ADMIN users see admin navbar only when in general_admin mode.

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