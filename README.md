# K9 Operations Management System

A comprehensive web-based management system for K9 operations, built with Flask and PostgreSQL. This system handles dog management, training records, veterinary care, breeding programs, and comprehensive reporting.

## Features

- **Dog Management**: Complete dog profiles with health records and training status
- **Employee Management**: Staff management with role-based access control
- **Project Management**: Organize operations into projects with assignments
- **Training Records**: Track training sessions and progress
- **Veterinary Care**: Medical records and health monitoring
- **Breeding Program**: Mating, pregnancy, and delivery tracking
- **Attendance System**: Staff attendance with shift management
- **Comprehensive Reporting**: PDF exports with Arabic RTL support
- **Security**: Role-based permissions and secure authentication

## Technology Stack

- **Backend**: Flask (Python 3.11+)
- **Database**: PostgreSQL (production), SQLite (development)
- **Frontend**: Bootstrap 5 with RTL support for Arabic
- **PDF Generation**: ReportLab with Arabic text support
- **Authentication**: Flask-Login with secure session management
- **Migrations**: Flask-Migrate (Alembic)
- **Deployment**: Docker & Docker Compose

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (for production)
- Docker & Docker Compose (recommended)

### Option 1: Docker Deployment (Recommended)

1. **Clone and setup environment:**
   ```bash
   git clone <repository-url>
   cd k9-operations
   cp .env.example .env
   ```

2. **Configure environment variables:**
   Edit `.env` and update:
   - `POSTGRES_PASSWORD`: Set a secure password
   - `SESSION_SECRET`: Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`

3. **Deploy with Docker:**
   ```bash
   docker-compose up -d
   ```

4. **Initialize database:**
   ```bash
   docker-compose exec web flask db upgrade
   ```

5. **Create admin user:**
   ```bash
   docker-compose exec web python scripts/create_admin_user.py
   ```

6. **Access the application:**
   Open http://localhost (or your configured port)

### Option 2: Local Development Setup

1. **Setup Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

3. **Setup database:**
   ```bash
   # For PostgreSQL (recommended)
   export DATABASE_URL="postgresql://username:password@localhost/k9_operations"
   
   # Or use SQLite for development
   export DATABASE_URL="sqlite:///k9_operations.db"
   ```

4. **Initialize database:**
   ```bash
   flask db upgrade
   ```

5. **Create admin user:**
   ```bash
   python scripts/create_admin_user.py
   ```

6. **Run the application:**
   ```bash
   flask run --host=0.0.0.0 --port=5000
   ```

## Environment Variables

Key environment variables (see `.env.example` for complete list):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///k9_operations.db` |
| `SESSION_SECRET` | Secret key for sessions | Generated for development |
| `FLASK_ENV` | Environment mode | `development` |
| `POSTGRES_DB` | PostgreSQL database name | `k9operations` |
| `POSTGRES_USER` | PostgreSQL username | `k9user` |
| `POSTGRES_PASSWORD` | PostgreSQL password | **Must be changed!** |

## Project Structure

```
k9-operations/
├── app.py              # Main Flask application
├── models.py           # Database models
├── routes.py           # Web routes
├── api_routes.py       # API endpoints
├── auth.py            # Authentication logic
├── config.py          # Configuration
├── utils.py           # Utility functions
├── templates/         # HTML templates
├── static/            # CSS, JS, fonts
├── migrations/        # Database migrations
├── scripts/           # Utility scripts
├── docker/            # Docker configuration
├── Dockerfile         # Docker image definition
├── docker-compose.yml # Multi-container setup
└── .env.example       # Environment template
```

## Database Migrations

Create new migration:
```bash
flask db migrate -m "Description of changes"
```

Apply migrations:
```bash
flask db upgrade
```

Rollback migration:
```bash
flask db downgrade
```

## Security Features

- **Secure Session Cookies**: HTTPOnly, Secure, SameSite protection
- **Role-Based Access Control**: Admin and Project Manager roles
- **Environment-Based Configuration**: Separate dev/prod settings
- **PostgreSQL Enforcement**: Required for production deployments
- **Input Validation**: Comprehensive form validation
- **CSRF Protection**: Built-in Flask-WTF CSRF tokens

## User Management

### Default Admin Account
- **Username**: `admin`
- **Password**: `admin123`
- **⚠️ Important**: Change this password immediately after first login!

### Creating Additional Users
Use the admin panel to create new users with appropriate roles:
- **General Admin**: Full system access
- **Project Manager**: Limited project-specific access

## API Documentation

The system provides REST APIs for:
- Dog management (`/api/dogs/`)
- Employee management (`/api/employees/`)
- Training records (`/api/training/`)
- Attendance tracking (`/api/attendance/`)
- Report generation (`/api/reports/`)

API endpoints require authentication and appropriate permissions.

## Production Deployment

### Security Checklist
- [ ] Change default PostgreSQL password
- [ ] Generate secure SESSION_SECRET
- [ ] Change/disable default admin account
- [ ] Configure firewall for database access
- [ ] Enable SSL/TLS encryption
- [ ] Set up regular database backups
- [ ] Monitor application logs
- [ ] Use Docker secrets for sensitive values

### Performance Tuning
- Adjust `GUNICORN_WORKERS` based on server capacity
- Configure PostgreSQL connection pooling
- Set up reverse proxy (nginx) for production
- Enable gzip compression
- Configure static file serving

## Development

### Running Tests
```bash
python -m pytest
```

### Code Style
The project follows PEP 8 style guidelines. Use:
```bash
flake8 .
black .
```

### Contributing
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## Troubleshooting

### Common Issues

**Application won't start:**
- Check environment variables are set correctly
- Verify database connectivity
- Check logs for specific error messages

**Database connection errors:**
- Ensure PostgreSQL is running
- Verify connection string format
- Check network connectivity

**Permission errors:**
- Verify user roles are set correctly
- Check project assignments
- Review permission logs

### Logs
- Application logs: Check Docker logs or console output
- Database logs: PostgreSQL logs for connection/query issues
- Nginx logs: If using reverse proxy

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Check GitHub issues
4. Contact system administrator

## License

This project is proprietary software. All rights reserved.

---

**K9 Operations Management System** - Professional dog training and operations management.