# K9 Operations Management System

## Overview
This project is a comprehensive, web-based, and mobile-first K9 operations management system designed for military and police canine units. It provides an Arabic RTL-compatible UI. The system's core purpose is to manage the entire lifecycle of K9s, encompassing employee supervision, project management, training, veterinary care, breeding, and operational missions. The system aims to streamline operations, enhance efficiency, and provide robust tracking and reporting for critical canine unit functions, supporting a vision for optimized K9 deployment and resource utilization.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
- **UI Framework**: Bootstrap 5 RTL for comprehensive UI components with right-to-left language support.
- **Styling**: Custom CSS optimized for RTL layouts.
- **Fonts**: Google Fonts, specifically Noto Sans Arabic, for appropriate Arabic text rendering.
- **Responsiveness**: Mobile-first design approach ensuring full responsiveness across all device types.

### Technical Implementations
- **Backend Framework**: Flask (Python) utilizing a modular Blueprint structure.
- **Database**: PostgreSQL, integrated via SQLAlchemy ORM.
- **Authentication**: Flask-Login implements session-based authentication and role-based access control with two tiers: `GENERAL_ADMIN` (full access) and `PROJECT_MANAGER` (limited to assigned resources).
- **Database Migrations**: Flask-Migrate, powered by Alembic, for schema versioning and management.
- **File Handling**: Local file system storage for uploads, with configurable limits.
- **Security**: Incorporates CSRF protection, configurable session timeouts, input validation, and audit logging for all user actions, including IP tracking.

### Feature Specifications
- **Dogs Management**: Tracks full lifecycle (Active, Retired, Deceased, Training), physical characteristics, photos, and assignments.
- **Employee Management**: Manages personal and professional information for roles (Handler, Vet, Project Manager), including assignment and attendance.
- **Training System**: Records session-based training across various categories (Obedience, Detection, Agility, Attack, Fitness) with trainer assignments and progress notes.
- **Veterinary Care**: Documents visits (Routine, Emergency, Vaccination), health metrics, diagnoses, treatments, and costs.
- **Breeding Management**: Covers general information, maturity tracking, heat cycles, mating records, pregnancy monitoring, delivery records, puppy management, and puppy training.
- **Project Operations**: Manages project lifecycle (Planned, Active, Completed, Cancelled), resource allocation (dogs), incident logging, suspicion reporting, and performance evaluations. Project finish dates are automatically set upon completion. **Project managers are permanently restricted to one active or planned project at a time** - this is an enforced system constraint that cannot be overridden.
- **Attendance System**: Comprehensive attendance tracking system with shift management, employee and dog scheduling, and project-specific attendance recording. Features include shift assignments, bulk attendance operations, status tracking (Present, Absent, Late), absence reason tracking, and attendance reporting.
- **Enhanced Permission System**: Granular role-based access control for `PROJECT_MANAGER` users with toggleable permissions per project. `GENERAL_ADMIN` can control permissions for: managing assignments, shifts, attendance, training, incidents, performance evaluations, and viewing veterinary/breeding information. Permissions are enforced at both backend and frontend levels with immediate effect. `PROJECT_MANAGER` users are automatically linked to employee records with matching roles.

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