# K9 Operations Management System

## Overview

This is a comprehensive K9 operations management system built for military/police canine units. The system is web-based, mobile-first, and fully responsive with Arabic RTL-compatible UI. It manages all aspects of dog life cycles, employee supervision, projects, training, veterinary care, breeding, and operational missions.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes (Updated - August 2, 2025)

✅ **Employee Role System Simplified - August 2, 2025**
- Simplified employee roles to only three options as requested:
  * سائس (Handler) - for dog handlers
  * طبيب (Vet) - for veterinarians  
  * مسؤول مشروع (Project Manager) - for project managers
- Updated add/edit employee forms to show only these three roles
- Fixed role display in employee list with correct Arabic names
- Removed unnecessary TRAINER and OPERATIONS roles from templates

✅ **Project Attendance Tracking System Added - August 2, 2025**
- Added comprehensive project attendance tracking system based on attached document specification
- Created ProjectAttendance, AttendanceEntry, and LeaveRequest models for daily attendance management
- Implemented route handlers for listing, adding, and viewing attendance records
- Added templates for attendance list, add form, and detailed view with print functionality
- Integrated attendance management into project dashboard with navigation buttons
- Support for two groups (صباحي/مسائي) with employee, substitute, and dog assignments
- Leave request tracking with different types (سنوية/مرضية/طارئة/أخرى)
- Fixed JavaScript errors in search functionality to prevent console errors
- Full RTL Arabic interface maintained throughout attendance system

✅ **Migration Completed Successfully - August 2, 2025**
- Successfully migrated K9 Operations Management System to Replit environment
- Database provisioned and connected (PostgreSQL) with all environment variables configured
- All dependencies properly installed and configured
- Application running smoothly on port 5000 with gunicorn
- Fixed import statements and database models for new attendance system
- All core functionality verified and working with enhanced attendance tracking

✅ **Project Finish Date Management Enhancement - August 2, 2025**
- Removed manual finish date input field from project creation form
- Made end_date nullable in Project model (set automatically on completion)
- Added automatic end date setting when project status changes to COMPLETED
- Enhanced project dashboard with status change buttons:
  * "بدء المشروع" (Start Project) - changes status from PLANNED to ACTIVE
  * "إنهاء المشروع" (Complete Project) - changes status to COMPLETED and sets end_date
  * "إلغاء المشروع" (Cancel Project) - changes status to CANCELLED
- Added project status change route with audit logging
- Fixed database schema constraint issues by making end_date nullable
- Projects now automatically calculate duration when completed

✅ **Project Dashboard & Enhanced Assignment System - August 2, 2025**
- Created comprehensive project dashboard system with real-time statistics
- Added centralized overview for each project showing resources, incidents, suspicions, and evaluations
- Enhanced project assignment management with improved UI and functionality:
  * Project manager assignment and change capabilities (GENERAL_ADMIN only)
  * Employee assignment with role selection (Handler, Trainer, Vet, Operations)
  * Dog assignment with activity status tracking
  * Period management (Morning, Evening, Night shifts)
  * Easy removal and status toggle functionality
- Fixed template routing errors (project_add_incident, project_assign_employee)
- Added navigation between all project sections with consistent UI
- Updated Suspicion model queries to use correct field names (evidence_collected)
- All project functionality now accessible through intuitive dashboard interface

✅ **Migration to Replit Environment Completed - August 2, 2025**
- Successfully migrated K9 Operations Management System from Replit Agent to Replit environment
- Database provisioned and connected (PostgreSQL) with all environment variables configured
- Fixed status mapping errors in project templates (PLANNED vs PLANNING)
- Enhanced Projects section with comprehensive management features based on attached specifications:
  * Advanced employee/dog assignment management with periods and attendance tracking
  * Comprehensive incident logging system with severity levels and attachments
  * Suspicion reporting with detection details and follow-up tracking
  * Performance evaluation system for both employees and dogs
  * Full RTL Arabic interface maintained throughout
- Application running smoothly on port 5000 with gunicorn
- All core functionality verified and working

✅ **Production/Breeding System Enhancement** (8 comprehensive sections)
- Added complete breeding management system as requested:
  1. General Information + Maturity tracking (البلوغ)
  2. Heat Cycle management (الدورة) - tracks 1st, 2nd, 3rd cycles 
  3. Mating Records (التزاوج) - begins after 3rd heat cycle
  4. Pregnancy tracking (الحمل) - weekly monitoring
  5. Delivery records (الولادة) - complete birth documentation
  6. Puppy management (الجراء) - individual puppy tracking
  7. Puppy Training (تدريب الجراء) - specialized training for puppies
- Enhanced Employee roles with TRAINER and OPERATIONS
- Fixed missing enum values causing training module errors

✅ **Security & Architecture Improvements**
- Proper client/server separation maintained
- All security practices aligned with Replit standards
- Database models enhanced with new production system tables
- RTL Arabic interface fully preserved

✅ **Migration to Replit Environment Completed - July 31, 2025**
- Successfully migrated K9 Operations Management System from Replit Agent to standard Replit environment
- Database provisioned and connected (PostgreSQL)
- All dependencies properly installed and configured
- Application now running on port 5000 with gunicorn
- Fixed template date calculation errors in dog views
- Fixed role mapping issues in employee templates
- Resolved microchip_id unique constraint issues (empty strings converted to NULL)  
- All console errors eliminated and application fully functional

