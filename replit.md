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
- **Authentication**: Flask-Login implements session-based authentication and role-based access control with `GENERAL_ADMIN`, `PROJECT_MANAGER`, and `HANDLER` tiers.
- **Database Migrations**: Flask-Migrate, powered by Alembic, for schema versioning and management.
- **File Handling**: Local file system storage for uploads.
- **Security**: Incorporates CSRF protection, configurable session timeouts, input validation, and audit logging. **Role-Based Access Control** enforces strict route protection with decorators (`@admin_or_pm_required`, `@handler_required`, `@admin_required`) ensuring HANDLER users can only access `/handler/*` routes and are automatically redirected from admin/PM interfaces.
- **Database Backup & Restore**: Comprehensive backup/restore functionality using pg_dump/psql, automated scheduling via APScheduler, configurable retention, and an admin dashboard for management.

### Feature Specifications
- **Core Management**: Tracks K9 lifecycle, employee information, training records, veterinary care, and breeding production.
- **Project Operations**: Manages project lifecycle, resource allocation, incident logging, and performance evaluations.
- **Attendance System**: Comprehensive tracking with shift management, scheduling, project-specific recording, dual group tracking, leave management, and Arabic RTL PDF export. Includes an advanced Unified Matrix Attendance System with filtering, pagination, and multi-format export.
- **Ultra-Granular Permission System**: Provides `GENERAL_ADMIN` users with control over `PROJECT_MANAGER` access at a subsection level, featuring 79 distinct permission combinations, audit logging, and an intuitive admin dashboard.
- **Excel Export System**: Comprehensive XLSX export functionality for attendance reports and permissions data with Arabic RTL support, auto-formatted columns, and styled headers.
- **Modern Reporting Hub**: Centralized dashboard with dynamic statistics, categorized report organization (Attendance, Training, Breeding, Veterinary, Production, General), and integrated chart visualization.
- **Data Visualization Framework**: Chart.js integration with custom RTL-aware utilities for interactive charts across all reporting modules.
- **Handler Daily System**: Comprehensive daily operations management for K9 handlers featuring:
  - Daily schedule creation and management with auto-locking
  - Handler report submission with health checks, training logs, care tracking, behavior observations, and incident reporting
  - Configurable grace period for late report submissions (HANDLER_REPORT_GRACE_MINUTES)
  - Real-time notification system for schedule changes, report approvals/rejections
  - User management with bulk import from Excel/CSV
  - Automated cron jobs for schedule locking (23:59 daily) and notification cleanup (weekly)
  - **Enhanced Notification System**:
    - Direct links from notifications to specific reports/schedules
    - Pending reports counter in admin navigation menu
    - Separate notification pages for handlers (`/handler/notifications`) and admins (`/admin/notifications`)
    - Automatic notifications sent to project managers and admins when handlers submit reports
    - Real-time unread counters in navigation for all user roles
- **PM Report Review Workflow**: 2-tier review process for project-based report management:
  - Project Managers review reports from their assigned project first
  - PM actions: Approve, Reject, Request Edits, or Forward to General Admin for final approval
  - Covers four report types: HandlerReport, VeterinaryVisit, BreedingTrainingActivity, CaretakerDailyLog
  - Report statuses: DRAFT, SUBMITTED, APPROVED_BY_PM, REJECTED_BY_PM, FORWARDED_TO_ADMIN, APPROVED, REJECTED
  - Authorization enforced via ProjectManagerPermission model for proper access control
  - ReportReview audit trail for complete review history
  - Notification system for report submissions, approvals, rejections, and edit requests
  - API endpoints: `/supervisor/pm-review/*` for pending reports, counts, approval, rejection, edit requests, and admin forwarding
  - Service layer: `k9/services/report_review_service.py` handles all review workflow logic
