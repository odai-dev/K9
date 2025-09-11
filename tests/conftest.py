import pytest
import os
from datetime import datetime, date, timedelta
from flask import Flask
from flask_login import login_user

# Import the app and database
from app import app, db
from k9.models.models import (
    User, Project, Dog, FeedingLog, SubPermission, UserRole, 
    PermissionType, BodyConditionScale, PrepMethod, DogGender
)
from werkzeug.security import generate_password_hash


@pytest.fixture(scope='session')
def app_instance():
    """Create application instance for testing"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='function')
def client(app_instance):
    """Create test client"""
    return app_instance.test_client()


@pytest.fixture(scope='function')
def db_session(app_instance):
    """Create database session for testing"""
    with app_instance.app_context():
        # Clean up any existing data
        db.session.query(FeedingLog).delete()
        db.session.query(Dog).delete()
        db.session.query(Project).delete()
        db.session.query(SubPermission).delete()
        db.session.query(User).delete()
        db.session.commit()
        yield db.session
        db.session.rollback()


@pytest.fixture(scope='function')
def test_user(db_session):
    """Create test user with PROJECT_MANAGER role"""
    user = User(
        username='test_manager',
        email='manager@test.com',
        password_hash=generate_password_hash('testpass123'),
        full_name='Test Manager',
        role=UserRole.PROJECT_MANAGER,
        active=True
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def test_project(db_session, test_user):
    """Create test project"""
    project = Project(
        name='Test K9 Project',
        code='TK9P001',
        description='Test project for feeding reports',
        start_date=date.today() - timedelta(days=30),
        manager_id=test_user.id
    )
    db.session.add(project)
    db.session.commit()
    return project


@pytest.fixture(scope='function')
def test_dogs(db_session, test_project):
    """Create test dogs"""
    dogs = []
    for i in range(3):
        dog = Dog(
            code=f'K9-{i+1:03d}',
            name=f'Test Dog {i+1}',
            breed='German Shepherd',
            birth_date=date(2020, 1, 1),
            gender=DogGender.MALE if i % 2 == 0 else DogGender.FEMALE
        )
        db.session.add(dog)
        dogs.append(dog)
    
    db.session.commit()
    return dogs


@pytest.fixture(scope='function')
def test_feeding_logs(db_session, test_dogs, test_project):
    """Create test feeding logs"""
    logs = []
    base_date = date.today()
    
    for day_offset in range(7):  # Create data for a week
        test_date = base_date - timedelta(days=day_offset)
        
        for i, dog in enumerate(test_dogs):
            # Morning meal
            morning_log = FeedingLog(
                project_id=test_project.id,
                dog_id=dog.id,
                date=test_date,
                time=datetime.strptime('08:00:00', '%H:%M:%S').time(),
                meal_name=f'إفطار كلب {dog.name}',
                grams=500 + (i * 100),
                water_ml=250 + (i * 50),
                meal_type_fresh=True,
                meal_type_dry=False,
                prep_method=PrepMethod.BOILED,
                body_condition=BodyConditionScale.IDEAL if i == 0 else BodyConditionScale.ABOVE_IDEAL,
                supplements=['فيتامين د', 'أوميجا 3'] if i == 0 else [],
                notes=f'وجبة صباحية لـ {dog.name}'
            )
            db.session.add(morning_log)
            logs.append(morning_log)
            
            # Evening meal  
            evening_log = FeedingLog(
                project_id=test_project.id,
                dog_id=dog.id,
                date=test_date,
                time=datetime.strptime('18:00:00', '%H:%M:%S').time(),
                meal_name=f'عشاء كلب {dog.name}',
                grams=400 + (i * 80),
                water_ml=200 + (i * 40),
                meal_type_fresh=False,
                meal_type_dry=True,
                prep_method=PrepMethod.STEAMED,
                body_condition=BodyConditionScale.THIN if i == 2 else BodyConditionScale.IDEAL,
                supplements=['بروتين'] if i == 1 else [],
                notes=f'وجبة مسائية لـ {dog.name}'
            )
            db.session.add(evening_log)
            logs.append(evening_log)
    
    db.session.commit()
    return logs


@pytest.fixture(scope='function')
def authenticated_client(client, test_user):
    """Create authenticated test client"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
    return client


@pytest.fixture(scope='function')
def admin_user(db_session):
    """Create admin user for permission testing"""
    user = User(
        username='admin_user',
        email='admin@test.com',
        password_hash=generate_password_hash('adminpass123'),
        full_name='Admin User',
        role=UserRole.GENERAL_ADMIN,
        active=True
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def unauthorized_user(db_session):
    """Create user without permissions for testing"""
    user = User(
        username='no_permissions',
        email='noperm@test.com',
        password_hash=generate_password_hash('nopass123'),
        full_name='No Permissions User',
        role=UserRole.PROJECT_MANAGER,  # Will be restricted via SubPermission
        active=True
    )
    db.session.add(user)
    db.session.commit()
    return user