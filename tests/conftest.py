import pytest
import os
from datetime import datetime, date, timedelta
from flask import Flask
from flask_login import login_user

# Import the app and database
from app import app, db
from k9.models.models import (
    User, Project, Dog, FeedingLog, SubPermission, UserRole, 
    PermissionType, BodyConditionScale, PrepMethod, DogGender,
    VeterinaryVisit, VisitType, Employee, EmployeeRole, CaretakerDailyLog,
    AuditLog
)
from werkzeug.security import generate_password_hash


@pytest.fixture(scope='session')
def app_instance():
    """Create application instance for testing
    
    WARNING: This fixture needs refactoring to use app-factory pattern.
    Currently DISABLED to prevent accidental data loss on production database.
    
    TODO: Implement create_app() factory function that accepts config
    so tests can instantiate a fresh Flask app with SQLite in-memory database.
    """
    pytest.skip("Test configuration needs refactoring - currently unsafe. "
                "Tests would run against production PostgreSQL database. "
                "Need to implement app-factory pattern first.")


@pytest.fixture(scope='function')
def client(app_instance):
    """Create test client"""
    return app_instance.test_client()


@pytest.fixture(scope='function')
def db_session(app_instance):
    """Create database session for testing"""
    with app_instance.app_context():
        # Clean up any existing data in correct order (child tables first to avoid FK violations)
        db.session.query(FeedingLog).delete()
        db.session.query(CaretakerDailyLog).delete()
        db.session.query(VeterinaryVisit).delete()
        db.session.query(SubPermission).delete()
        db.session.query(Dog).delete()
        db.session.query(Project).delete()
        db.session.query(AuditLog).delete()
        db.session.query(Employee).delete()
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


@pytest.fixture(scope='function')
def test_vet_employee(db_session):
    """Create test veterinarian employee"""
    vet = Employee(
        name='د. أحمد الطبيب البيطري',
        employee_id='VET001',
        role=EmployeeRole.VETERINARIAN,
        phone='123456789',
        email='vet@test.com',
        hire_date=date(2020, 1, 1),
        is_active=True
    )
    db.session.add(vet)
    db.session.commit()
    return vet


@pytest.fixture(scope='function')
def test_veterinary_visits(db_session, test_dogs, test_project, test_vet_employee):
    """Create test veterinary visits"""
    visits = []
    base_date = datetime.now()
    
    # Create different types of visits for testing
    for day_offset in range(7):  # Create data for a week
        visit_date = base_date - timedelta(days=day_offset)
        
        for i, dog in enumerate(test_dogs):
            # Routine checkup
            routine_visit = VeterinaryVisit(
                dog_id=dog.id,
                vet_id=test_vet_employee.id,
                project_id=test_project.id if i != 2 else None,  # Some without project
                visit_type=VisitType.ROUTINE,
                visit_date=visit_date,
                weight=25.5 + (i * 2),
                temperature=38.2 + (i * 0.3),
                heart_rate=80 + (i * 10),
                blood_pressure='120/80',
                symptoms=f'فحص روتيني لـ {dog.name}',
                diagnosis='حالة جيدة',
                treatment='لا يوجد علاج مطلوب',
                medications=[
                    {'name': 'فيتامين د', 'dose': '200 وحدة', 'duration': '7 أيام', 'frequency': 'مرة يومياً'},
                    {'name': 'مكملات غذائية', 'dose': '1 كبسولة', 'duration': '30 يوم', 'frequency': 'مع الطعام'}
                ] if i == 0 else [],
                stool_color='بني طبيعي',
                stool_consistency='طبيعية',
                urine_color='أصفر فاتح',
                vaccinations_given=['التطعيم السنوي'] if day_offset == 0 and i == 0 else [],
                next_visit_date=visit_date.date() + timedelta(days=30),
                notes=f'زيارة روتينية لفحص {dog.name} - حالة ممتازة',
                cost=150.0 + (i * 25),
                location='العيادة البيطرية',
                weather='مشمس معتدل',
                vital_signs={
                    'temp': 38.2 + (i * 0.3),
                    'hr': 80 + (i * 10),
                    'resp': 20 + (i * 2),
                    'bp': '120/80'
                }
            )
            db.session.add(routine_visit)
            visits.append(routine_visit)
            
            # Add emergency visit every few days for variety
            if day_offset % 3 == 0 and i == 1:
                emergency_visit = VeterinaryVisit(
                    dog_id=dog.id,
                    vet_id=test_vet_employee.id,
                    project_id=test_project.id,
                    visit_type=VisitType.EMERGENCY,
                    visit_date=visit_date + timedelta(hours=6),
                    weight=27.0,
                    temperature=39.5,
                    heart_rate=120,
                    blood_pressure='140/90',
                    symptoms='تعب وخمول مفاجئ',
                    diagnosis='التهاب معوي بسيط',
                    treatment='علاج بالمضادات الحيوية والراحة',
                    medications=[
                        {'name': 'أموكسيسيلين', 'dose': '500mg', 'duration': '7 أيام', 'frequency': 'كل 8 ساعات'},
                        {'name': 'مسكن ألم', 'dose': '200mg', 'duration': '3 أيام', 'frequency': 'كل 12 ساعة'}
                    ],
                    stool_color='أخضر فاتح',
                    stool_consistency='لينة',
                    urine_color='أصفر داكن',
                    vaccinations_given=[],
                    next_visit_date=visit_date.date() + timedelta(days=7),
                    notes=f'زيارة طارئة لـ {dog.name} - تم العلاج بنجاح',
                    cost=350.0,
                    location='عيادة الطوارئ',
                    weather='ممطر',
                    vital_signs={
                        'temp': 39.5,
                        'hr': 120,
                        'resp': 32,
                        'bp': '140/90'
                    }
                )
                db.session.add(emergency_visit)
                visits.append(emergency_visit)
            
            # Add vaccination visit once per week
            if day_offset == 0:
                vaccination_visit = VeterinaryVisit(
                    dog_id=dog.id,
                    vet_id=test_vet_employee.id,
                    project_id=test_project.id,
                    visit_type=VisitType.VACCINATION,
                    visit_date=visit_date + timedelta(hours=12),
                    weight=26.0 + i,
                    temperature=38.0,
                    heart_rate=75 + (i * 5),
                    blood_pressure='115/75',
                    symptoms='لا يوجد أعراض',
                    diagnosis='سليم للتطعيم',
                    treatment='تطعيم وقائي',
                    medications=[],
                    stool_color='بني',
                    stool_consistency='طبيعية',
                    urine_color='أصفر',
                    vaccinations_given=[
                        'تطعيم الكلب',
                        'تطعيم البارفو',
                        'تطعيم الديستمبر'
                    ],
                    next_visit_date=visit_date.date() + timedelta(days=365),
                    notes=f'تطعيم سنوي لـ {dog.name} - تم بنجاح',
                    cost=200.0,
                    location='العيادة البيطرية',
                    weather='معتدل',
                    vital_signs={
                        'temp': 38.0,
                        'hr': 75 + (i * 5),
                        'resp': 18,
                        'bp': '115/75'
                    }
                )
                db.session.add(vaccination_visit)
                visits.append(vaccination_visit)
    
    db.session.commit()
    return visits