- **Project Manager Dashboard**: Workflow-focused interface for PROJECT_MANAGER role:
  - **1:1 PM-Project Relationship**: Each PM manages exactly ONE project (Project.manager_id → User.id)
  - **Automatic Project Scoping**: All data automatically filtered to PM's assigned project - no project selection needed
  - **PM Dashboard** (`/pm/dashboard`): Project overview with metrics, pending approvals counter, team status, and quick action buttons
  - **My Team** (`/pm/my-team`): View all employees and handlers assigned to PM's project with account status
  - **My Dogs** (`/pm/my-dogs`): View all dogs assigned to PM's project with recent training/vet activity
  - **Pending Approvals** (`/pm/pending-approvals`): Centralized approval queue for handler reports, vet visits, breeding activities, and caretaker logs
  - **Project View** (`/pm/project`): Complete project details with statistics and quick links
  - **Security**: Strict project-scoped queries prevent cross-project data leakage; authorization checks in all approval endpoints
  - **Routes**: Blueprint registered at `/pm/*` with `@require_pm_project` decorator ensuring PM has assigned project

### System Design Choices
- **Client/Server Separation**: Clear distinction between frontend and backend.
- **Data Integrity**: Uses Enum-based status management.
- **Secure Identification**: UUID fields for object identification.
- **Flexible Data Storage**: JSON fields for metadata and audit logs.
- **Performance**: Optimized with database connection pooling and file size limits.
- **Scalability**: Modular architecture and role-based data isolation.

### Employee vs User/Handler Architecture
The system uses **two distinct but complementary concepts** for managing handlers:

**1. Employee Table (General Workforce Management)**
- **Purpose**: Manages ALL employees across the organization (handlers, vets, trainers, project managers, etc.)
- **Used by**: Attendance system, Project assignments, Training records, Veterinary records, Breeding/Production
- **Fields**: `employee_id` (badge number), `name`, `role` (HANDLER, VET, TRAINER, etc.)
- **Access**: Via `/employees` routes and Employee management pages
- **Shift Assignment**: Employees must be assigned to shifts via `/attendance/assignments` to appear in attendance dropdowns

**2. User Table with HANDLER Role (Authentication & Daily Operations)**
- **Purpose**: User accounts for handlers who need system access for daily reporting
- **Used by**: Handler Daily System (schedules, reports, notifications), Authentication/login
- **Fields**: `username`, `password_hash`, `full_name`, `role=HANDLER`
- **Access**: Via `/admin/users` and User management pages
- **Schedule Assignment**: Users are assigned to daily schedules via `/supervisor/schedules/create`

**Key Workflow:**
1. **For Attendance**: Create Employee record → Assign to shift via `/attendance/assignments` → Record attendance
2. **For Handler Daily Reports**: Create User account → Assign to daily schedule → Handler submits reports
3. **Optional**: Link Employee and User records via `user_account_id` field for integrated functionality

**Important Notes:**
- Attendance dropdowns only show employees **assigned to shifts** (not all employees)
- Daily schedule creation uses User accounts with HANDLER role
- These systems can work independently or be linked through the optional `user_account_id` field

## External Dependencies

### Python Packages
- **Flask Ecosystem**: Flask, Flask-SQLAlchemy, Flask-Login, Flask-Migrate.
- **Security**: Werkzeug.
- **Database**: psycopg2-binary.
- **PDF Generation**: ReportLab.
- **Excel Export**: openpyxl.
- **Scheduling**: APScheduler.
- **Google API**: google-api-python-client (for future Google Drive integration).

### Frontend Dependencies
- **UI Framework**: Bootstrap 5 RTL.
- **Icon Library**: Font Awesome 6.
- **Fonts**: Google Fonts (Noto Sans Arabic).
- **Charting**: Chart.js.

### Database Requirements
- **Primary Database**: PostgreSQL (automatically configured for production and Replit environments).
- **UUID Compatibility**: Native UUID support for PostgreSQL, automatic string fallback for SQLite.
- **Connection Pooling**: Configured for production PostgreSQL.
- **Migration Support**: Flask-Migrate with Alembic.