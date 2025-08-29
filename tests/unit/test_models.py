"""
اختبارات الوحدة للنماذج الأساسية
تفحص صحة النماذج وسلوكها المنطقي
"""

import pytest
from datetime import date, datetime, time
from werkzeug.security import check_password_hash
from models import (
    User, Employee, Dog, Project, TrainingSession, VeterinaryVisit,
    UserRole, EmployeeRole, DogStatus, DogGender, TrainingCategory,
    ProjectStatus, VisitType
)


@pytest.mark.unit
class TestUserModel:
    """اختبارات نموذج المستخدم"""
    
    def test_user_creation(self, db_session):
        """اختبار إنشاء مستخدم جديد"""
        user = User()
        user.username = 'test_user'
        user.email = 'test@example.com'
        user.password_hash = 'hashed_password'
        user.full_name = 'مستخدم تجريبي'
        user.role = UserRole.PROJECT_MANAGER
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == 'test_user'
        assert user.email == 'test@example.com'
        assert user.role == UserRole.PROJECT_MANAGER
        assert user.active is True  # القيمة الافتراضية
        
    def test_user_password_verification(self, sample_user):
        """اختبار التحقق من كلمة المرور"""
        assert check_password_hash(sample_user.password_hash, 'password123')
        assert not check_password_hash(sample_user.password_hash, 'wrong_password')
        
    def test_user_string_representation(self, sample_user):
        """اختبار التمثيل النصي للمستخدم"""
        assert str(sample_user) == '<User test_user>'
        
    def test_user_is_active_property(self, sample_user):
        """اختبار خاصية is_active للمستخدم"""
        assert sample_user.is_active is True
        
        sample_user.active = False
        assert sample_user.is_active is False


@pytest.mark.unit
class TestEmployeeModel:
    """اختبارات نموذج الموظف"""
    
    def test_employee_creation(self, db_session):
        """اختبار إنشاء موظف جديد"""
        employee = Employee()
        employee.name = 'أحمد محمد'
        employee.employee_id = 'EMP001'
        employee.role = EmployeeRole.TRAINER
        employee.phone = '123456789'
        employee.email = 'ahmed@example.com'
        employee.hire_date = date(2023, 1, 15)
        
        db_session.add(employee)
        db_session.commit()
        
        assert employee.id is not None
        assert employee.name == 'أحمد محمد'
        assert employee.employee_id == 'EMP001'
        assert employee.role == EmployeeRole.TRAINER
        assert employee.active is True
        
    def test_employee_string_representation(self, sample_employee):
        """اختبار التمثيل النصي للموظف"""
        expected = '<Employee أحمد محمد (EMP001)>'
        assert str(sample_employee) == expected


@pytest.mark.unit
class TestDogModel:
    """اختبارات نموذج الكلب"""
    
    def test_dog_creation(self, db_session):
        """اختبار إنشاء كلب جديد"""
        dog = Dog()
        dog.name = 'ماكس'
        dog.code = 'DOG002'
        dog.breed = 'لابرادور'
        dog.gender = DogGender.FEMALE
        dog.birth_date = date(2021, 3, 10)
        dog.status = DogStatus.TRAINING
        dog.weight = 28.5
        dog.height = 55.0
        dog.color = 'ذهبي'
        
        db_session.add(dog)
        db_session.commit()
        
        assert dog.id is not None
        assert dog.name == 'ماكس'
        assert dog.code == 'DOG002'
        assert dog.breed == 'لابرادور'
        assert dog.gender == DogGender.FEMALE
        assert dog.status == DogStatus.TRAINING
        
    def test_dog_age_calculation(self, sample_dog):
        """اختبار حساب عمر الكلب"""
        # الكلب النموذجي ولد في 2022-06-15
        today = date.today()
        expected_age = today.year - 2022
        if today.month < 6 or (today.month == 6 and today.day < 15):
            expected_age -= 1
            
        # سنحتاج لإضافة دالة حساب العمر للنموذج
        # assert sample_dog.get_age() == expected_age
        
    def test_dog_string_representation(self, sample_dog):
        """اختبار التمثيل النصي للكلب"""
        expected = '<Dog ريكس (DOG001)>'
        assert str(sample_dog) == expected


@pytest.mark.unit
class TestProjectModel:
    """اختبارات نموذج المشروع"""
    
    def test_project_creation(self, db_session, sample_employee):
        """اختبار إنشاء مشروع جديد"""
        project = Project()
        project.name = 'مشروع الحدود'
        project.code = 'BORDER001'
        project.main_task = 'مراقبة الحدود'
        project.description = 'مشروع لمراقبة الحدود الجنوبية'
        project.status = ProjectStatus.PLANNED
        project.start_date = date(2024, 6, 1)
        project.expected_completion_date = date(2024, 12, 31)
        project.location = 'الحد الجنوبي'
        project.priority = 'HIGH'
        project.project_manager_id = sample_employee.id
        
        db_session.add(project)
        db_session.commit()
        
        assert project.id is not None
        assert project.name == 'مشروع الحدود'
        assert project.code == 'BORDER001'
        assert project.status == ProjectStatus.PLANNED
        assert project.priority == 'HIGH'
        
    def test_project_duration_calculation(self, sample_project):
        """اختبار حساب مدة المشروع"""
        # المشروع النموذجي من 2024-01-01 إلى 2024-12-31
        duration = sample_project.calculate_duration()
        expected_duration = (date(2024, 12, 31) - date(2024, 1, 1)).days + 1
        assert duration == expected_duration
        
    def test_project_string_representation(self, sample_project):
        """اختبار التمثيل النصي للمشروع"""
        expected = '<Project مشروع الأمن (SEC001)>'
        assert str(sample_project) == expected


