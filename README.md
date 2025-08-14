# K9 Operations Management System

A comprehensive web-based management system for military and police canine units, built with Flask and designed for Arabic RTL support.

## Features

- **Dogs Management**: Complete lifecycle tracking, health records, and assignments
- **Employee Management**: Handler, veterinarian, trainer, and project manager profiles
- **Project Operations**: Mission planning, resource allocation, and performance tracking
- **Training System**: Session logging and progress monitoring
- **Veterinary Care**: Health visits, treatments, and medical records
- **Breeding Management**: Comprehensive breeding program management
- **Attendance System**: Project-based attendance and shift management
- **Reports**: PDF generation for all major data sections

## Quick Setup (Replit)

### 1. Import the Project
- Fork or import this repository into your Replit account
- The project will automatically detect the Replit environment

### 2. Install Dependencies
Dependencies are automatically installed via the `pyproject.toml` file. The system uses:
- PostgreSQL database (automatically configured)
- All Python dependencies auto-install on first run

### 3. Database Setup
The application automatically uses PostgreSQL for production compatibility:
- Database is created automatically via environment variables
- Tables are created automatically on first run
- UUID-compatible schema with string fallbacks

### 4. Start the Application
Click the "Run" button or use:
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### 5. Add Sample Data (Optional)
To populate the system with sample data for testing:
```bash
python simple_seed.py
```

### 6. Verify Setup (Optional)
Run the verification script to ensure everything is configured correctly:
```bash
python verify_setup.py
```

### 7. Login
Default admin account:
- **Username**: `admin`
- **Password**: `admin123`

Additional test accounts (after running seed script):
- **Username**: `manager1` **Password**: `manager123`
- **Username**: `manager2` **Password**: `manager123`

## Local Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL (optional, SQLite used by default)

### Installation
1. Clone the repository:
```bash
git clone <repository-url>
cd k9-operations-system
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables (optional):
```bash
export DATABASE_URL="sqlite:///k9_operations.db"
export SESSION_SECRET="your-secret-key-here"
```

5. Run the application:
```bash
python main.py
```

## Database Configuration

### PostgreSQL (Default/Replit)
- Automatically configured via Replit environment variables
- Production-ready database with connection pooling
- UUID support with string compatibility fallbacks
- Automatic schema creation and migrations

### Local Development
For local development, set the `DATABASE_URL` environment variable:
```bash
export DATABASE_URL="postgresql://user:password@localhost/k9_operations"
# Or use SQLite for local testing:
export DATABASE_URL="sqlite:///k9_operations.db"
```

## Important Notes for Replit Users

### UUID Compatibility
This system uses UUID identifiers for most entities. The codebase automatically handles database compatibility:
- **PostgreSQL**: Native UUID support (primary)
- **SQLite**: UUIDs stored as strings (fallback for local development)

### File Uploads
- Upload directory: `uploads/`
- Maximum file size: 16MB
- Supported formats: PDF, JPG, PNG
- Secure filename handling with virus scanning

### RTL Support
The interface is optimized for Arabic (RTL) layout:
- Bootstrap 5 RTL with full Arabic language support
- Noto Sans Arabic font for proper text rendering
- Right-to-left navigation, forms, and data tables
- Arabic enum values and labels throughout

### Permission System
- **Ultra-Granular Permissions**: 79 distinct permission combinations
- **Project-Specific Access**: PROJECT_MANAGER users restricted to assigned projects
- **Real-time Updates**: Permission changes take effect immediately
- **Audit Logging**: All permission changes tracked with timestamps

## Project Structure

```
├── app.py                    # Flask application factory
├── main.py                   # Application entry point
├── models.py                 # Database models with UUID compatibility
├── routes.py                 # Main application routes (3000+ lines)
├── api_routes.py             # API endpoints for attendance system
├── auth.py                   # Authentication routes
├── admin_routes.py           # Admin dashboard and permissions
├── attendance_service.py     # Attendance business logic
├── utils.py                  # Utility functions and helpers
├── permission_utils.py       # Permission system utilities
├── permission_decorators.py  # Permission-based route decorators
├── project_validation.py     # Project business rules validation
├── simple_seed.py            # Sample data generator
├── verify_setup.py           # System verification script
├── config.py                 # Configuration settings
├── templates/                # Jinja2 templates (Arabic RTL)
├── static/css/               # RTL-optimized stylesheets
├── static/js/                # JavaScript assets
├── uploads/                  # File upload storage
├── attached_assets/          # Project documentation (Arabic)
└── instance/                 # Database files
```

## User Roles

### General Admin (`GENERAL_ADMIN`)
- Full system access
- User management
- System configuration
- All CRUD operations

### Project Manager (`PROJECT_MANAGER`)
- Limited to assigned projects
- Employee and dog management within projects
- Reports and analytics
- Project-specific operations

## Security Features

- Flask-Login session management
- Password hashing with Werkzeug
- CSRF protection
- Input validation and sanitization
- Audit logging for all operations
- Role-based access control

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout

### Dogs Management
- `GET /dogs` - List all dogs
- `POST /dogs` - Create new dog
- `GET /dogs/<id>` - Get dog details
- `PUT /dogs/<id>` - Update dog
- `DELETE /dogs/<id>` - Delete dog

### Employees Management
- `GET /employees` - List all employees
- `POST /employees` - Create new employee
- `GET /employees/<id>` - Get employee details
- `PUT /employees/<id>` - Update employee

### Projects Management
- `GET /projects` - List all projects
- `POST /projects` - Create new project
- `GET /projects/<id>` - Get project details
- `PUT /projects/<id>` - Update project

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - PostgreSQL database should auto-configure via environment variables
   - Check that DATABASE_URL is properly set
   - Restart the application to recreate database connections

2. **Permission Access Issues**
   - Ensure PROJECT_MANAGER users have proper SubPermission grants
   - Run admin dashboard to assign granular permissions
   - Check that project assignments are properly configured

3. **Missing Dependencies**
   - Dependencies auto-install from `pyproject.toml` in Replit
   - For local: `pip install flask flask-sqlalchemy flask-login flask-migrate gunicorn psycopg2-binary reportlab werkzeug email-validator`

4. **Arabic Font Issues**
   - Ensure internet connection for Google Fonts (Noto Sans Arabic)
   - Check Bootstrap RTL CSS loading
   - Verify RTL layout is properly configured

### Getting Help

1. Check the application logs in Replit console
2. Verify database file permissions
3. Ensure all environment variables are set correctly

## License

This project is proprietary software developed for K9 operations management.

## Contributors

- System designed for Arabic-speaking K9 units
- Built with Flask, SQLAlchemy, and Bootstrap 5 RTL
- Optimized for Replit deployment

---

**Last Updated**: August 2025