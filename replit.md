# K9 Operations Management System

## Overview
This project is a comprehensive, web-based, and mobile-first K9 operations management system designed for military and police canine units. It provides an Arabic RTL-compatible UI. The system's core purpose is to manage the entire lifecycle of K9s, encompassing employee supervision, project management, training, veterinary care, breeding, and operational missions. The system aims to streamline operations, enhance efficiency, and provide robust tracking and reporting for critical canine unit functions, supporting a vision for optimized K9 deployment and resource utilization.

## Recent Updates (August 2025)
- **Puppy Creation Form Fixed**: Resolved issue where delivery records dropdown was empty in puppy creation form. Fixed database queries to properly populate delivery records for all user roles and fixed multiple model constructor issues throughout the application - August 20, 2025
- **Migration to Standard Replit Environment Complete**: Successfully migrated project from Replit Agent to standard Replit environment with PostgreSQL database provisioning, secure configuration, sample data integration, and verified functionality - August 20, 2025
- **Training & Veterinary Reports Navigation**: Added Reports buttons to Training and Veterinary sections that navigate to General Reports page with pre-applied filters for seamless section-specific reporting - August 19, 2025
- **Production Navigation Enhancement**: Modified reports advanced page to redirect production selection to main production management interface with comprehensive dropdown options - August 19, 2025
- **Export Functionality Added**: Implemented PDF and Excel export for unified attendance matrix with proper Arabic text support and color-coded status indicators - August 19, 2025
- **Unified Matrix Attendance Feature**: Implemented comprehensive unified attendance matrix with Bootstrap 5 RTL Arabic support, advanced filtering, real-time data loading, and export capabilities (PDF/Excel/CSV) - August 18, 2025
- **PDF Layout Fixed**: Updated PM Daily PDF reports to stack group tables vertically instead of horizontally for better readability - August 18, 2025
- **Attendance Reporting System Complete**: Implemented comprehensive attendance reporting module with RTL Arabic support - August 18, 2025
- **PDF Generation Fixed**: Added Arabic RTL PDF generation with proper text rendering, Bootstrap 5 RTL templates, and vertical group layout - August 18, 2025
- **Model Issues Resolved**: Fixed ProjectAttendance vs ProjectAttendanceReporting model references and UUID handling - August 18, 2025
- **Sample Data Added**: Created comprehensive sample attendance data for testing daily sheet functionality - August 18, 2025
- **Authentication Working**: Fixed audit logging parameters and API authentication for attendance reports - August 18, 2025
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
- **Production Management**: Covers general information, maturity tracking, heat cycles, mating records, pregnancy monitoring, delivery records, puppy management, and puppy training.
- **Project Operations**: Manages project lifecycle (Planned, Active, Completed, Cancelled), resource allocation (dogs), incident logging, suspicion reporting, and performance evaluations. Project finish dates are automatically set upon completion. **Project managers are permanently restricted to one active or planned project at a time** - this is an enforced system constraint that cannot be overridden.
- **Attendance System**: Comprehensive attendance tracking system with shift management, employee and dog scheduling, and project-specific attendance recording. Features include shift assignments, bulk attendance operations, status tracking (Present, Absent, Late), absence reason tracking, and attendance reporting.
- **Attendance Reporting Module**: Complete reporting system with daily sheet generation mirroring paper DOCX forms. Features Arabic RTL PDF export, Bootstrap 5 RTL templates, comprehensive API endpoints, and sample data integration. Includes dual group attendance tracking, leave management, and signature boxes for official documentation.
- **Unified Matrix Attendance System**: Advanced attendance matrix feature displaying employees vs dates with comprehensive filtering, pagination, real-time data loading, and multi-format export capabilities. Features Bootstrap 5 RTL design, Arabic language support, dynamic status filtering, project scoping, and responsive layout for optimal viewing across devices.
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