# K9 Operations Management System - Developer Guide

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Development Environment Setup](#development-environment-setup)
4. [Project Structure](#project-structure)
5. [Database Schema](#database-schema)
6. [API Documentation](#api-documentation)
7. [Frontend Development](#frontend-development)
8. [Security Guidelines](#security-guidelines)
9. [Testing](#testing)
10. [Deployment](#deployment)
11. [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (for containerized development)
- Node.js 18+ (for frontend asset building, optional)

### Local Development Setup

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd k9-operations
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

2. **Database Setup**
   ```bash
   # Create PostgreSQL database
   createdb k9operations
   
   # Set environment variables
   export DATABASE_URL="postgresql://username:password@localhost:5432/k9operations"
   export SESSION_SECRET="your-secret-key-here"
   
   # Run migrations
   flask db upgrade
   
   # Create admin user
   python scripts/create_admin_user.py
   ```

3. **Run Development Server**
   ```bash
   flask run --debug
   # Or with Gunicorn
   gunicorn --bind 0.0.0.0:5000 --reload main:app
   ```

### Docker Development

```bash
# Development with auto-reload
docker-compose up --build

# Production build
docker-compose -f docker-compose.production.yml up --build
```

## Architecture Overview

### System Architecture

The K9 Operations Management System follows a modular Flask application architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │  Flask App      │    │   PostgreSQL    │
│   (SSL/Static)  │◄──►│  (Python 3.11) │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                    ┌─────────────────┐
                    │   File Storage  │
                    │   (Uploads)     │
                    └─────────────────┘
```

### Technology Stack

- **Backend**: Flask 3.0+, SQLAlchemy 2.0+, PostgreSQL 15+
- **Frontend**: Bootstrap 5 RTL, Arabic font support
- **Security**: Flask-Login, CSRF protection, audit logging
- **Deployment**: Docker multi-stage builds, Nginx reverse proxy
- **Database**: PostgreSQL with full-text search, JSON fields, UUIDs

### Key Design Principles

1. **Security First**: Role-based access control, audit logging, input validation
2. **Arabic RTL Support**: Full right-to-left UI and PDF generation
3. **Modular Architecture**: Blueprint-based organization, clear separation of concerns
4. **Production Ready**: Containerized deployment, health checks, monitoring

## Development Environment Setup

### IDE Configuration

**VS Code Recommended Extensions:**
- Python
- Flask-Snippets
- SQLAlchemy Stubs
- Docker
- HTML CSS Support

**VS Code Settings:**
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"]
}
```

### Environment Variables

Create a `.env` file for local development:

```bash
# Database
DATABASE_URL=postgresql://k9user:password@localhost:5432/k9operations
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=k9user
POSTGRES_PASSWORD=password
POSTGRES_DB=k9operations

# Flask
FLASK_ENV=development
FLASK_APP=app.py
SESSION_SECRET=your-development-secret-key

# Features
DEBUG=True
TESTING=False

# File Upload
MAX_CONTENT_LENGTH=16777216  # 16MB
UPLOAD_FOLDER=uploads

# Security
WTF_CSRF_ENABLED=True
WTF_CSRF_TIME_LIMIT=3600
```

## Project Structure

```
k9-operations/
├── app.py                    # Flask application factory
├── main.py                   # Application entry point
├── config.py                 # Configuration classes
├── pyproject.toml           # Python dependencies
├── docker-compose.yml       # Development containers
├── docker-compose.production.yml  # Production containers
├── Dockerfile               # Simple container build
├── Dockerfile.multistage    # Optimized production build
│
├── k9/                      # Main application package
│   ├── __init__.py
│   ├── api/                 # REST API endpoints
│   │   ├── api_routes.py    # Main API routes
│   │   ├── attendance_reporting_api.py
│   │   ├── pm_daily_api.py
│   │   └── ...
│   ├── models/              # Database models
│   │   ├── models.py        # Core models (User, Dog, Employee, etc.)
│   │   └── models_attendance_reporting.py
│   ├── routes/              # Web routes (HTML endpoints)
│   │   ├── main.py          # Dashboard and core routes
│   │   ├── auth.py          # Authentication routes
│   │   ├── admin_routes.py  # Admin panel
│   │   └── ...
│   ├── services/            # Business logic layer
│   │   ├── attendance_service.py
│   │   ├── pm_daily_services.py
│   │   └── ...
│   ├── templates/           # Jinja2 HTML templates
│   │   ├── base.html        # Base layout
│   │   ├── dashboard.html   # Main dashboard
│   │   ├── auth/            # Authentication pages
│   │   ├── dogs/            # Dog management
│   │   ├── employees/       # Employee management
│   │   └── ...
│   ├── static/              # Static assets
│   │   ├── css/style.css    # Main stylesheet
│   │   ├── js/              # JavaScript files
│   │   ├── fonts/           # Arabic fonts
│   │   └── img/             # Images
│   └── utils/               # Utility functions
│       ├── utils.py         # General utilities
│       ├── pdf_rtl.py       # Arabic PDF generation
│       ├── permission_utils.py  # Permission helpers
│       └── security_utils.py    # Security functions
│
├── migrations/              # Database migrations
├── scripts/                 # Utility scripts
├── docs/                    # Documentation
├── tests/                   # Test suite
├── nginx/                   # Nginx configuration
└── uploads/                 # File uploads (development)
```

### Module Organization

**API Layer** (`k9/api/`):
- RESTful endpoints for AJAX requests
- JSON responses
- Rate limiting and validation

**Routes Layer** (`k9/routes/`):
- HTML page rendering
- Form handling
- Session management

**Services Layer** (`k9/services/`):
- Business logic
- Database operations
- External integrations

**Models Layer** (`k9/models/`):
- SQLAlchemy models
- Database schema definitions
- Relationships and constraints

## Database Schema

### Core Entities

1. **User Management**
   - `User`: System users (admin, project managers)
   - `Employee`: K9 unit personnel
   - `UserRole`: GENERAL_ADMIN, PROJECT_MANAGER

2. **K9 Management**
   - `Dog`: Individual dogs with status tracking
   - `DogAssignment`: Project assignments
   - `DogStatus`: ACTIVE, RETIRED, DECEASED, TRAINING

3. **Training System**
   - `TrainingSession`: Individual training records
   - `TrainingCategory`: Obedience, Detection, etc.

4. **Veterinary Care**
   - `VeterinaryVisit`: Health checkups and treatments
   - `VisitType`: ROUTINE, EMERGENCY, VACCINATION

5. **Project Operations**
   - `Project`: Operational missions
   - `ProjectStatus`: PLANNED, ACTIVE, COMPLETED, CANCELLED
   - `Incident`: Security incidents
   - `Suspicion`: Suspicious activities

6. **Breeding Program**
   - `MaturityRecord`: Dog maturity tracking
   - `HeatCycle`: Female dog heat cycles
   - `MatingRecord`: Breeding records
   - `PregnancyRecord`: Pregnancy monitoring
   - `DeliveryRecord`: Birth records
   - `Puppy`: Offspring management

7. **Attendance System**
   - `AttendanceShift`: Work shifts
   - `Attendance`: Daily attendance records
   - `AttendanceStatus`: PRESENT, ABSENT, LATE, etc.

### Database Relationships

```mermaid
erDiagram
    User ||--o{ Project : manages
    Project ||--o{ DogAssignment : contains
    Dog ||--o{ DogAssignment : assigned_to
    Dog ||--o{ TrainingSession : receives
    Dog ||--o{ VeterinaryVisit : undergoes
    Employee ||--o{ TrainingSession : conducts
    Employee ||--o{ Attendance : has
    Project ||--o{ Attendance : tracks
```

### Key Design Decisions

1. **UUID Primary Keys**: For security and distributed systems
2. **Enum Types**: Consistent status values across entities
3. **JSON Fields**: Flexible metadata storage
4. **Audit Logging**: Complete action history
5. **Soft Deletes**: Data preservation for historical records

## API Documentation

### Authentication

All API endpoints require authentication via session cookies:

```javascript
// Login required for all API calls
fetch('/api/dogs', {
  method: 'GET',
  credentials: 'include',  // Include session cookie
  headers: {
    'X-CSRFToken': getCSRFToken()  // CSRF protection
  }
})
```

### Common Endpoints

#### Dogs API
- `GET /api/dogs` - List all dogs
- `POST /api/dogs` - Create new dog
- `GET /api/dogs/{id}` - Get dog details
- `PUT /api/dogs/{id}` - Update dog
- `DELETE /api/dogs/{id}` - Remove dog

#### Projects API
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `GET /api/projects/{id}/assignments` - Get project assignments

#### Training API
- `POST /api/training` - Record training session
- `GET /api/training/statistics` - Training statistics

### Response Format

```json
{
  "success": true,
  "data": {
    "id": "uuid-here",
    "name": "Dog Name",
    "status": "ACTIVE"
  },
  "message": "Operation completed successfully"
}
```

### Error Handling

```json
{
  "success": false,
  "error": "validation_error",
  "message": "Name is required",
  "details": {
    "field": "name",
    "code": "required"
  }
}
```

## Frontend Development

### CSS Architecture

The frontend uses Bootstrap 5 with RTL support:

```css
/* Main stylesheet: k9/static/css/style.css */

/* RTL Layout */
[dir="rtl"] {
  text-align: right;
}

/* Arabic Typography */
.arabic-text {
  font-family: 'Noto Sans Arabic', sans-serif;
  line-height: 1.8;
}

/* Custom Components */
.k9-card {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
```

### JavaScript Patterns

**AJAX Requests:**
```javascript
// Utility function for API calls
async function apiRequest(url, options = {}) {
  const response = await fetch(url, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken(),
      ...options.headers
    },
    ...options
  });
  
  return response.json();
}

// Usage
const dogs = await apiRequest('/api/dogs');
```

**Form Handling:**
```javascript
// Enhanced form submission with validation
class K9Form {
  constructor(formElement) {
    this.form = formElement;
    this.setupValidation();
  }
  
  async submit() {
    if (!this.validate()) return;
    
    try {
      const result = await apiRequest(this.form.action, {
        method: this.form.method,
        body: new FormData(this.form)
      });
      
      this.showSuccess(result.message);
    } catch (error) {
      this.showError(error.message);
    }
  }
}
```

### Template Patterns

**Base Template Structure:**
```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}K9 Operations{% endblock %}</title>
  
  <!-- Bootstrap RTL CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
  
  <!-- Arabic Fonts -->
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@300;400;500;700&display=swap" rel="stylesheet">
  
  <!-- Custom CSS -->
  <link href="{{ url_for('static', filename='css/style.css') }}" rel="stylesheet">
  
  {% block extra_css %}{% endblock %}
</head>
<body>
  <!-- Navigation -->
  {% include 'navigation.html' %}
  
  <!-- Main Content -->
  <main class="container-fluid">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="alert alert-{{ 'danger' if category == 'error' else category }}">
            {{ message }}
          </div>
        {% endfor %}
      {% endif %}
    {% endwith %}
    
    {% block content %}{% endblock %}
  </main>
  
  <!-- Scripts -->
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  <script src="{{ url_for('static', filename='js/main.js') }}"></script>
  {% block extra_js %}{% endblock %}
</body>
</html>
```

## Security Guidelines

### Authentication & Authorization

1. **Session Management**
   - Secure session cookies
   - Session timeout configuration
   - CSRF protection on all forms

2. **Role-Based Access Control**
   ```python
   from k9.utils.permission_decorators import require_permission
   
   @app.route('/admin/users')
   @require_permission('admin.users.view')
   def admin_users():
       return render_template('admin/users.html')
   ```

3. **Input Validation**
   ```python
   from flask_wtf import FlaskForm
   from wtforms import StringField, validators
   
   class DogForm(FlaskForm):
       name = StringField('Name', [
           validators.Length(min=1, max=100),
           validators.Regexp(r'^[a-zA-Z\u0600-\u06FF\s]+$')
       ])
   ```

### Data Protection

1. **SQL Injection Prevention**
   - Always use SQLAlchemy ORM
   - Parameterized queries only
   - Input sanitization

2. **File Upload Security**
   ```python
   ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
   
   def allowed_file(filename):
       return '.' in filename and \
              filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
   ```

3. **Audit Logging**
   ```python
   from k9.utils.utils import log_audit
   
   # Log all significant actions
   log_audit(
       user_id=current_user.id,
       action='CREATE',
       target_type='Dog',
       target_id=dog.id,
       details={'name': dog.name}
   )
   ```

### Production Security

1. **HTTPS Only**
   - Force SSL in production
   - HSTS headers
   - Secure cookie flags

2. **Rate Limiting**
   - API endpoint limits
   - Login attempt protection
   - File upload restrictions

3. **Security Headers**
   ```python
   @app.after_request
   def security_headers(response):
       response.headers['X-Frame-Options'] = 'DENY'
       response.headers['X-Content-Type-Options'] = 'nosniff'
       response.headers['X-XSS-Protection'] = '1; mode=block'
       return response
   ```

## Testing

### Test Structure

```
tests/
├── conftest.py              # Pytest configuration
├── test_models.py           # Database model tests
├── test_api.py              # API endpoint tests
├── test_auth.py             # Authentication tests
├── test_permissions.py      # Permission system tests
└── integration/             # Integration tests
    ├── test_workflows.py
    └── test_deployment.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=k9 --cov-report=html

# Run specific test file
pytest tests/test_models.py

# Run with debugging
pytest -v -s tests/test_api.py::test_dog_creation
```

### Test Examples

**Model Testing:**
```python
def test_dog_creation():
    dog = Dog(
        name="Test Dog",
        microchip_id="123456789",
        status=DogStatus.ACTIVE
    )
    db.session.add(dog)
    db.session.commit()
    
    assert dog.id is not None
    assert dog.created_at is not None
```

**API Testing:**
```python
def test_dog_api_endpoint(client, auth_headers):
    response = client.post('/api/dogs', 
        json={'name': 'Test Dog', 'microchip_id': '123456789'},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    assert response.json['success'] is True
```

## Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   # Generate SSL certificates
   ./scripts/ssl/setup-letsencrypt.sh yourdomain.com admin@yourdomain.com
   
   # Set production environment variables
   export FLASK_ENV=production
   export DATABASE_URL="postgresql://user:pass@db:5432/k9operations"
   export SESSION_SECRET="$(openssl rand -base64 32)"
   ```

2. **Container Deployment**
   ```bash
   # Build and deploy
   docker-compose -f docker-compose.production.yml up -d --build
   
   # Monitor logs
   docker-compose -f docker-compose.production.yml logs -f
   
   # Scale application
   docker-compose -f docker-compose.production.yml up -d --scale web=3
   ```

3. **Database Migrations**
   ```bash
   # Run migrations in production
   docker-compose -f docker-compose.production.yml exec web flask db upgrade
   
   # Create admin user
   docker-compose -f docker-compose.production.yml exec web python scripts/create_admin_user.py
   ```

### Health Monitoring

1. **Application Health Checks**
   - `/health` endpoint for load balancer
   - Database connectivity checks
   - File system access verification

2. **Log Management**
   ```bash
   # Application logs
   docker-compose logs web
   
   # Nginx access logs
   docker-compose logs nginx
   
   # Database logs
   docker-compose logs db
   ```

3. **Backup Strategy**
   ```bash
   # Manual backup
   docker-compose exec backup ./backup.sh
   
   # Automated backups (crontab)
   0 2 * * * docker-compose -f /path/to/docker-compose.production.yml exec backup ./backup.sh
   ```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database status
   docker-compose ps db
   
   # Check database logs
   docker-compose logs db
   
   # Test connection
   docker-compose exec web python -c "from app import db; print(db.engine.execute('SELECT 1').scalar())"
   ```

2. **Permission Errors**
   ```bash
   # Check file permissions
   ls -la uploads/
   
   # Fix ownership
   docker-compose exec web chown -R k9user:k9user /app/uploads
   ```

3. **SSL Certificate Issues**
   ```bash
   # Check certificate validity
   openssl x509 -in nginx/ssl/server.crt -text -noout
   
   # Test SSL connection
   openssl s_client -connect yourdomain.com:443
   ```

### Performance Optimization

1. **Database Optimization**
   ```sql
   -- Add indexes for common queries
   CREATE INDEX idx_dogs_status ON dogs(status);
   CREATE INDEX idx_attendance_date ON attendance(date);
   
   -- Analyze query performance
   EXPLAIN ANALYZE SELECT * FROM dogs WHERE status = 'ACTIVE';
   ```

2. **Application Optimization**
   ```python
   # Use database pagination
   dogs = Dog.query.paginate(
       page=page, per_page=20, error_out=False
   )
   
   # Eager load relationships
   dogs = Dog.query.options(
       joinedload(Dog.assignments)
   ).all()
   ```

3. **Nginx Optimization**
   ```nginx
   # Enable compression
   gzip on;
   gzip_types text/css application/javascript;
   
   # Cache static files
   location /static/ {
       expires 1y;
       add_header Cache-Control "public, immutable";
   }
   ```

### Debug Mode

For development debugging:

```bash
# Enable Flask debug mode
export FLASK_ENV=development
export FLASK_DEBUG=1

# Enable SQL query logging
export SQLALCHEMY_ECHO=1

# Run with debug server
python -m flask run --debug --host=0.0.0.0
```

---

## Contributing

1. **Code Style**
   - Follow PEP 8 for Python code
   - Use Black for code formatting
   - Add type hints where applicable

2. **Git Workflow**
   ```bash
   # Create feature branch
   git checkout -b feature/new-feature
   
   # Make changes and commit
   git add .
   git commit -m "Add new feature: description"
   
   # Push and create pull request
   git push origin feature/new-feature
   ```

3. **Documentation**
   - Update this guide for architectural changes
   - Add docstrings for new functions
   - Update API documentation

For more information, see the [API Documentation](API_REFERENCE.md) and [Database Schema](DATABASE_SCHEMA.md).