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
Dependencies are automatically installed via the `pyproject.toml` file. If needed, run:
```bash
python -m pip install -r requirements.txt
```

### 3. Database Setup
The application automatically uses SQLite for Replit compatibility:
- Database file: `k9_operations.db`
- No additional database setup required
- Tables are created automatically on first run

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

### SQLite (Default/Replit)
- Automatically used when no `DATABASE_URL` is set
- Perfect for development and Replit hosting
- Database file: `k9_operations.db`

### PostgreSQL (Production)
Set the `DATABASE_URL` environment variable:
```bash
export DATABASE_URL="postgresql://user:password@localhost/k9_operations"
```

## Important Notes for Replit Users

### UUID Compatibility
This system uses UUID identifiers for most entities. The codebase automatically handles SQLite/PostgreSQL compatibility:
- **SQLite**: UUIDs stored as strings (36 characters)
- **PostgreSQL**: Native UUID support

### File Uploads
- Upload directory: `uploads/`
- Maximum file size: 16MB
- Supported formats: PDF, JPG, PNG

### RTL Support
The interface is optimized for Arabic (RTL) layout:
- Bootstrap 5 RTL
- Noto Sans Arabic font
- Right-to-left navigation and forms

## Project Structure

```
├── app.py              # Flask application factory
├── main.py             # Application entry point
├── models.py           # Database models
├── routes.py           # Main application routes
├── api_routes.py       # API endpoints
├── auth.py             # Authentication routes
├── utils.py            # Utility functions
├── simple_seed.py      # Sample data generator
├── config.py           # Configuration settings
├── templates/          # Jinja2 templates
├── static/            # CSS, JS, and assets
└── uploads/           # File upload storage
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

1. **UUID Errors in SQLite**
   - Ensure all route handlers use string IDs, not UUID objects
   - The codebase should handle this automatically

2. **Database Creation Errors**
   - Delete existing database file: `rm k9_operations.db`
   - Restart the application

3. **Missing Dependencies**
   - Run: `pip install -r requirements.txt`
   - For Replit: dependencies auto-install from `pyproject.toml`

4. **Arabic Font Issues**
   - Ensure internet connection for Google Fonts
   - Check Bootstrap RTL CSS loading

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