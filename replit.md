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
- **Unified Header Design**: Modern gradient hero headers with quick navigation bars across all user roles, featuring animated buttons, user dropdowns, and consistent design language.

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
- **Hybrid Permission System (V2)**: Complete role-based access control with user-specific overrides, featuring:
  - **Role Baseline Permissions**: Each role (HANDLER, PROJECT_MANAGER, GENERAL_ADMIN, etc.) has predefined permission sets
  - **User-Specific Overrides**: GENERAL_ADMIN can grant or revoke individual permissions per user beyond their role baseline
  - **Permission Formula**: `effective_permissions = role_baseline + granted_overrides - revoked_overrides`
  - **Real-Time Updates**: Permission changes take effect immediately with automatic cache invalidation
  - **Permission Management UI**: Admin interface to view baseline vs overrides, with 3-way controls (Default/Grant/Revoke)
- **Handler Shift Report Enforcement**: Hard enforcement requiring handlers to submit shift reports for completed shifts before accessing system features. Blocked handlers are redirected to pending reports page until all reports are submitted.
- **Excel Export System**: Comprehensive XLSX export functionality for reports with Arabic RTL support.
- **Modern Reporting Hub**: Centralized dashboard with dynamic statistics, categorized report organization, and integrated chart visualization.
- **Handler Daily System**: Comprehensive daily operations management for K9 handlers including schedule creation, two-tier reporting (Shift and Daily Reports), and a modern notification system.
- **Report Export System**: Unified Minimal Elegant PDF design for all report types with Arabic RTL support and consistent styling.
- **Report Review Workflow**: A 2-tier review process for project-based reports with statuses, audit trails, and notifications.
- **Admin Final Approval System**: Two-tier approval workflow (Project Manager review, General Admin final approval/rejection) for all report types, with dual notifications and audit logging.
- **Unified Reporting System**: Centralized reporting architecture with ReportDefinition, ReportContext, and ReportApprovalHistory models. Features Generate → Preview → Approve → Export workflow, professional PDF/Excel export with Arabic RTL support, PM dashboard integration for pending reports, and permission-based export restrictions (PM must approve before export, Admin has full access).
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
- **Production Readiness**: Complete removal of debug code, comprehensive error handling with structured logging, and robust security hardening.
- **Unified PDF Design**: Minimal Elegant design system implemented across all PDF reports for consistent professional document generation.

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