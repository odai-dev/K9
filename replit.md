# K9 Operations Management System

## Overview
This is a comprehensive K9 operations management system designed for military and police canine units. The system is a web-based, mobile-first, and fully responsive application with an Arabic RTL-compatible UI. Its primary purpose is to manage all aspects of K9 life cycles, including employee supervision, project management, training, veterinary care, breeding, and operational missions. The system aims to streamline K9 operations, enhance efficiency, and provide robust tracking and reporting capabilities for critical canine unit functions.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
- **UI Framework**: Bootstrap 5 RTL for comprehensive UI components with right-to-left language support.
- **Styling**: Custom CSS optimized for RTL layouts.
- **Fonts**: Google Fonts, specifically Noto Sans Arabic, for appropriate Arabic text rendering.
- **Responsiveness**: Mobile-first design approach ensuring full responsiveness across all device types.

### Technical Implementations
- **Backend Framework**: Flask (Python) utilizing a modular Blueprint structure for organized development.
- **Database**: PostgreSQL, integrated via SQLAlchemy ORM for object-relational mapping.
- **Authentication**: Flask-Login implements session-based authentication and role-based access control with two tiers: `GENERAL_ADMIN` (full access) and `PROJECT_MANAGER` (limited to assigned resources).
- **Database Migrations**: Flask-Migrate, powered by Alembic, for schema versioning and management.
- **File Handling**: Local file system storage for uploads, with configurable limits.
- **Security**: Incorporates CSRF protection, configurable session timeouts, input validation, and audit logging for all user actions, including IP tracking.

### Feature Specifications
- **Dogs Management**: Tracks full lifecycle (Active, Retired, Deceased, Training), physical characteristics, photos, and assignments.
- **Employee Management**: Manages personal and professional information for roles (Handler, Vet, Project Manager), including assignment and attendance. Roles are simplified to Handler (سائس), Vet (طبيب), and Project Manager (مسؤول مشروع).
- **Training System**: Records session-based training across various categories (Obedience, Detection, Agility, Attack, Fitness) with trainer assignments and progress notes.
- **Veterinary Care**: Documents visits (Routine, Emergency, Vaccination), health metrics, diagnoses, treatments, and costs.
- **Breeding Management**: A comprehensive system covering general information, maturity tracking, heat cycles, mating records, pregnancy monitoring, delivery records, puppy management, and puppy training.
- **Project Operations**: Manages project lifecycle (Planned, Active, Completed, Cancelled), resource allocation (dogs), incident logging, suspicion reporting, and performance evaluations for both employees and dogs. Project finish dates are automatically set upon completion.
- **Attendance System**: Comprehensive attendance tracking system with shift management, employee and dog scheduling, and project-specific attendance recording. Features include shift assignments, bulk attendance operations, status tracking (Present, Absent, Late), absence reason tracking, and attendance reporting.
- **Enhanced Permission System**: Granular role-based access control for PROJECT_MANAGER users with toggleable permissions per project. GENERAL_ADMIN can control: manage assignments, shifts, attendance, training, incidents, performance evaluations, and view veterinary/breeding info. Permissions are enforced at both backend and frontend levels with immediate effect.

### System Design Choices
- **Client/Server Separation**: Clear distinction between frontend and backend.
- **Data Integrity**: Uses Enum-based status management for consistency.
- **Secure Identification**: UUID fields for object identification.
- **Flexible Data Storage**: JSON fields for metadata and audit logs.
- **Performance**: Optimized with database connection pooling and file size limits.
- **Scalability**: Modular architecture and role-based data isolation for future expansion.

## External Dependencies

### Python Packages
- **Flask Ecosystem**: Flask, Flask-SQLAlchemy, Flask-Login, Flask-Migrate.
- **Security**: Werkzeug (for password hashing and proxy handling).
- **Database**: PostgreSQL adapter for SQLAlchemy (psycopg2-binary).
- **PDF Generation**: ReportLab.

### Frontend Dependencies
- **UI Framework**: Bootstrap 5 RTL.
- **Icon Library**: Font Awesome 6.
- **Fonts**: Google Fonts (Noto Sans Arabic).

### Database Requirements
- **Primary Database**: PostgreSQL for production, SQLite for development/Replit.
- **Auto-Detection**: System automatically detects database type from DATABASE_URL.
- **UUID Compatibility**: Automatic string/UUID conversion for SQLite compatibility.
- **Connection Pooling**: Configured for production PostgreSQL.
- **Migration Support**: Alembic.

## Replit Deployment Notes

### Database Configuration
- **SQLite Mode**: Activated automatically when DATABASE_URL is not set or starts with "sqlite"
- **UUID Handling**: All UUID columns use String(36) in SQLite mode for compatibility
- **Route Compatibility**: All route handlers use string IDs instead of UUID objects for SQLite

### Setup Instructions
1. Import project to Replit
2. Application auto-detects Replit environment and uses SQLite
3. Database and admin user created automatically on first run
4. Optional: Run `python simple_seed.py` for sample data

### Common Issues Prevention
- UUID compatibility handled automatically in models and routes
- Database file management handled by SQLite
- No manual database configuration needed in Replit environment

## Recent Changes (August 2025)

