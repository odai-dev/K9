# K9 Operations Management System

## Overview
This project is a comprehensive, web-based, and mobile-first K9 operations management system designed for military and police canine units. It provides an Arabic RTL-compatible UI. The system's core purpose is to manage the entire lifecycle of K9s, encompassing employee supervision, project management, training, veterinary care, breeding, and operational missions. The system aims to streamline operations, enhance efficiency, and provide robust tracking and reporting for critical canine unit functions, supporting a vision for optimized K9 deployment and resource utilization.

## Recent Updates (August 2025)
- **Project Manager Credentials Removed**: Removed PM username/password from seed data - only admin user created by default - August 14, 2025
- **Codebase Cleanup Complete**: Removed 10+ obsolete files including backup routes, test scripts, and redundant seed files - August 14, 2025
- **Documentation Updated**: Refreshed all README, SETUP, QUICKSTART, and IMPORT_GUIDE files to reflect current PostgreSQL setup
- **Attached Assets Cleaned**: Removed 22+ temporary pasted files and screenshots, keeping only essential Arabic documentation
- **Simple Seed Enhanced**: Updated to follow current business rules (Project Manager single active project constraint)
- **Migration Complete**: Successfully migrated from Replit Agent to standard Replit environment with verified functionality - August 14, 2025
- **Route Issues Fixed**: Added missing breeding module routes (maturity_add, heat_cycles_add, mating_add, etc.)
- **Form Submission Bugs Fixed**: Resolved Dog model constructor issues and file upload security problems
- **Application Stability**: Fixed template routing errors and improved error handling
- **Database Upgraded**: Migrated from SQLite to PostgreSQL for better performance and scalability
- **Form Submission Fixed**: Resolved critical bug where adding new dogs caused page refresh without saving
- **Model Constructors Fixed**: Updated all database model instantiation to use proper field assignment pattern
- **Permission System Fixed**: Resolved critical bug where PROJECT_MANAGER users couldn't access assigned data
- **Integration Working**: Dashboard, dogs, employees, and projects now properly use SubPermission grants
- **Authentication Verified**: Users can log in and access appropriate data based on their permissions
- **Bug Fixes Complete**: Fixed critical form submission issues for dogs and employees add functionality
- **Enum Mapping Fixed**: Resolved EmployeeRole enum mismatch between form values and database values
- **Employee Roles Complete**: Added TRAINER (مدرب) and BREEDER (مربي) roles to all employee interfaces
- **Code Quality**: Significantly improved with obsolete file removal and documentation updates

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
- **Ultra-Granular Permission System**: Revolutionary permission architecture providing GENERAL_ADMIN users with complete control over PROJECT_MANAGER access at subsection level. Features 79 distinct permission combinations across 9 major sections (Dogs, Employees, Projects, Training, Veterinary, Breeding, Attendance, Reports, Analytics). Each permission supports 7 action types (View, Create, Edit, Delete, Export, Assign, Approve). Includes comprehensive audit logging, real-time permission updates, bulk operations, preview functionality, and multi-format exports (JSON, PDF, CSV). Admin dashboard provides intuitive matrix interface with project-specific and global permission scoping.

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
- **Primary Database**: PostgreSQL for production and Replit environments (automatically configured).
- **Auto-Detection**: System automatically detects database type from DATABASE_URL environment variable.
- **UUID Compatibility**: Native UUID support for PostgreSQL, automatic string fallback for SQLite in local development.
- **Connection Pooling**: Configured for production PostgreSQL with pool recycling and pre-ping.
- **Migration Support**: Flask-Migrate with Alembic for schema versioning and automatic table creation.