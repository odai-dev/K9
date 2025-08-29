"""
ملف التكوين الرئيسي للاختبارات
يحتوي على الإعدادات المشتركة والـ fixtures المطلوبة لجميع الاختبارات
"""

import pytest
import tempfile
import os
from datetime import datetime, date, time
import sys

# إضافة مسار المشروع للـ Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app, db
from models import *
from models_attendance_reporting import *


@pytest.fixture(scope='session')
def app():
    """إنشاء تطبيق Flask للاختبارات"""
    # إنشاء ملف قاعدة بيانات مؤقت
    db_fd, db_path = tempfile.mkstemp()
    
    # تكوين التطبيق للاختبارات
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        
    # تنظيف الملفات المؤقتة
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='function')
def client(app):
    """إنشاء عميل HTTP للاختبارات"""
    return app.test_client()


@pytest.fixture(scope='function')
def app_context(app):
    """إنشاء سياق التطبيق للاختبارات"""
    with app.app_context():
        yield app


@pytest.fixture(scope='function')
def db_session(app_context):
    """إنشاء جلسة قاعدة بيانات للاختبارات مع rollback تلقائي"""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    # ربط الجلسة بالمعاملة
    db.session.bind = connection
    
    yield db.session
    
    # إعادة تدوير التغييرات
    transaction.rollback()
    connection.close()
    db.session.bind = None


@pytest.fixture
def sample_user(db_session):
    """إنشاء مستخدم نموذجي للاختبارات"""
    from werkzeug.security import generate_password_hash
    
    user = User()
    user.username = 'test_user'
    user.email = 'test@example.com'
    user.password_hash = generate_password_hash('password123')
    user.full_name = 'مستخدم تجريبي'
    user.role = UserRole.PROJECT_MANAGER
    user.active = True
    
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_admin(db_session):
    """إنشاء مدير نموذجي للاختبارات"""
    from werkzeug.security import generate_password_hash
    
    admin = User()
    admin.username = 'admin_user'
    admin.email = 'admin@example.com'
    admin.password_hash = generate_password_hash('admin123')
    admin.full_name = 'مدير النظام'
    admin.role = UserRole.GENERAL_ADMIN
    admin.active = True
    
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture
def sample_employee(db_session):
    """إنشاء موظف نموذجي للاختبارات"""
    employee = Employee()
    employee.name = 'أحمد محمد'
    employee.employee_id = 'EMP001'
    employee.role = EmployeeRole.HANDLER
    employee.phone = '123456789'
    employee.email = 'ahmed@example.com'
    employee.address = 'الرياض، المملكة العربية السعودية'
    employee.hire_date = date(2023, 1, 15)
    employee.active = True
    
    db_session.add(employee)
    db_session.commit()
    return employee


@pytest.fixture
def sample_dog(db_session):
    """إنشاء كلب نموذجي للاختبارات"""
    dog = Dog()
    dog.name = 'ريكس'
    dog.code = 'DOG001'
    dog.breed = 'جيرمن شيبرد'
    dog.gender = DogGender.MALE
    dog.birth_date = date(2022, 6, 15)
    dog.status = DogStatus.ACTIVE
    dog.weight = 35.5
    dog.height = 65.0
    dog.color = 'بني وأسود'
    dog.microchip_id = '12345678901234'
    dog.vaccination_status = 'محدث'
    dog.notes = 'كلب مدرب جيداً وهادئ'
    
    db_session.add(dog)
    db_session.commit()
    return dog


@pytest.fixture
def sample_project(db_session, sample_employee):
    """إنشاء مشروع نموذجي للاختبارات"""
    project = Project()
    project.name = 'مشروع الأمن'
    project.code = 'SEC001'
    project.main_task = 'حراسة المطار'
    project.description = 'مشروع أمني لحراسة المطار الدولي'
    project.status = ProjectStatus.ACTIVE
    project.start_date = date(2024, 1, 1)
    project.expected_completion_date = date(2024, 12, 31)
    project.location = 'مطار الملك خالد الدولي'
    project.mission_type = 'أمني'
    project.priority = 'HIGH'
    project.project_manager_id = sample_employee.id
    
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture
def sample_training_session(db_session, sample_dog, sample_employee, sample_project):
    """إنشاء جلسة تدريب نموذجية للاختبارات"""
    training = TrainingSession()
    training.dog_id = sample_dog.id
    training.trainer_id = sample_employee.id
    training.project_id = sample_project.id
    training.category = TrainingCategory.OBEDIENCE
    training.subject = 'تدريب الطاعة الأساسي'
    training.training_date = date.today()
    training.duration_minutes = 60
    training.success_rating = 8
    training.location = 'ساحة التدريب الرئيسية'
    training.notes = 'تدريب ممتاز، الكلب يستجيب بشكل جيد'
    training.weather_conditions = 'مشمس، 25 درجة مئوية'
    
    db_session.add(training)
    db_session.commit()
    return training


@pytest.fixture
def sample_attendance_record(db_session, sample_project, sample_employee):
    """إنشاء سجل حضور نموذجي للاختبارات"""
    from models_attendance_reporting import ProjectAttendanceReporting, AttendanceStatus
    
    attendance = ProjectAttendanceReporting()
    attendance.date = date.today()
    attendance.project_id = sample_project.id
    attendance.employee_id = sample_employee.id
    attendance.group_no = 1
    attendance.seq_no = 1
    attendance.check_in_time = time(8, 0)
    attendance.check_out_time = time(16, 0)
    attendance.status = AttendanceStatus.PRESENT
    
    db_session.add(attendance)
    db_session.commit()
    return attendance


# Markers للتصنيف
def pytest_configure(config):
    """تكوين إضافي للاختبارات"""
    config.addinivalue_line("markers", "unit: اختبارات الوحدة")
    config.addinivalue_line("markers", "integration: اختبارات التكامل")
    config.addinivalue_line("markers", "slow: اختبارات بطيئة")
    config.addinivalue_line("markers", "database: اختبارات تتطلب قاعدة بيانات")