### Project Migration to Replit Environment Completed
- **Date**: August 6, 2025
- **Changes**: Successfully migrated K9 Operations Management System from Replit Agent to standard Replit environment
- **Issues Fixed**:
  - Fixed URL routing errors in project dashboard template
  - Corrected `main.training_sessions` to `main.training_list` endpoint references
  - Corrected `main.veterinary_visits` to `main.veterinary_list` endpoint references
  - Resolved all UUID variable naming conflicts (project_uuid → project.id, dog_uuid → dog.id)
  - Fixed NameError issues in project assignments, incidents, suspicions, and evaluations routes
  - Verified all dependencies are properly installed and configured
- **Migration Benefits**:
  - Enhanced security and performance on standard Replit infrastructure
  - Automatic SQLite fallback for development environment
  - Proper gunicorn server configuration for production-ready deployment
  - Client/server separation maintained with robust security practices

### Enhanced Project Manager Constraint System Implementation
- **Date**: August 6, 2025
- **Changes**: Strengthened project manager assignment constraints to enforce one-active-project rule
- **New Features**:
  - Enhanced `validate_project_manager_assignment()` function with stricter validation
  - Added `get_user_all_projects()` function to check all project statuses
  - Project managers limited to one ACTIVE or PLANNED project at a time
  - Validation enforced during project creation, manager assignment, and status changes
  - Status change validation prevents activating projects when manager has ongoing projects
- **Rules Enforced**:
  - PROJECT_MANAGER can only manage one ACTIVE project at a time
  - PROJECT_MANAGER can only manage one PLANNED project at a time
  - New projects can only be assigned after previous projects are COMPLETED or CANCELLED
  - GENERAL_ADMIN users are exempt from all constraints
  - Clear Arabic error messages explaining constraint violations
- **Components Enhanced**:
  - `utils.py`: Enhanced validation functions with comprehensive project status checking
  - `routes.py`: Added validation to project status change route
  - Error messages provide specific details about conflicting projects
- **Benefits**:
  - Prevents project manager overload with clear one-project focus
  - Ensures accountability and proper resource allocation
  - Maintains system integrity with consistent constraint enforcement
  - Provides clear feedback when constraints are violated

### Project Manager Constraint System Implementation
- **Date**: August 5, 2025
- **Changes**: Implemented project manager constraint system with admin override capability
- **New Features**:
  - Project managers are restricted to managing one active project at a time by default
  - Validation functions added to check project manager assignment constraints
  - Admin panel displays current active projects for each project manager
  - Multi-project management toggle (ready for future implementation)
  - Project assignment routes validate manager constraints before assignment
- **Components Added**:
  - `validate_project_manager_assignment()` function in `utils.py`
  - `get_user_active_projects()` function for retrieving manager's active projects
  - Project creation and manager assignment validation in relevant routes
  - Admin panel UI showing active projects and constraint status
- **Benefits**:
  - Prevents project managers from being overloaded with multiple active projects
  - Maintains clear accountability with single project focus
  - General admin retains full control with ability to override constraints
  - Clear visual indication of manager workload in admin interface

## Recent Changes (August 2025)

### Project Migration to Replit Environment Completed
- **Date**: August 6, 2025
- **Changes**: Successfully migrated K9 Operations Management System from Replit Agent to standard Replit environment
- **Issues Fixed**:
  - Fixed URL routing errors in project dashboard template
  - Corrected `main.training_sessions` to `main.training_list` endpoint references
  - Corrected `main.veterinary_visits` to `main.veterinary_list` endpoint references
  - Verified all dependencies are properly installed and configured
- **Migration Benefits**:
  - Enhanced security and performance on standard Replit infrastructure
  - Automatic SQLite fallback for development environment
  - Proper gunicorn server configuration for production-ready deployment
  - Client/server separation maintained with robust security practices

### Enhanced Role-Based Access Control Implementation
- **Date**: August 5, 2025
- **Changes**: Implemented comprehensive granular permission system for PROJECT_MANAGER users
- **New Features**:
  - ProjectManagerPermission model for per-project permission control
  - Unified admin panel combining user management and permission control
  - Permission decorators for route-level access control
  - Real-time permission enforcement in both backend and frontend
  - Project-scoped data filtering for enhanced security
- **Components Added**:
  - `permission_decorators.py`: Decorators for route protection
  - `templates/admin/admin_panel.html`: Unified admin interface
  - Enhanced utility functions in `utils.py` for permission checking
  - New routes in `routes.py` for user and permission management
- **Permission Types**:
  - Manage assignments (assign/unassign dogs and employees)
  - Manage shifts (create/edit work shifts)
  - Manage attendance (record attendance for dogs/employees)
  - Manage training (create/manage training sessions)
  - Manage incidents (log incidents and suspicion reports)
  - Manage performance (create performance evaluations)
  - View veterinary (access veterinary records for assigned dogs)
  - View breeding (access breeding records for assigned dogs)
- **Employee-User Linkage**: 
  - PROJECT_MANAGER users are automatically linked to Employee records with matching role
  - Admin panel queries only users with linked PROJECT_MANAGER employee profiles
  - Automatic synchronization creates user accounts for existing PROJECT_MANAGER employees
  - General admin can edit usernames, passwords, and email addresses for project managers
  - System prevents duplicate usernames and emails across user accounts
- **Benefits**: 
  - GENERAL_ADMIN can fine-tune each PROJECT_MANAGER's access per project
  - Immediate permission toggle effects without system restart
  - Enhanced security with row-level data filtering
  - Clear UI indication of user permissions and linked employee information
  - Unified admin interface for easier management
  - Ensures users are tied to actual employee records with PROJECT_MANAGER role