@pytest.fixture(scope='function')
def test_other_project(db_session, admin_user):
    """Create another test project for permission testing"""
    project = Project(
        name='Other K9 Project',
        code='OK9P002',
        description='Another test project for access control testing',
        start_date=date.today() - timedelta(days=20),
        manager_id=admin_user.id
    )
    db.session.add(project)
    db.session.commit()
    return project


@pytest.fixture(scope='function')
def test_user_without_permissions(db_session):
    """Create user without veterinary report permissions"""
    user = User(
        username='limited_user',
        email='limited@test.com',
        password_hash=generate_password_hash('limitedpass123'),
        full_name='Limited User',
        role=UserRole.PROJECT_MANAGER,
        active=True
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def test_caretaker_employee(db_session):
    """Create test caretaker employee"""
    caretaker = Employee(
        name='أحمد القائم بالرعاية',
        employee_id='CARE001',
        role=EmployeeRole.HANDLER,
        phone='987654321',
        email='caretaker@test.com',
        hire_date=date(2021, 1, 1),
        is_active=True
    )
    db.session.add(caretaker)
    db.session.commit()
    return caretaker


@pytest.fixture(scope='function')
def test_caretaker_logs(db_session, test_dogs, test_project, test_caretaker_employee, test_user):
    """Create test caretaker daily logs"""
    logs = []
    base_date = date.today()
    
    # Create caretaker logs for testing
    for day_offset in range(7):  # Create data for a week
        log_date = base_date - timedelta(days=day_offset)
        
        for i, dog in enumerate(test_dogs):
            caretaker_log = CaretakerDailyLog(
                dog_id=dog.id,
                project_id=test_project.id,
                caretaker_employee_id=test_caretaker_employee.id,
                date=log_date,
                house_number=f"H{i+1:03d}",
                house_clean=True if i % 2 == 0 else False,
                house_vacuum=True if i % 3 == 0 else False,
                house_tap_clean=True if i % 2 == 1 else False,
                house_drain_clean=True if i % 4 == 0 else False,
                dog_clean=True if i % 2 == 0 else False,
                dog_washed=True if i % 3 == 1 else False,
                dog_brushed=True if i % 2 == 1 else False,
                bowls_bucket_clean=True if i % 3 == 0 else False,
                notes=f'رعاية يومية لـ {dog.name} - يوم {day_offset + 1}',
                created_by=test_user.id,
                created_at=datetime.combine(log_date, datetime.min.time().replace(hour=9, minute=30))
            )
            db.session.add(caretaker_log)
            logs.append(caretaker_log)
    
    db.session.commit()
    return logs