"""
Tests for Unified Attendance Matrix functionality
"""

import pytest
import json
from datetime import date, timedelta
from app import app, db
from models import User, Employee, Project, UserRole, EmployeeRole, ProjectStatus
from models_attendance_reporting import ProjectAttendanceReporting, AttendanceStatus


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture
def auth_headers(client):
    """Create authenticated user and return auth headers"""
    with app.app_context():
        # Create test admin user
        admin = User()
        admin.username = 'test_admin'
        admin.email = 'admin@test.com'
        admin.password_hash = 'hashed_password'
        admin.role = UserRole.GENERAL_ADMIN
        admin.full_name = 'Test Admin'
        admin.active = True
        db.session.add(admin)
        db.session.commit()
        
        # Login (simplified for testing)
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True
    
    return {}


def test_unified_matrix_ui_route(client, auth_headers):
    """Test that the unified matrix UI route loads"""
    response = client.get('/reports/attendance/unified')
    
    # Should redirect to login if not authenticated
    # In a real test, you'd mock authentication
    assert response.status_code in [200, 302]


def test_run_unified_matrix_api_validation(client, auth_headers):
    """Test API validation for unified matrix"""
    # Test missing JSON body
    response = client.post('/api/reports/attendance/run/unified')
    assert response.status_code == 400
    
    # Test missing required fields
    response = client.post('/api/reports/attendance/run/unified',
                          json={})
    assert response.status_code == 400
    
    # Test invalid date format
    response = client.post('/api/reports/attendance/run/unified',
                          json={'date_from': 'invalid', 'date_to': 'invalid'})
    assert response.status_code == 400


def test_date_range_validation(client, auth_headers):
    """Test date range validation"""
    today = date.today()
    future_date = today + timedelta(days=70)  # Over 62 days limit
    
    response = client.post('/api/reports/attendance/run/unified',
                          json={
                              'date_from': today.strftime('%Y-%m-%d'),
                              'date_to': future_date.strftime('%Y-%m-%d')
                          })
    
    if response.status_code == 200:
        data = json.loads(response.data)
        # Should return error for date range over 62 days
        assert 'error' in data


def create_test_data():
    """Create test data for matrix testing"""
    # Create employees
    employees = []
    for i in range(4):
        emp = Employee()
        emp.name = f'Employee {i+1}'
        emp.employee_id = f'EMP{i+1:03d}'
        emp.role = EmployeeRole.HANDLER
        emp.hire_date = date.today()
        emp.is_active = True
        employees.append(emp)
        db.session.add(emp)
    
    # Create project
    project = Project()
    project.name = 'Test Project'
    project.code = 'TEST001'
    project.status = ProjectStatus.ACTIVE
    project.start_date = date.today()
    db.session.add(project)
    
    db.session.commit()
    
    # Create attendance data
    test_date = date.today()
    
    # Employee 1: project-controlled attendance (should be excluded)
    for i in range(3):
        attendance = ProjectAttendanceReporting()
        attendance.date = test_date + timedelta(days=i)
        attendance.project_id = project.id
        attendance.employee_id = employees[0].id
        attendance.status = AttendanceStatus.PRESENT
        attendance.is_project_controlled = True
        db.session.add(attendance)
    
    # Employee 2: unified/global attendance only
    for i in range(7):
        attendance = ProjectAttendanceReporting()
        attendance.date = test_date + timedelta(days=i)
        attendance.project_id = project.id
        attendance.employee_id = employees[1].id
        attendance.status = AttendanceStatus.PRESENT if i % 2 == 0 else AttendanceStatus.ABSENT
        attendance.is_project_controlled = False
        db.session.add(attendance)
    
    db.session.commit()
    
    return employees, project


# Note: These tests would need proper authentication mocking and database setup
# The above provides a framework for testing the unified matrix functionality