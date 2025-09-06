# K9 Operations Management System - Developer Onboarding Guide

## Welcome to the K9 Operations Team! 🐕

This guide will help you get up and running with the K9 Operations Management System development environment quickly and efficiently.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Setup](#quick-setup)
3. [Development Workflow](#development-workflow)
4. [First Day Tasks](#first-day-tasks)
5. [Code Guidelines](#code-guidelines)
6. [Resources and Documentation](#resources-and-documentation)
7. [Getting Help](#getting-help)

## Prerequisites

### Required Software

Before starting, ensure you have the following installed:

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **PostgreSQL 15+** - [Download](https://www.postgresql.org/download/)
- **Git** - [Download](https://git-scm.com/downloads)
- **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop)
- **Visual Studio Code** (recommended) - [Download](https://code.visualstudio.com/)

### System Requirements

- **OS**: Linux, macOS, or Windows with WSL2
- **RAM**: Minimum 8GB (16GB recommended)
- **Disk Space**: At least 10GB free space
- **Network**: Internet connection for downloading dependencies

### Accounts Needed

- GitHub account with access to the repository
- Development database credentials (will be provided)
- Docker Hub account (for pushing images, if applicable)

## Quick Setup

### Option 1: Docker Setup (Recommended for Beginners)

```bash
# 1. Clone the repository
git clone <repository-url>
cd k9-operations

# 2. Copy environment file
cp .env.example .env
# Edit .env with your settings

# 3. Start the development environment
docker-compose up --build

# 4. Create admin user (in another terminal)
docker-compose exec web python scripts/create_admin_user.py

# 5. Open your browser
open http://localhost:5000
```

### Option 2: Local Development Setup

```bash
# 1. Clone and setup Python environment
git clone <repository-url>
cd k9-operations
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -e .

# 3. Setup database
createdb k9operations
export DATABASE_URL="postgresql://username:password@localhost:5432/k9operations"
export SESSION_SECRET="your-secret-key-here"

# 4. Run migrations
flask db upgrade

# 5. Create admin user
python scripts/create_admin_user.py

# 6. Start development server
flask run --debug
```

## Development Workflow

### Daily Workflow

1. **Pull Latest Changes**
   ```bash
   git pull origin main
   ```

2. **Check for Dependencies**
   ```bash
   pip install -e .  # If pyproject.toml changed
   ```

3. **Run Database Migrations**
   ```bash
   flask db upgrade
   ```

4. **Start Development Server**
   ```bash
   # Docker
   docker-compose up
   
   # Local
   flask run --debug
   ```

### Feature Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Write code following our guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   # Run tests
   pytest
   
   # Check code style
   black k9/ tests/
   flake8 k9/ tests/
   
   # Test in browser
   open http://localhost:5000
   ```

4. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**
   - Open GitHub and create a pull request
   - Fill out the PR template
   - Request review from team members

## First Day Tasks

### Task 1: Verify Setup (30 minutes)

1. ✅ Successfully start the application
2. ✅ Login with admin credentials
3. ✅ Navigate through all main sections:
   - Dashboard
   - Dogs Management
   - Employee Management
   - Projects
   - Training
   - Veterinary
   - Breeding
   - Attendance
   - Reports

### Task 2: Create Your First Dog Record (15 minutes)

1. Navigate to Dogs → Add New Dog
2. Fill in the form with test data:
   - Name: "Test Dog 001"
   - Microchip ID: "TEST001"
   - Breed: "German Shepherd"
   - Status: "Training"
3. Save and verify the record appears in the dogs list

### Task 3: Explore the Codebase (45 minutes)

1. **Read the project structure**
   ```
   k9/
   ├── api/          # REST API endpoints
   ├── models/       # Database models
   ├── routes/       # Web page routes
   ├── services/     # Business logic
   ├── templates/    # HTML templates
   ├── static/       # CSS, JS, images
   └── utils/        # Helper functions
   ```

2. **Examine key files:**
   - `app.py` - Application factory
   - `k9/models/models.py` - Database models
   - `k9/routes/main.py` - Main routes
   - `k9/templates/base.html` - Base template

3. **Study one complete feature flow:**
   - Model: `Dog` class in `models.py`
   - API: Dog endpoints in `api/api_routes.py`
   - Routes: Dog routes in `routes/main.py`
   - Templates: Dog templates in `templates/dogs/`

### Task 4: Make Your First Code Change (30 minutes)

1. **Add a new field to the Dog model**
   ```python
   # In k9/models/models.py, add to Dog class:
   nickname = db.Column(db.String(50), nullable=True)
   ```

2. **Create a migration**
   ```bash
   flask db revision --autogenerate -m "Add nickname field to Dog"
   flask db upgrade
   ```

3. **Update the form and template**
   - Add nickname field to dog form
   - Display nickname in dog list

4. **Test your changes**
   - Restart the server
   - Add a new dog with a nickname
   - Verify it saves and displays correctly

### Task 5: Write Your First Test (20 minutes)

1. **Create a test file** (if not exists): `tests/test_dogs.py`
2. **Write a simple test:**
   ```python
   def test_dog_with_nickname():
       dog = Dog(
           name="Test Dog",
           microchip_id="TEST123",
           nickname="Buddy"
       )
       db.session.add(dog)
       db.session.commit()
       
       assert dog.nickname == "Buddy"
   ```

3. **Run the test:**
   ```bash
   pytest tests/test_dogs.py::test_dog_with_nickname -v
   ```

## Code Guidelines

### Python Code Style

We follow PEP 8 with these specific guidelines:

```python
# Good: Clear, descriptive names
def create_training_session(dog_id, trainer_id, category):
    """Create a new training session record."""
    pass

# Good: Type hints
def get_dog_by_id(dog_id: str) -> Optional[Dog]:
    return Dog.query.get(dog_id)

# Good: Docstrings
class TrainingService:
    """Service for managing training sessions."""
    
    def schedule_session(self, dog: Dog, trainer: Employee) -> TrainingSession:
        """Schedule a new training session.
        
        Args:
            dog: The dog to be trained
            trainer: The trainer conducting the session
            
        Returns:
            The created training session record
        """
        pass
```

### Database Models

```python
# Good: Clear model with proper relationships
class Dog(db.Model):
    __tablename__ = 'dogs'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    name = db.Column(db.String(100), nullable=False)
    microchip_id = db.Column(db.String(15), unique=True, nullable=False)
    
    # Relationships
    assignments = db.relationship('DogAssignment', backref='dog', lazy='dynamic')
    training_sessions = db.relationship('TrainingSession', backref='dog')
    
    def __repr__(self):
        return f'<Dog {self.name}>'
```

### API Endpoints

```python
# Good: Consistent API structure
@api_bp.route('/dogs', methods=['POST'])
@require_permission('dogs.create')
def create_dog():
    """Create a new dog record."""
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'Name is required'}), 400
        
        # Create dog
        dog = Dog(
            name=data['name'],
            microchip_id=data['microchip_id']
        )
        db.session.add(dog)
        db.session.commit()
        
        # Log action
        log_audit(
            user_id=current_user.id,
            action='CREATE',
            target_type='Dog',
            target_id=dog.id
        )
        
        return jsonify({
            'success': True,
            'data': {'id': dog.id, 'name': dog.name}
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
```

### Frontend Code

```javascript
// Good: Consistent AJAX pattern
async function createDog(dogData) {
    try {
        const response = await fetch('/api/dogs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'include',
            body: JSON.stringify(dogData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('Dog created successfully!');
            window.location.reload();
        } else {
            showError(result.error);
        }
    } catch (error) {
        showError('Failed to create dog: ' + error.message);
    }
}
```

### Template Guidelines

```html
<!-- Good: Semantic HTML with proper Arabic support -->
<div class="card">
    <div class="card-header">
        <h5 class="card-title">{{ _('Dog Information') }}</h5>
    </div>
    <div class="card-body">
        <div class="row">
            <div class="col-md-6">
                <label class="form-label">{{ _('Name') }}</label>
                <input type="text" class="form-control" name="name" 
                       value="{{ dog.name if dog else '' }}" required>
            </div>
            <div class="col-md-6">
                <label class="form-label">{{ _('Microchip ID') }}</label>
                <input type="text" class="form-control" name="microchip_id" 
                       value="{{ dog.microchip_id if dog else '' }}" required>
            </div>
        </div>
    </div>
</div>
```

## Resources and Documentation

### Essential Reading

1. **[Developer Guide](DEVELOPER_GUIDE.md)** - Complete technical documentation
2. **[Database ERD](DATABASE_ERD.md)** - Database schema and relationships
3. **[API Reference](API_REFERENCE.md)** - API endpoint documentation
4. **[Deployment Guide](../DEPLOYMENT.md)** - Production deployment instructions

### External Resources

- **Flask Documentation**: https://flask.palletsprojects.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Bootstrap 5 RTL**: https://getbootstrap.com/docs/5.3/getting-started/rtl/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/

### Tools and Extensions

**VS Code Extensions:**
- Python
- Flask-Snippets
- SQLAlchemy Stubs
- Docker
- GitLens
- Arabic Language Pack

**Useful Commands:**
```bash
# Database
flask db current        # Show current migration
flask db history        # Show migration history
flask db show <revision>  # Show specific migration

# Development
flask routes           # Show all routes
flask shell           # Interactive Python shell
pytest --cov         # Run tests with coverage

# Docker
docker-compose logs web     # View application logs
docker-compose exec web bash  # Shell into container
docker-compose down -v      # Stop and remove volumes
```

## Getting Help

### Team Communication

- **Daily Standups**: 9:00 AM (discuss progress and blockers)
- **Code Reviews**: All pull requests require one approval
- **Technical Questions**: Use team chat or GitHub discussions
- **Architecture Decisions**: Discuss in team meetings

### Debugging Resources

1. **Application Logs**
   ```bash
   # View real-time logs
   docker-compose logs -f web
   
   # View specific service logs
   docker-compose logs nginx
   docker-compose logs db
   ```

2. **Database Access**
   ```bash
   # Connect to database
   docker-compose exec db psql -U k9user -d k9operations
   
   # Or from host (if PostgreSQL client installed)
   psql postgresql://k9user:password@localhost:5432/k9operations
   ```

3. **Python Debugging**
   ```python
   # Add breakpoints in code
   import pdb; pdb.set_trace()
   
   # Or use Flask shell for interactive debugging
   flask shell
   ```

### Common Issues and Solutions

**Issue: Import errors**
```bash
# Solution: Reinstall in development mode
pip install -e .
```

**Issue: Database connection errors**
```bash
# Solution: Check if PostgreSQL is running
docker-compose ps db
docker-compose logs db
```

**Issue: Permission denied errors**
```bash
# Solution: Fix file permissions
sudo chown -R $USER:$USER .
```

**Issue: Port already in use**
```bash
# Solution: Stop conflicting services
docker-compose down
sudo lsof -i :5000  # Find what's using port 5000
```

### Questions and Support

- **Immediate Help**: Ask in team chat
- **Code Review**: Create PR and request review
- **Bug Reports**: Create GitHub issue with reproduction steps
- **Feature Requests**: Discuss in team meeting first

### Learning Path

**Week 1**: Setup and basic understanding
- Complete onboarding tasks
- Understand project structure
- Make first code contribution

**Week 2**: Deep dive into features
- Work on assigned feature/bug
- Write comprehensive tests
- Learn deployment process

**Week 3**: Advanced topics
- Performance optimization
- Security considerations
- Arabic localization

**Month 1 Goal**: Independently develop features end-to-end

---

## Conclusion

Welcome to the team! This system manages critical K9 operations for military and police units. Your contributions help ensure the safety and effectiveness of these important operations.

Take your time to understand the system thoroughly, ask questions freely, and don't hesitate to suggest improvements. We're here to support your success!

**Next Steps:**
1. Complete the first day tasks
2. Schedule a code walkthrough with a senior team member
3. Pick up your first assigned issue
4. Join the team for daily standup tomorrow

Happy coding! 🐕‍🦺