✅ **Employee Form Cleanup - August 2, 2025**
- Removed "الرقم المدني" (Civil ID) field from employee management
- Removed "القسم" (Department) and "الرتبة" (Rank) fields from work information section
- Updated Employee model, templates (add.html, edit.html, list.html), and routes
- Cleaned database by dropping unused columns
- Simplified employee forms to show only essential information

✅ **Production/Breeding System Enhancement** (8 comprehensive sections)
- Added complete breeding management system as requested:
  1. General Information + Maturity tracking (البلوغ)
  2. Heat Cycle management (الدورة) - tracks 1st, 2nd, 3rd cycles 
  3. Mating Records (التزاوج) - begins after 3rd heat cycle
  4. Pregnancy tracking (الحمل) - weekly monitoring
  5. Delivery records (الولادة) - complete birth documentation
  6. Puppy management (الجراء) - individual puppy tracking
  7. Puppy Training (تدريب الجراء) - specialized training for puppies
- Enhanced Employee roles with TRAINER and OPERATIONS
- Fixed missing enum values causing training module errors

✅ **Security & Architecture Improvements**
- Proper client/server separation maintained
- All security practices aligned with Replit standards
- Database models enhanced with new production system tables
- RTL Arabic interface fully preserved

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python) with modular Blueprint structure
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Flask-Login with role-based access control
- **Migration System**: Flask-Migrate with Alembic
- **File Handling**: Local file system storage with configurable upload limits

### Frontend Architecture
- **UI Framework**: Bootstrap 5 RTL with Arabic font support (Noto Sans Arabic)
- **Styling**: Custom CSS with RTL layout optimization
- **JavaScript**: Vanilla JS with Bootstrap components
- **Responsive Design**: Mobile-first approach with full responsive layout

### Database Design
- Uses SQLAlchemy with declarative base model
- PostgreSQL as the primary database with connection pooling
- Enum-based status management for consistent data integrity
- UUID fields for secure object identification
- JSON fields for flexible data storage (audit logs, metadata)

## Key Components

### Authentication & Authorization
- **Two-tier role system**:
  - `GENERAL_ADMIN`: Full system access and management
  - `PROJECT_MANAGER`: Limited access to assigned resources only
- **Session-based authentication** with Flask-Login
- **Audit logging** for all user actions with IP tracking
- **Setup route** for initial admin user creation

### Core Modules

#### Dogs Management
- Complete lifecycle tracking (Active, Retired, Deceased, Training)
- Breed, gender, and physical characteristics management
- Photo upload and file handling
- Location and assignment tracking

#### Employee Management
- Multiple role types (Handler, Trainer, Vet, Operations)
- Personal and professional information tracking
- Attendance and assignment management
- Contact information and emergency details

#### Training System
- Session-based training tracking with categories (Obedience, Detection, Agility, Attack, Fitness)
- Trainer assignment and performance evaluation
- Duration and location tracking
- Progress notes and assessment scoring

#### Veterinary Care
- Visit types (Routine, Emergency, Vaccination)
- Health metrics tracking (weight, temperature, vital signs)
- Diagnosis and treatment records
- Cost tracking and medical history

#### Breeding Management
- Breeding cycle tracking (Natural/Artificial)
- Parentage management and offspring tracking
- Mating date and expected birth date calculations
- Success rate and survival tracking

#### Project Operations
- Project lifecycle management with status tracking
- Manager assignment and resource allocation
- Priority levels and deadline management
- Mission type categorization

### Data Flow
1. **User Authentication**: Login → Role verification → Permission checking
2. **CRUD Operations**: Form submission → Validation → Database update → Audit logging
3. **File Uploads**: File validation → Secure storage → Database reference
4. **Reporting**: Data aggregation → PDF generation → File delivery

## External Dependencies

### Python Packages
- **Flask ecosystem**: Flask, Flask-SQLAlchemy, Flask-Login, Flask-Migrate
- **Security**: Werkzeug for password hashing and proxy handling
- **Database**: PostgreSQL adapter and SQLAlchemy
- **PDF Generation**: ReportLab for report creation
- **File Handling**: Secure filename utilities

### Frontend Dependencies
- **Bootstrap 5 RTL**: Complete UI framework with RTL support
- **Font Awesome 6**: Icon library for UI elements
- **Google Fonts**: Noto Sans Arabic for proper Arabic text rendering

### Database Requirements
- **PostgreSQL**: Primary database with JSON support
- **Connection Pooling**: Configured for production environments
- **Migration Support**: Alembic-based schema versioning

## Deployment Strategy

### Configuration Management
- **Environment-based configuration**: Development and Production configs
- **Environment variables**: Database URLs, secret keys, and service credentials
- **File upload configuration**: Configurable storage paths and size limits

### Security Features
- **CSRF Protection**: Built-in form security
- **Session Management**: Configurable session timeouts
- **Proxy Support**: Production deployment with reverse proxy
- **Input Validation**: Server-side validation for all forms

### Performance Optimizations
- **Database Connection Pooling**: Prevents connection exhaustion
- **File Size Limits**: 16MB maximum upload size
- **Static File Serving**: Optimized for production deployment

### Scalability Considerations
- **Modular Blueprint Architecture**: Easy feature addition and maintenance
- **Role-based Data Isolation**: PROJECT_MANAGER users only see assigned data
- **Audit Trail System**: Complete action logging for compliance
- **Responsive Design**: Works across all device types

The system is designed for military-grade security and operational requirements while maintaining ease of use and comprehensive functionality for managing K9 operations.