@pytest.mark.unit
class TestTrainingSessionModel:
    """اختبارات نموذج جلسة التدريب"""
    
    def test_training_session_creation(self, db_session, sample_dog, sample_employee, sample_project):
        """اختبار إنشاء جلسة تدريب جديدة"""
        training = TrainingSession()
        training.dog_id = sample_dog.id
        training.trainer_id = sample_employee.id
        training.project_id = sample_project.id
        training.category = TrainingCategory.DETECTION
        training.subject = 'تدريب كشف المتفجرات'
        training.training_date = date.today()
        training.duration_minutes = 90
        training.success_rating = 9
        training.location = 'ساحة التدريب المتقدم'
        training.notes = 'أداء ممتاز في كشف المتفجرات'
        
        db_session.add(training)
        db_session.commit()
        
        assert training.id is not None
        assert training.category == TrainingCategory.DETECTION
        assert training.subject == 'تدريب كشف المتفجرات'
        assert training.duration_minutes == 90
        assert training.success_rating == 9
        
    def test_training_session_relationships(self, sample_training_session):
        """اختبار العلاقات في جلسة التدريب"""
        assert sample_training_session.dog is not None
        assert sample_training_session.trainer is not None
        assert sample_training_session.project is not None
        assert sample_training_session.dog.name == 'ريكس'
        assert sample_training_session.trainer.name == 'أحمد محمد'
        
    def test_training_session_string_representation(self, sample_training_session):
        """اختبار التمثيل النصي لجلسة التدريب"""
        expected = '<TrainingSession تدريب الطاعة الأساسي - ريكس>'
        assert str(sample_training_session) == expected


@pytest.mark.unit
class TestVeterinaryVisitModel:
    """اختبارات نموذج الزيارة البيطرية"""
    
    def test_veterinary_visit_creation(self, db_session, sample_dog, sample_employee):
        """اختبار إنشاء زيارة بيطرية جديدة"""
        visit = VeterinaryVisit()
        visit.dog_id = sample_dog.id
        visit.vet_id = sample_employee.id
        visit.visit_type = VisitType.ROUTINE
        visit.visit_date = datetime.now()
        visit.weight = 36.0
        visit.temperature = 38.5
        visit.heart_rate = 85
        visit.symptoms = 'فحص دوري'
        visit.diagnosis = 'الكلب بحالة صحية جيدة'
        visit.treatment = 'لا يوجد علاج مطلوب'
        
        db_session.add(visit)
        db_session.commit()
        
        assert visit.id is not None
        assert visit.visit_type == VisitType.ROUTINE
        assert visit.weight == 36.0
        assert visit.temperature == 38.5
        assert visit.heart_rate == 85
        
    def test_veterinary_visit_relationships(self, db_session, sample_dog, sample_employee):
        """اختبار العلاقات في الزيارة البيطرية"""
        visit = VeterinaryVisit()
        visit.dog_id = sample_dog.id
        visit.vet_id = sample_employee.id
        visit.visit_type = VisitType.EMERGENCY
        visit.visit_date = datetime.now()
        
        db_session.add(visit)
        db_session.commit()
        
        assert visit.dog is not None
        assert visit.vet is not None
        assert visit.dog.name == 'ريكس'
        assert visit.vet.name == 'أحمد محمد'


@pytest.mark.unit
class TestModelValidations:
    """اختبارات التحقق من صحة النماذج"""
    
    def test_user_unique_username(self, db_session, sample_user):
        """اختبار فرادة اسم المستخدم"""
        # محاولة إنشاء مستخدم آخر بنفس اسم المستخدم
        duplicate_user = User()
        duplicate_user.username = 'test_user'  # نفس اسم المستخدم
        duplicate_user.email = 'different@example.com'
        duplicate_user.password_hash = 'hashed_password'
        duplicate_user.full_name = 'مستخدم آخر'
        duplicate_user.role = UserRole.PROJECT_MANAGER
        
        db_session.add(duplicate_user)
        
        # يجب أن يرفع خطأ بسبب التكرار
        with pytest.raises(Exception):
            db_session.commit()
            
    def test_employee_unique_employee_id(self, db_session, sample_employee):
        """اختبار فرادة رقم الموظف"""
        # محاولة إنشاء موظف آخر بنفس الرقم
        duplicate_employee = Employee()
        duplicate_employee.name = 'سالم أحمد'
        duplicate_employee.employee_id = 'EMP001'  # نفس رقم الموظف
        duplicate_employee.role = EmployeeRole.VET
        duplicate_employee.phone = '987654321'
        duplicate_employee.email = 'salem@example.com'
        duplicate_employee.hire_date = date(2023, 6, 1)
        
        db_session.add(duplicate_employee)
        
        # يجب أن يرفع خطأ بسبب التكرار
        with pytest.raises(Exception):
            db_session.commit()
            
    def test_dog_unique_code(self, db_session, sample_dog):
        """اختبار فرادة رمز الكلب"""
        # محاولة إنشاء كلب آخر بنفس الرمز
        duplicate_dog = Dog()
        duplicate_dog.name = 'بيلا'
        duplicate_dog.code = 'DOG001'  # نفس رمز الكلب
        duplicate_dog.breed = 'روت وايلر'
        duplicate_dog.gender = DogGender.FEMALE
        duplicate_dog.birth_date = date(2021, 8, 20)
        duplicate_dog.status = DogStatus.ACTIVE
        
        db_session.add(duplicate_dog)
        
        # يجب أن يرفع خطأ بسبب التكرار
        with pytest.raises(Exception):
            db_session.commit()