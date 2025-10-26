from app import db
from flask_login import UserMixin
from datetime import datetime, date
from enum import Enum
import uuid
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import String, Text
import os

# Use String for UUID when using SQLite, UUID when using PostgreSQL
def get_uuid_column():
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url.startswith("sqlite") or not database_url:
        return String(36)
    else:
        from sqlalchemy.dialects.postgresql import UUID
        return UUID(as_uuid=True)

# Helper function to ensure UUID values are strings for SQLite
def ensure_uuid_string():
    return lambda: str(uuid.uuid4())

# Helper to get default UUID - always returns string for compatibility
def default_uuid():
    return str(uuid.uuid4())

class UserRole(Enum):
    GENERAL_ADMIN = "GENERAL_ADMIN"
    PROJECT_MANAGER = "PROJECT_MANAGER"
    HANDLER = "HANDLER"

class EmployeeRole(Enum):
    HANDLER = "سائس"
    TRAINER = "مدرب"
    BREEDER = "مربي"
    VET = "طبيب"
    PROJECT_MANAGER = "مسؤول مشروع"

class DogStatus(Enum):
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"
    DECEASED = "DECEASED"
    TRAINING = "TRAINING"

class DogGender(Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"

class TrainingCategory(Enum):
    OBEDIENCE = "طاعة"
    DETECTION = "كشف"
    AGILITY = "رشاقة"
    ATTACK = "هجوم"
    FITNESS = "لياقة"
    SOCIALIZATION = "تطبيع"
    BALL_WORK = "تدريب الكرة"
    OTHER = "أخرى"

class SocializationType(Enum):
    HUMAN_INTERACTION = "تفاعل مع البشر"
    ANIMAL_INTERACTION = "تفاعل مع الحيوانات"
    VEHICLE_EXPOSURE = "التعرض للمركبات"
    SOUND_DESENSITIZATION = "إزالة الحساسية للأصوات"
    ENVIRONMENT_EXPLORATION = "استكشاف البيئة"
    CROWD_INTERACTION = "تفاعل مع الحشود"

class BallWorkType(Enum):
    FETCH_TRAINING = "تدريب الإحضار"
    CATCH_TRAINING = "تدريب المسك"
    AGILITY_BALL = "كرة الرشاقة"
    COORDINATION_BALL = "كرة التناسق"
    REWARD_BALL = "كرة المكافأة"

class VisitType(Enum):
    ROUTINE = "ROUTINE"
    EMERGENCY = "EMERGENCY"
    VACCINATION = "VACCINATION"

class ProductionCycleType(Enum):
    NATURAL = "NATURAL"
    ARTIFICIAL = "ARTIFICIAL"

class ProductionResult(Enum):
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"

class MaturityStatus(Enum):
    JUVENILE = "يافع"
    MATURE = "بالغ"
    RETIRED = "متقاعد"

class HeatStatus(Enum):
    NOT_IN_HEAT = "لا توجد دورة"
    IN_HEAT = "في الدورة"
    POST_HEAT = "بعد الدورة"
    COMPLETED = "مكتملة"
    PRE_HEAT = "ما قبل الحرارة"

class MatingResult(Enum):
    SUCCESSFUL = "نجح"
    FAILED = "فشل"
    UNKNOWN = "غير معروف"

class DeliveryStatus(Enum):
    EXPECTED = "متوقع"
    IN_PROGRESS = "جاري"
    COMPLETED = "مكتمل"
    COMPLICATIONS = "مضاعفات"

class PregnancyStatus(Enum):
    NOT_PREGNANT = "غير حامل"
    PREGNANT = "حامل"
    DELIVERED = "ولدت"

class ProjectStatus(Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"



class ElementType(Enum):
    WEAPON = "WEAPON"
    DRUG = "DRUG"
    EXPLOSIVE = "EXPLOSIVE"
    OTHER = "OTHER"

class PerformanceRating(Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    WEAK = "WEAK"

class TargetType(Enum):
    EMPLOYEE = "EMPLOYEE"
    DOG = "DOG"

class AuditAction(Enum):
    CREATE = "CREATE"
    EDIT = "EDIT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    EXPORT = "EXPORT"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    SECURITY_EVENT = "SECURITY_EVENT"

# New enums for attendance system
class EntityType(Enum):
    EMPLOYEE = "EMPLOYEE"
    DOG = "DOG"

class AttendanceStatus(Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    SICK = "SICK"
    LEAVE = "LEAVE"
    REMOTE = "REMOTE"
    OVERTIME = "OVERTIME"

class AbsenceReason(Enum):
    ANNUAL = "إجازة سنوية"
    SICK = "مريض"
    EMERGENCY = "حالة طارئة"
    TRAINING = "تدريب"
    MISSION = "مهمة"
    NO_REASON = "بلا سبب"
    OTHER = "أخرى"

# Arabic enums for Daily Checkup (store Arabic strings)
class PartStatus(Enum):
    NORMAL = "سليم"
    REDNESS = "احمرار"
    INFLAMMATION = "التهاب"
    DISCHARGE = "إفرازات"
    SWELLING = "تورم"
    WOUND = "جرح"
    PAIN = "ألم"
    OTHER = "أخرى"

class Severity(Enum):
    MILD = "خفيف"
    MODERATE = "متوسط"
    SEVERE = "شديد"

# Grooming enums - Using English values for database, Arabic display in UI
class GroomingYesNo(Enum):
    YES = "YES"
    NO = "NO"

class GroomingCleanlinessScore(Enum):  # 1..5 stars/levels
    SCORE_1 = "1"
    SCORE_2 = "2"
    SCORE_3 = "3"
    SCORE_4 = "4"
    SCORE_5 = "5"

# ---------- Arabic enums for Deworming (stored values are Arabic) ----------
class Route(Enum):
    ORAL = "فموي"        # فموي
    TOPICAL = "موضعي"    # موضعي  
    INJECTION = "حقن"     # حقن

class Unit(Enum):
    ML = "مل"            # مل
    MG = "ملغم"          # ملغم
    TABLET = "قرص"       # قرص

class Reaction(Enum):
    NONE = "لا يوجد"             # لا يوجد
    VOMITING = "قيء"             # قيء
    DIARRHEA = "إسهال"           # إسهال
    LETHARGY = "خمول"            # خمول
    SKIN_ALLERGY = "تحسس جلدي"   # تحسس جلدي
    OTHER = "أخرى"              # أخرى

# Association table for many-to-many relationship between employees and dogs
employee_dog_assignment = db.Table('employee_dog_assignment',
    db.Column('employee_id', get_uuid_column(), db.ForeignKey('employee.id'), primary_key=True),
    db.Column('dog_id', get_uuid_column(), db.ForeignKey('dog.id'), primary_key=True)
)

# Association table for many-to-many relationship between projects and dogs
project_dog_assignment = db.Table('project_dog_assignment',
    db.Column('project_id', get_uuid_column(), db.ForeignKey('project.id'), primary_key=True),
    db.Column('dog_id', get_uuid_column(), db.ForeignKey('dog.id'), primary_key=True)
)

# Association table for many-to-many relationship between projects and employees
project_employee_assignment = db.Table('project_employee_assignment',
    db.Column('project_id', get_uuid_column(), db.ForeignKey('project.id'), primary_key=True),
    db.Column('employee_id', get_uuid_column(), db.ForeignKey('employee.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.PROJECT_MANAGER)
    full_name = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean, default=True)
    
    @property
    def is_active(self):
        return self.active
    
    @is_active.setter
    def is_active(self, value):
        self.active = value
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Security enhancements
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime)
    password_changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # MFA fields
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(32))
    backup_codes = db.Column(JSON, default=list)
    
    # For project managers - which sections they can access
    allowed_sections = db.Column(JSON, default=list)
    
    # Handler-specific fields
    phone = db.Column(db.String(20))  # رقم الهاتف للسائس
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=True)  # المشروع المخصص للسائس
    dog_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'), nullable=True)  # الكلب المخصص للسائس
    
    # Relationship to project manager permissions
    pm_permissions = db.relationship('ProjectManagerPermission', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # Relationships for handler
    assigned_project = db.relationship('Project', backref='handler_users', foreign_keys=[project_id])
    assigned_dog = db.relationship('Dog', backref='handler_users', foreign_keys=[dog_id])
    
    def __repr__(self):
        return f'<User {self.username}>'

class Dog(db.Model):
    __table_args__ = (
        db.Index('idx_dog_status_breed', 'current_status', 'breed'),
        db.Index('idx_dog_gender_status', 'gender', 'current_status'),
        db.Index('idx_dog_birth_date', 'birth_date'),
    )
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    breed = db.Column(db.String(100), nullable=False)
    family_line = db.Column(db.String(100))
    gender = db.Column(db.Enum(DogGender), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    microchip_id = db.Column(db.String(50), unique=True)
    current_status = db.Column(db.Enum(DogStatus), default=DogStatus.ACTIVE)
    location = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    color = db.Column(db.String(50))
    weight = db.Column(db.Float)
    height = db.Column(db.Float)
    
    # File uploads
    birth_certificate = db.Column(db.String(255))
    photo = db.Column(db.String(255))
    medical_records = db.Column(JSON, default=list)
    
    # Relationships
    assigned_to_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'))
    assigned_to_user = db.relationship('User', backref='assigned_dogs', foreign_keys=[assigned_to_user_id])
    
    # Parent relationships for breeding
    father_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'))
    mother_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'))
    father = db.relationship('Dog', remote_side=[id], foreign_keys=[father_id], backref='sired_offspring')
    mother = db.relationship('Dog', remote_side=[id], foreign_keys=[mother_id], backref='birthed_offspring')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Many-to-many relationships
    assigned_employees = db.relationship('Employee', secondary=employee_dog_assignment, back_populates='assigned_dogs')
    projects = db.relationship('Project', secondary=project_dog_assignment, back_populates='assigned_dogs')
    
    def __repr__(self):
        return f'<Dog {self.name} ({self.code})>'

class Employee(db.Model):
    __table_args__ = (
        db.Index('idx_employee_role_active', 'role', 'is_active'),
        db.Index('idx_employee_email', 'email'),
    )
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    name = db.Column(db.String(100), nullable=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    role = db.Column(db.Enum(EmployeeRole), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    hire_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Additional info
    certifications = db.Column(JSON, default=list)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assigned_to_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'))
    assigned_to_user = db.relationship('User', foreign_keys=[assigned_to_user_id], backref='assigned_employees')
    
    # For project managers - link to their user account
    user_account_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'))
    user_account = db.relationship('User', foreign_keys=[user_account_id], backref='employee_profile')
    
    # Many-to-many relationships
    assigned_dogs = db.relationship('Dog', secondary=employee_dog_assignment, back_populates='assigned_employees')
    projects = db.relationship('Project', secondary=project_employee_assignment, back_populates='assigned_employees')
    
    def is_project_owned(self, target_date):
        """Check if employee is assigned to any active or planned projects for the given date"""
        from datetime import date
        from sqlalchemy import and_, or_
        if isinstance(target_date, str):
            try:
                target_date = date.fromisoformat(target_date)
            except ValueError:
                return False
        
        # Check if employee has any active assignments for the target date
        active_assignments = db.session.query(ProjectAssignment).join(Project).filter(
            and_(
                ProjectAssignment.employee_id == self.id,
                ProjectAssignment.is_active == True,
                or_(
                    Project.status == ProjectStatus.ACTIVE,
                    Project.status == ProjectStatus.PLANNED
                ),
                or_(
                    # Assignment has no end date (open-ended)
                    ProjectAssignment.assigned_to.is_(None),
                    # Or target date is within assignment period
                    and_(
                        ProjectAssignment.assigned_from <= target_date,
                        ProjectAssignment.assigned_to >= target_date
                    )
                ),
                or_(
                    # Project has no end date (open-ended)
                    Project.end_date.is_(None),
                    # Or target date is within project period
                    and_(
                        Project.start_date <= target_date,
                        Project.end_date >= target_date
                    )
                )
            )
        ).first()
        
        return active_assignments is not None

    def __repr__(self):
        return f'<Employee {self.name} ({self.employee_id})>'

class TrainingSession(db.Model):
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    dog_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'), nullable=False)
    trainer_id = db.Column(get_uuid_column(), db.ForeignKey('employee.id'), nullable=False)
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=True)  # Auto-linked project
    category = db.Column(db.Enum(TrainingCategory), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    session_date = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # minutes
    success_rating = db.Column(db.Integer, nullable=False)  # 0-10
    location = db.Column(db.String(100))
    notes = db.Column(Text)
    weather_conditions = db.Column(db.String(100))
    equipment_used = db.Column(JSON, default=list)
    
    # Relationships
    dog = db.relationship('Dog', backref='training_sessions')
    trainer = db.relationship('Employee', backref='training_sessions')
    project = db.relationship('Project', backref='training_sessions')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TrainingSession {self.subject} - {self.dog.name}>'

class VeterinaryVisit(db.Model):
    __table_args__ = (
        db.Index('idx_veterinary_visit_date', 'visit_date'),
        db.Index('idx_veterinary_dog_date', 'dog_id', 'visit_date'),
        db.Index('idx_veterinary_vet_date', 'vet_id', 'visit_date'),
        db.Index('idx_veterinary_project_date', 'project_id', 'visit_date'),
        db.Index('idx_veterinary_type_date', 'visit_type', 'visit_date'),
    )
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    dog_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'), nullable=False)
    vet_id = db.Column(get_uuid_column(), db.ForeignKey('employee.id'), nullable=False)
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=True)  # Auto-linked project
    visit_type = db.Column(db.Enum(VisitType), nullable=False)
    visit_date = db.Column(db.DateTime, nullable=False)
    
    # Physical examination
    weight = db.Column(db.Float)
    temperature = db.Column(db.Float)
    heart_rate = db.Column(db.Integer)
    blood_pressure = db.Column(db.String(20))
    
    # Health assessment
    symptoms = db.Column(Text)
    diagnosis = db.Column(Text)
    treatment = db.Column(Text)
    medications = db.Column(JSON, default=list)  # [{name, dose, duration, frequency}]
    
    # Stool and urine analysis
    stool_color = db.Column(db.String(50))
    stool_consistency = db.Column(db.String(50))
    urine_color = db.Column(db.String(50))
    
    # Vaccinations
    vaccinations_given = db.Column(JSON, default=list)
    next_visit_date = db.Column(db.Date)
    
    notes = db.Column(Text)
    cost = db.Column(db.Float)
    
    # Additional fields for daily reports
    location = db.Column(db.String(120))  # Location of examination
    weather = db.Column(db.String(80))    # Weather conditions
    vital_signs = db.Column(JSON, default=dict)  # Consolidated vital signs
    
    # Relationships
    dog = db.relationship('Dog', backref='veterinary_visits')
    vet = db.relationship('Employee', backref='veterinary_visits')
    project = db.relationship('Project', backref='veterinary_visits')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<VeterinaryVisit {self.visit_type.value} - {self.dog.name}>'

class ProductionCycle(db.Model):
    __tablename__ = 'production_cycle'
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    female_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'), nullable=False)
    male_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'), nullable=False)
    cycle_type = db.Column(db.Enum(ProductionCycleType), nullable=False)
    
    # Cycle dates
    heat_start_date = db.Column(db.Date)
    mating_date = db.Column(db.Date, nullable=False)
    expected_delivery_date = db.Column(db.Date)
    actual_delivery_date = db.Column(db.Date)
    
    # Results
    result = db.Column(db.Enum(ProductionResult), default=ProductionResult.UNKNOWN)
    number_of_puppies = db.Column(db.Integer, default=0)
    puppies_survived = db.Column(db.Integer, default=0)
    puppies_info = db.Column(JSON, default=list)  # [{name, gender, chip_id, birth_weight}]
    
    # Care information
    prenatal_care = db.Column(Text)
    delivery_notes = db.Column(Text)
    complications = db.Column(Text)
    
    # Relationships
    female = db.relationship('Dog', foreign_keys=[female_id], backref='production_as_female')
    male = db.relationship('Dog', foreign_keys=[male_id], backref='production_as_male')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProductionCycle {self.female.name} x {self.male.name}>'

class Project(db.Model):
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    main_task = db.Column(Text)  # المهمة الأساسية
    description = db.Column(Text)
    status = db.Column(db.Enum(ProjectStatus), default=ProjectStatus.PLANNED)
    
    # Dates
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)  # Set automatically when project is completed
    duration_days = db.Column(db.Integer)  # computed field
    expected_completion_date = db.Column(db.Date)
    
    # Location and mission details
    location = db.Column(db.String(200))
    mission_type = db.Column(db.String(100))
    priority = db.Column(db.String(20), default='MEDIUM')
    
    # Management
    manager_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'))
    manager = db.relationship('User', foreign_keys=[manager_id], backref='managed_projects')
    
    # Project manager assignment (Employee with PROJECT_MANAGER role)
    project_manager_id = db.Column(get_uuid_column(), db.ForeignKey('employee.id'))
    project_manager = db.relationship('Employee', foreign_keys=[project_manager_id], backref='managed_projects')
    
    # Results and reporting
    success_rating = db.Column(db.Integer)  # 0-10
    final_report = db.Column(Text)
    lessons_learned = db.Column(Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Many-to-many relationships
    assigned_dogs = db.relationship('Dog', secondary=project_dog_assignment, back_populates='projects')
    assigned_employees = db.relationship('Employee', secondary=project_employee_assignment, back_populates='projects')
    
    def calculate_duration(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    def __repr__(self):
        return f'<Project {self.name} ({self.code})>'



class ProjectDog(db.Model):
    """Dog assignments to projects"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=False)
    dog_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    assigned_date = db.Column(db.Date, default=date.today)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='dog_assignments')
    dog = db.relationship('Dog', backref='project_dog_assignments')
    
    # Unique constraint to prevent duplicate assignments
    __table_args__ = (db.UniqueConstraint('project_id', 'dog_id', name='unique_project_dog'),)
    
    def __repr__(self):
        return f'<ProjectDog {self.dog.name} -> {self.project.name}>'

class ProjectAssignment(db.Model):
    """Combined assignments model for dogs and employees to projects"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=False)
    
    # Either dog or employee assignment
    dog_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'), nullable=True)
    employee_id = db.Column(get_uuid_column(), db.ForeignKey('employee.id'), nullable=True)
    
    # Assignment details
    is_active = db.Column(db.Boolean, default=True)
    assigned_from = db.Column(db.DateTime, default=datetime.utcnow)  # when the assignment started
    assigned_to = db.Column(db.DateTime, nullable=True)  # when the assignment ended (null means still active)
    assigned_date = db.Column(db.Date, default=date.today)  # Keep for backward compatibility
    unassigned_date = db.Column(db.Date, nullable=True)  # Keep for backward compatibility
    notes = db.Column(Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='assignments')
    dog = db.relationship('Dog', backref='project_assignments')
    employee = db.relationship('Employee', backref='project_assignments')
    
    # Constraint to ensure either dog_id or employee_id is set, but not both
    __table_args__ = (
        db.CheckConstraint('(dog_id IS NOT NULL AND employee_id IS NULL) OR (dog_id IS NULL AND employee_id IS NOT NULL)', name='assignment_target_check'),
        db.UniqueConstraint('project_id', 'dog_id', name='unique_project_dog_assignment'),
        db.UniqueConstraint('project_id', 'employee_id', name='unique_project_employee_assignment'),
    )
    
    def __repr__(self):
        target = self.dog.name if self.dog else self.employee.name
        return f'<ProjectAssignment {target} -> {self.project.name}>'

class Incident(db.Model):
    """Incident logging for projects"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)  # اسم الحادث
    incident_date = db.Column(db.Date, nullable=False)
    incident_time = db.Column(db.Time, nullable=False)
    incident_type = db.Column(db.String(100), nullable=False)  # نوع الحادث
    description = db.Column(Text)
    location = db.Column(db.String(200))
    severity = db.Column(db.String(20), default='MEDIUM')  # LOW, MEDIUM, HIGH
    
    # People involved
    reported_by = db.Column(get_uuid_column(), db.ForeignKey('employee.id'))
    people_involved = db.Column(JSON, default=list)  # List of employee IDs
    dogs_involved = db.Column(JSON, default=list)  # List of dog IDs
    
    # Attachments and evidence
    attachments = db.Column(JSON, default=list)  # File paths/URLs for photos, PDFs
    witness_statements = db.Column(Text)
    
    # Follow-up
    resolved = db.Column(db.Boolean, default=False)
    resolution_notes = db.Column(Text)
    resolution_date = db.Column(db.Date)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='incidents')
    reporter = db.relationship('Employee', backref='reported_incidents')
    
    def __repr__(self):
        return f'<Incident {self.name} - {self.project.name}>'

class Suspicion(db.Model):
    """Suspicion/discovery logging for projects"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=False)
    element_type = db.Column(db.Enum(ElementType), nullable=False)  # سلاح/مخدرات/متفجرات/أخرى
    suspicion_type = db.Column(db.String(100))  # نوع الاشتباه
    risk_level = db.Column(db.String(20), default='MEDIUM')  # LOW, MEDIUM, HIGH
    subtype = db.Column(db.String(100))  # نوع السلاح/العبوة
    discovery_date = db.Column(db.Date, nullable=False)
    discovery_time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    
    # Detection details
    detected_by_dog = db.Column(get_uuid_column(), db.ForeignKey('dog.id'))
    handler = db.Column(get_uuid_column(), db.ForeignKey('employee.id'))
    detection_method = db.Column(db.String(100))  # Visual, K9 Alert, Equipment, etc.
    
    # Description and evidence
    description = db.Column(Text)
    quantity_estimate = db.Column(db.String(100))
    attachments = db.Column(JSON, default=list)  # Photos, evidence logs
    
    # Follow-up actions
    authorities_notified = db.Column(db.Boolean, default=False)
    evidence_collected = db.Column(db.Boolean, default=False)
    follow_up_required = db.Column(db.Boolean, default=True)
    follow_up_notes = db.Column(Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='suspicions')
    detecting_dog = db.relationship('Dog', backref='detections')
    handling_employee = db.relationship('Employee', backref='handled_detections')
    
    def __repr__(self):
        return f'<Suspicion {self.element_type.value} - {self.project.name}>'

class PerformanceEvaluation(db.Model):
    """Performance evaluation for employees and dogs in projects"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=False)
    evaluator_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=False)
    target_type = db.Column(db.Enum(TargetType), nullable=False)  # EMPLOYEE or DOG
    
    # Target identification (generic approach)
    target_employee_id = db.Column(get_uuid_column(), db.ForeignKey('employee.id'))
    target_dog_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'))
    
    # Evaluation details
    evaluation_date = db.Column(db.Date, nullable=False, default=date.today)
    rating = db.Column(db.Enum(PerformanceRating), nullable=False)  # ممتاز/جيد/ضعيف
    
    # Specific criteria (primarily for employees)
    uniform_ok = db.Column(db.Boolean, default=True)  # زي الموظف
    id_card_ok = db.Column(db.Boolean, default=True)  # البطاقة
    appearance_ok = db.Column(db.Boolean, default=True)  # المظهر
    cleanliness_ok = db.Column(db.Boolean, default=True)  # النظافة
    
    # Performance metrics
    punctuality = db.Column(db.Integer)  # 1-10 scale
    job_knowledge = db.Column(db.Integer)  # 1-10 scale
    teamwork = db.Column(db.Integer)  # 1-10 scale
    communication = db.Column(db.Integer)  # 1-10 scale
    
    # For dogs - specific metrics
    obedience_level = db.Column(db.Integer)  # 1-10 scale
    detection_accuracy = db.Column(db.Integer)  # 1-10 scale
    physical_condition = db.Column(db.Integer)  # 1-10 scale
    handler_relationship = db.Column(db.Integer)  # 1-10 scale
    
    # General assessment
    strengths = db.Column(Text)
    areas_for_improvement = db.Column(Text)
    comments = db.Column(Text)
    recommendations = db.Column(Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='performance_evaluations')
    evaluator = db.relationship('User', backref='conducted_evaluations')
    target_employee = db.relationship('Employee', backref='performance_evaluations')
    target_dog = db.relationship('Dog', backref='performance_evaluations')
    
    def __repr__(self):
        target_name = self.target_employee.name if self.target_employee else self.target_dog.name
        return f'<PerformanceEvaluation {target_name} - {self.rating.value}>'

class AttendanceRecord(db.Model):
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    employee_id = db.Column(get_uuid_column(), db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(20), nullable=False)  # MORNING, EVENING
    
    # Times
    scheduled_start = db.Column(db.Time)
    actual_start = db.Column(db.Time)
    scheduled_end = db.Column(db.Time)
    actual_end = db.Column(db.Time)
    
    # Status
    status = db.Column(db.String(20), default='PRESENT')  # PRESENT, ABSENT, LATE, LEAVE
    leave_type = db.Column(db.String(50))  # ANNUAL, SICK, EMERGENCY
    substitute_employee_id = db.Column(get_uuid_column(), db.ForeignKey('employee.id'))
    
    notes = db.Column(Text)
    
    # Relationships
    employee = db.relationship('Employee', foreign_keys=[employee_id], backref='attendance_records')
    substitute = db.relationship('Employee', foreign_keys=[substitute_employee_id])
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate attendance records
    __table_args__ = (db.UniqueConstraint('employee_id', 'date', 'shift', name='unique_attendance'),)
    
    def __repr__(self):
        return f'<AttendanceRecord {self.employee.name} - {self.date}>'

# Old AuditLog removed - using enhanced version at end of file

# Production System Models (8 sections as requested)

class DogMaturity(db.Model):
    """Section 1: General Information + Section 2: Maturity (البلوغ)"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    dog_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'), nullable=False)
    maturity_date = db.Column(db.Date)  # تاريخ البلوغ
    maturity_status = db.Column(db.Enum(MaturityStatus), default=MaturityStatus.JUVENILE)
    weight_at_maturity = db.Column(db.Float)
    height_at_maturity = db.Column(db.Float)
    notes = db.Column(Text)
    
    # Relationships
    dog = db.relationship('Dog', backref='maturity_record')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HeatCycle(db.Model):
    """Section 3: Heat Cycle (الدورة)"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    dog_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'), nullable=False)
    cycle_number = db.Column(db.Integer, nullable=False)  # رقم الدورة (1، 2، 3...)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    duration_days = db.Column(db.Integer)
    status = db.Column(db.Enum(HeatStatus), default=HeatStatus.IN_HEAT)
    
    # Physical signs
    behavioral_changes = db.Column(Text)
    physical_signs = db.Column(Text)
    appetite_changes = db.Column(db.String(100))
    
    notes = db.Column(Text)
    
    # Relationships
    dog = db.relationship('Dog', backref='heat_cycles')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MatingRecord(db.Model):
    """Section 4: Mating (التزاوج)"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    female_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'), nullable=False)
    male_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'), nullable=False)
    heat_cycle_id = db.Column(get_uuid_column(), db.ForeignKey('heat_cycle.id'), nullable=True)
    
    mating_date = db.Column(db.Date, nullable=False)
    mating_time = db.Column(db.Time)
    location = db.Column(db.String(100))
    supervised_by = db.Column(get_uuid_column(), db.ForeignKey('employee.id'))
    
    # Mating details
    success_rate = db.Column(db.Integer)  # 0-10
    duration_minutes = db.Column(db.Integer)
    behavior_observed = db.Column(Text)
    complications = db.Column(Text)
    
    notes = db.Column(Text)
    
    # Relationships
    female = db.relationship('Dog', foreign_keys=[female_id], backref='matings_as_female')
    male = db.relationship('Dog', foreign_keys=[male_id], backref='matings_as_male')
    heat_cycle = db.relationship('HeatCycle', backref='mating_records')
    supervisor = db.relationship('Employee', backref='supervised_matings')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PregnancyRecord(db.Model):
    """Section 5: Pregnancy (الحمل)"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    mating_record_id = db.Column(get_uuid_column(), db.ForeignKey('mating_record.id'), nullable=False)
    dog_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'), nullable=False)
    
    # Pregnancy timeline
    confirmed_date = db.Column(db.Date)  # تاريخ تأكيد الحمل
    expected_delivery_date = db.Column(db.Date)  # تاريخ الولادة المتوقع
    status = db.Column(db.Enum(PregnancyStatus), default=PregnancyStatus.NOT_PREGNANT)
    
    # Health monitoring
    week_1_checkup = db.Column(JSON, default=dict)  # {weight, appetite, behavior}
    week_2_checkup = db.Column(JSON, default=dict)
    week_3_checkup = db.Column(JSON, default=dict)
    week_4_checkup = db.Column(JSON, default=dict)
    week_5_checkup = db.Column(JSON, default=dict)
    week_6_checkup = db.Column(JSON, default=dict)
    week_7_checkup = db.Column(JSON, default=dict)
    week_8_checkup = db.Column(JSON, default=dict)
    
    # Ultrasound results
    ultrasound_results = db.Column(JSON, default=list)  # [{date, puppies_count, notes}]
    
    # Nutrition and care
    special_diet = db.Column(Text)
    exercise_restrictions = db.Column(Text)
    medications = db.Column(JSON, default=list)
    
    notes = db.Column(Text)
    
    # Relationships
    mating_record = db.relationship('MatingRecord', backref='pregnancy_records')
    dog = db.relationship('Dog', backref='pregnancy_records')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DeliveryRecord(db.Model):
    """Section 6: Delivery/Birth (الولادة)"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    pregnancy_record_id = db.Column(get_uuid_column(), db.ForeignKey('pregnancy_record.id'), nullable=False)
    
    # Delivery details
    delivery_date = db.Column(db.Date, nullable=False)
    delivery_start_time = db.Column(db.Time)
    delivery_end_time = db.Column(db.Time)
    location = db.Column(db.String(100))
    
    # Assistance
    vet_present = db.Column(get_uuid_column(), db.ForeignKey('employee.id'))
    handler_present = db.Column(get_uuid_column(), db.ForeignKey('employee.id'))
    assistance_required = db.Column(db.Boolean, default=False)
    assistance_type = db.Column(Text)  # cesarean, manual assistance, etc.
    
    # Results
    total_puppies = db.Column(db.Integer, default=0)
    live_births = db.Column(db.Integer, default=0)
    stillbirths = db.Column(db.Integer, default=0)
    
    # Complications
    delivery_complications = db.Column(Text)
    mother_condition = db.Column(Text)
    
    notes = db.Column(Text)
    
    # Relationships
    pregnancy_record = db.relationship('PregnancyRecord', backref='delivery_records')
    vet = db.relationship('Employee', foreign_keys=[vet_present], backref='assisted_deliveries')
    handler = db.relationship('Employee', foreign_keys=[handler_present], backref='handled_deliveries')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PuppyRecord(db.Model):
    """Section 7: Puppies (الجراء)"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    delivery_record_id = db.Column(get_uuid_column(), db.ForeignKey('delivery_record.id'), nullable=False)
    
    # Puppy identification
    puppy_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3...
    name = db.Column(db.String(100))
    temporary_id = db.Column(db.String(20))  # temporary ID until official registration
    gender = db.Column(db.Enum(DogGender), nullable=False)
    
    # Birth details
    birth_weight = db.Column(db.Float)
    birth_time = db.Column(db.Time)
    birth_order = db.Column(db.Integer)
    
    # Health status
    alive_at_birth = db.Column(db.Boolean, default=True)
    current_status = db.Column(db.String(50), default='صحي ونشط')  # صحي ونشط، ضعيف، متوفي، مريض
    
    # Physical characteristics
    color = db.Column(db.String(50))
    markings = db.Column(Text)
    birth_defects = db.Column(Text)
    
    # Weekly weight tracking
    week_1_weight = db.Column(db.Float)
    week_2_weight = db.Column(db.Float)
    week_3_weight = db.Column(db.Float)
    week_4_weight = db.Column(db.Float)
    week_5_weight = db.Column(db.Float)
    week_6_weight = db.Column(db.Float)
    week_7_weight = db.Column(db.Float)
    week_8_weight = db.Column(db.Float)
    
    # Weaning and placement
    weaning_date = db.Column(db.Date)
    placement_date = db.Column(db.Date)
    placement_location = db.Column(db.String(100))
    
    # Link to adult dog record (if kept in program)
    adult_dog_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'))
    
    notes = db.Column(Text)
    
    # Relationships
    delivery_record = db.relationship('DeliveryRecord', backref='puppies')
    adult_dog = db.relationship('Dog', backref='puppy_record')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PuppyTraining(db.Model):
    """Section 8: Puppy Training (تدريب الجراء)"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    puppy_id = db.Column(get_uuid_column(), db.ForeignKey('puppy_record.id'), nullable=False)
    trainer_id = db.Column(get_uuid_column(), db.ForeignKey('employee.id'), nullable=False)
    
    # Training details
    training_name = db.Column(db.String(200), nullable=False)  # اسم التدريب
    training_type = db.Column(db.Enum(TrainingCategory), nullable=False)  # نوع التدريب
    session_date = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # minutes
    
    # Age-appropriate training
    puppy_age_weeks = db.Column(db.Integer)
    developmental_stage = db.Column(db.String(50))  # socialization, basic commands, etc.
    
    # Performance
    success_rating = db.Column(db.Integer, nullable=False)  # 0-10
    skills_learned = db.Column(JSON, default=list)  # ["sit", "stay", "come"]
    behavior_observations = db.Column(Text)
    
    # Environment
    location = db.Column(db.String(100))
    weather_conditions = db.Column(db.String(100))
    equipment_used = db.Column(JSON, default=list)
    
    # Progress tracking
    previous_skills = db.Column(JSON, default=list)
    new_skills_acquired = db.Column(JSON, default=list)
    areas_for_improvement = db.Column(Text)
    
    notes = db.Column(Text)
    
    # Relationships
    puppy = db.relationship('PuppyRecord', backref='training_sessions')
    trainer = db.relationship('Employee', backref='puppy_training_sessions')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PuppyTraining {self.training_name} - {self.puppy.name}>'


# ============================================================================
# ATTENDANCE SYSTEM MODELS
# ============================================================================

class ProjectShift(db.Model):
    """Project shifts for attendance tracking"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # Morning, Evening, Night, or custom
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='shifts')
    
    def __repr__(self):
        return f'<ProjectShift {self.name} - {self.project.name}>'

class ProjectShiftAssignment(db.Model):
    """Assignment of employees/dogs to specific shifts"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    shift_id = db.Column(get_uuid_column(), db.ForeignKey('project_shift.id'), nullable=False)
    entity_type = db.Column(db.Enum(EntityType), nullable=False)
    entity_id = db.Column(get_uuid_column(), nullable=False)  # Points to employee.id or dog.id
    is_active = db.Column(db.Boolean, default=True)
    
    assigned_date = db.Column(db.Date, default=date.today)
    notes = db.Column(Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    shift = db.relationship('ProjectShift', backref='assignments')
    
    # Constraint to prevent duplicate assignments
    __table_args__ = (
        db.UniqueConstraint('shift_id', 'entity_type', 'entity_id', name='unique_shift_entity_assignment'),
    )
    
    def get_entity_name(self):
        """Get the name of the assigned entity (employee or dog)"""
        if self.entity_type == EntityType.EMPLOYEE:
            employee = Employee.query.get(self.entity_id)
            return employee.name if employee else "Unknown Employee"
        elif self.entity_type == EntityType.DOG:
            dog = Dog.query.get(self.entity_id)
            return dog.name if dog else "Unknown Dog"
        return "Unknown"
    
    def get_entity_code(self):
        """Get the code/ID of the assigned entity"""
        if self.entity_type == EntityType.EMPLOYEE:
            employee = Employee.query.get(self.entity_id)
            return employee.employee_id if employee else "N/A"
        elif self.entity_type == EntityType.DOG:
            dog = Dog.query.get(self.entity_id)
            return dog.code if dog else "N/A"
        return "N/A"
    
    def __repr__(self):
        return f'<ProjectShiftAssignment {self.get_entity_name()} -> {self.shift.name}>'

class ProjectAttendance(db.Model):
    """Attendance records for projects"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=False)
    shift_id = db.Column(get_uuid_column(), db.ForeignKey('project_shift.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    entity_type = db.Column(db.Enum(EntityType), nullable=False)
    entity_id = db.Column(get_uuid_column(), nullable=False)  # Points to employee.id or dog.id
    
    # Attendance status
    status = db.Column(db.Enum(AttendanceStatus), nullable=False)
    absence_reason = db.Column(db.Enum(AbsenceReason), nullable=True)  # Only for ABSENT status
    late_reason = db.Column(Text, nullable=True)  # Only for LATE status
    notes = db.Column(Text)
    
    # Time tracking
    check_in_time = db.Column(db.Time, nullable=True)
    check_out_time = db.Column(db.Time, nullable=True)
    
    # Recorded by
    recorded_by_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='attendance_records')
    shift = db.relationship('ProjectShift', backref='attendance_records')
    recorded_by = db.relationship('User', backref='recorded_attendance')
    
    # Constraints
    __table_args__ = (
        # Only one attendance record per entity per shift per date
        db.UniqueConstraint('project_id', 'shift_id', 'date', 'entity_type', 'entity_id', 
                          name='unique_attendance_record'),
        # Check constraint: absence_reason required when status is ABSENT
        db.CheckConstraint(
            "(status != 'ABSENT') OR (status = 'ABSENT' AND absence_reason IS NOT NULL)",
            name='absence_reason_required_for_absent'
        ),
    )
    
    def get_entity_name(self):
        """Get the name of the entity (employee or dog)"""
        if self.entity_type == EntityType.EMPLOYEE:
            employee = Employee.query.get(self.entity_id)
            return employee.name if employee else "Unknown Employee"
        elif self.entity_type == EntityType.DOG:
            dog = Dog.query.get(self.entity_id)
            return dog.name if dog else "Unknown Dog"
        return "Unknown"
    
    def get_entity_code(self):
        """Get the code/ID of the entity"""
        if self.entity_type == EntityType.EMPLOYEE:
            employee = Employee.query.get(self.entity_id)
            return employee.employee_id if employee else "N/A"
        elif self.entity_type == EntityType.DOG:
            dog = Dog.query.get(self.entity_id)
            return dog.code if dog else "N/A"
        return "N/A"
    
    def __repr__(self):
        return f'<ProjectAttendance {self.get_entity_name()} - {self.status.value} on {self.date}>'
        
    def get_status_display(self):
        """Get Arabic display text for status"""
        status_map = {
            'PRESENT': 'حاضر',
            'ABSENT': 'غائب', 
            'LATE': 'متأخر'
        }
        return status_map.get(self.status.value, self.status.value)
    
    def get_absence_reason_display(self):
        """Get Arabic display text for absence reason"""
        reason_map = {
            'ANNUAL': 'سنوية',
            'SICK': 'مرضية',
            'EMERGENCY': 'طارئة',
            'OTHER': 'أخرى'
        }
        return reason_map.get(self.absence_reason.value, self.absence_reason.value) if self.absence_reason else ''


# Enhanced permission system - granular subsection permissions
class PermissionType(Enum):
    VIEW = "VIEW"
    CREATE = "CREATE"
    EDIT = "EDIT"
    DELETE = "DELETE"
    EXPORT = "EXPORT"
    ASSIGN = "ASSIGN"
    APPROVE = "APPROVE"

class SubPermission(db.Model):
    """Ultra-granular permissions for PROJECT_MANAGER users"""
    __tablename__ = 'sub_permissions'
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=False)
    section = db.Column(db.String(50), nullable=False)       # e.g., "Dogs", "Employees", "Projects"
    subsection = db.Column(db.String(100), nullable=False)   # e.g., "View Dog List", "Upload Medical Records"
    permission_type = db.Column(db.Enum(PermissionType), nullable=False)  # VIEW/CREATE/EDIT/DELETE/EXPORT/ASSIGN/APPROVE
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=True)  # Null for global permissions
    is_granted = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='sub_permissions')
    project = db.relationship('Project', backref='sub_permissions')
    
    # Ensure unique permission record per user-section-subsection-type-project combination
    __table_args__ = (
        db.UniqueConstraint('user_id', 'section', 'subsection', 'permission_type', 'project_id', 
                          name='unique_sub_permission'),
    )
    
    def __repr__(self):
        project_info = f" (Project: {self.project_id})" if self.project_id else " (Global)"
        return f'<SubPermission {self.user.username}: {self.section}->{self.subsection} ({self.permission_type.value}){project_info}>'

class PermissionAuditLog(db.Model):
    """Audit trail for permission changes"""
    __tablename__ = 'permission_audit_logs'
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    
    # Who made the change
    changed_by_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=False)
    
    # Target user whose permissions were changed
    target_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=False)
    
    # Permission details
    section = db.Column(db.String(50), nullable=False)
    subsection = db.Column(db.String(100), nullable=False)
    permission_type = db.Column(db.Enum(PermissionType), nullable=False)
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=True)
    
    # Change details
    old_value = db.Column(db.Boolean, nullable=False)
    new_value = db.Column(db.Boolean, nullable=False)
    
    # Metadata
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    changed_by = db.relationship('User', foreign_keys=[changed_by_user_id], backref='permission_changes_made')
    target_user = db.relationship('User', foreign_keys=[target_user_id], backref='permission_changes_received')
    project = db.relationship('Project', backref='permission_audit_logs')
    
    def __repr__(self):
        return f'<PermissionAuditLog {self.changed_by.username} -> {self.target_user.username}: {self.section}->{self.subsection}>'

# Legacy permission model - keeping for backward compatibility during transition
class ProjectManagerPermission(db.Model):
    """Legacy granular permissions for PROJECT_MANAGER users per project"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=False)
    
    # Permission toggles - all default to True for PROJECT_MANAGER
    can_manage_assignments = db.Column(db.Boolean, default=True)
    can_manage_shifts = db.Column(db.Boolean, default=True)
    can_manage_attendance = db.Column(db.Boolean, default=True)
    can_manage_training = db.Column(db.Boolean, default=True)
    can_manage_incidents = db.Column(db.Boolean, default=True)
    can_manage_performance = db.Column(db.Boolean, default=True)
    can_view_veterinary = db.Column(db.Boolean, default=True)
    can_view_breeding = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='manager_permissions')
    
    # Ensure unique permission record per user-project combination
    __table_args__ = (
        db.UniqueConstraint('user_id', 'project_id', name='unique_user_project_permission'),
    )
    
    def __repr__(self):
        return f'<ProjectManagerPermission User{self.user_id} -> Project{self.project_id}>'

class AuditLog(db.Model):
    """Comprehensive audit logging for all user actions"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.Enum(AuditAction), nullable=False)
    
    # Target information
    target_type = db.Column(db.String(50))  # Dog, Employee, Project, etc.
    target_id = db.Column(get_uuid_column())  # ID of the target object
    target_name = db.Column(db.String(200))  # Name for easy identification
    
    # Action details
    description = db.Column(Text)
    old_values = db.Column(JSON)  # Previous state
    new_values = db.Column(JSON)  # New state
    
    # Session information
    ip_address = db.Column(db.String(45))  # Support IPv6
    user_agent = db.Column(Text)
    session_id = db.Column(db.String(255))
    
    # Metadata (using different name to avoid SQLAlchemy reserved word)
    extra_data = db.Column(JSON, default=dict)  # Additional context
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.user.username} - {self.action.value} - {self.target_type}>'

class AttendanceDay(db.Model):
    """Unified global attendance tracking - only for employees NOT assigned to active projects"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    employee_id = db.Column(get_uuid_column(), db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(AttendanceStatus), nullable=False, default=AttendanceStatus.ABSENT)
    note = db.Column(Text)
    source = db.Column(db.String(16), default='global', nullable=False)  # 'global' or 'project'
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'))  # Set when source='project'
    locked = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = db.relationship('Employee', backref='attendance_days')
    project = db.relationship('Project', backref='attendance_days')
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'date', name='unique_employee_date'),
        db.Index('ix_attendance_day_date', 'date'),
        db.Index('ix_attendance_day_employee_date', 'employee_id', 'date'),
        # Constraint: project_id required when source='project'
        db.CheckConstraint(
            "(source != 'project') OR (source = 'project' AND project_id IS NOT NULL)",
            name='project_id_required_for_project_source'
        ),
    )
    
    def __repr__(self):
        return f'<AttendanceDay {self.employee.name} - {self.date} - {self.status.value}>'


# ============================================================================
# STANDALONE ATTENDANCE SYSTEM MODELS (NOT PROJECT-SPECIFIC)
# ============================================================================

class Shift(db.Model):
    """Standalone shifts for general attendance tracking (not project-specific)"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    name = db.Column(db.String(100), nullable=False)  # Morning, Evening, Night, or custom
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Shift {self.name} ({self.start_time} - {self.end_time})>'

class ShiftAssignment(db.Model):
    """Assignment of employees/dogs to standalone shifts"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    shift_id = db.Column(get_uuid_column(), db.ForeignKey('shift.id'), nullable=False)
    entity_type = db.Column(db.Enum(EntityType), nullable=False)
    entity_id = db.Column(get_uuid_column(), nullable=False)  # Points to employee.id or dog.id
    is_active = db.Column(db.Boolean, default=True)
    
    assigned_date = db.Column(db.Date, default=date.today)
    notes = db.Column(Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    shift = db.relationship('Shift', backref='assignments')
    
    # Constraint to prevent duplicate assignments
    __table_args__ = (
        db.UniqueConstraint('shift_id', 'entity_type', 'entity_id', name='unique_standalone_shift_entity_assignment'),
    )
    
    def get_entity_name(self):
        """Get the name of the assigned entity (employee or dog)"""
        if self.entity_type == EntityType.EMPLOYEE:
            employee = Employee.query.get(self.entity_id)
            return employee.name if employee else "Unknown Employee"
        elif self.entity_type == EntityType.DOG:
            dog = Dog.query.get(self.entity_id)
            return dog.name if dog else "Unknown Dog"
        return "Unknown"
    
    def get_entity_code(self):
        """Get the code/ID of the assigned entity"""
        if self.entity_type == EntityType.EMPLOYEE:
            employee = Employee.query.get(self.entity_id)
            return employee.employee_id if employee else "N/A"
        elif self.entity_type == EntityType.DOG:
            dog = Dog.query.get(self.entity_id)
            return dog.code if dog else "N/A"
        return "N/A"
    
    def __repr__(self):
        return f'<ShiftAssignment {self.get_entity_name()} -> {self.shift.name}>'

class Attendance(db.Model):
    """Standalone attendance records (not project-specific)"""
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    shift_id = db.Column(get_uuid_column(), db.ForeignKey('shift.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    entity_type = db.Column(db.Enum(EntityType), nullable=False)
    entity_id = db.Column(get_uuid_column(), nullable=False)  # Points to employee.id or dog.id
    
    # Attendance status
    status = db.Column(db.Enum(AttendanceStatus), nullable=False)
    absence_reason = db.Column(db.Enum(AbsenceReason), nullable=True)  # Only for ABSENT status
    late_reason = db.Column(Text, nullable=True)  # Only for LATE status
    notes = db.Column(Text)
    
    # Time tracking
    check_in_time = db.Column(db.Time, nullable=True)
    check_out_time = db.Column(db.Time, nullable=True)
    
    # Recorded by
    recorded_by_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    shift = db.relationship('Shift', backref='attendance_records')
    recorded_by = db.relationship('User', backref='recorded_standalone_attendance')
    
    # Constraints
    __table_args__ = (
        # Only one attendance record per entity per shift per date
        db.UniqueConstraint('shift_id', 'date', 'entity_type', 'entity_id', 
                          name='unique_standalone_attendance_record'),
        # Check constraint: absence_reason required when status is ABSENT
        db.CheckConstraint(
            "(status != 'ABSENT') OR (status = 'ABSENT' AND absence_reason IS NOT NULL)",
            name='standalone_absence_reason_required_for_absent'
        ),
    )
    
    def get_entity_name(self):
        """Get the name of the entity (employee or dog)"""
        if self.entity_type == EntityType.EMPLOYEE:
            employee = Employee.query.get(self.entity_id)
            return employee.name if employee else "Unknown Employee"
        elif self.entity_type == EntityType.DOG:
            dog = Dog.query.get(self.entity_id)
            return dog.name if dog else "Unknown Dog"
        return "Unknown"
    
    def get_entity_code(self):
        """Get the code/ID of the entity"""
        if self.entity_type == EntityType.EMPLOYEE:
            employee = Employee.query.get(self.entity_id)
            return employee.employee_id if employee else "N/A"
        elif self.entity_type == EntityType.DOG:
            dog = Dog.query.get(self.entity_id)
            return dog.code if dog else "N/A"
        return "N/A"
    
    def __repr__(self):
        return f'<Attendance {self.get_entity_name()} - {self.status.value} on {self.date}>'
        
    def get_status_display(self):
        """Get Arabic display text for status"""
        status_map = {
            'PRESENT': 'حاضر',
            'ABSENT': 'غائب', 
            'LATE': 'متأخر'
        }
        return status_map.get(self.status.value, self.status.value)
    
    def get_absence_reason_display(self):
        """Get Arabic display text for absence reason"""
        if self.absence_reason:
            return self.absence_reason.value
        return ''


# All model methods are properly defined within their respective classes

# ---------- Breeding Enums with ARABIC VALUES ----------
class PrepMethod(Enum):
    BOILED = "غليان"
    STEAMED = "تبخير"
    SOAKED = "نقع"
    OTHER = "أخرى"

class BodyConditionScale(Enum):  # optional per meal if noted
    VERY_THIN   = "نحيف جدًا (1)"
    THIN        = "نحيف (2)"
    BELOW_IDEAL = "أقل من المثالي (3)"
    NEAR_IDEAL  = "قريب من المثالي (4)"
    IDEAL       = "مثالي (5)"
    ABOVE_IDEAL = "فوق المثالي (6)"
    FULL        = "ممتلئ (7)"
    OBESE       = "سمين (8)"
    VERY_OBESE  = "سمين جدًا (9)"

# ---------- FeedingLog table (per‑meal) ----------
class FeedingLog(db.Model):
    __tablename__ = "feeding_log"

    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)

    project_id = db.Column(get_uuid_column(), db.ForeignKey("project.id", ondelete="CASCADE"), nullable=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)

    dog_id = db.Column(get_uuid_column(), db.ForeignKey("dog.id", ondelete="CASCADE"), nullable=False)
    recorder_employee_id = db.Column(get_uuid_column(), db.ForeignKey("employee.id", ondelete="SET NULL"), nullable=True)

    # Meal type — checkboxes (both can be True if mixed)
    meal_type_fresh = db.Column(db.Boolean, nullable=False, default=False)  # طازج
    meal_type_dry   = db.Column(db.Boolean, nullable=False, default=False)  # مجفف

    meal_name   = db.Column(db.String(120), nullable=True)                 # اسم الوجبة
    prep_method = db.Column(db.Enum(PrepMethod), nullable=True)            # طريقة التحضير (Arabic values)

    grams    = db.Column(db.Integer, nullable=True)                        # كمية الوجبة (غم)
    water_ml = db.Column(db.Integer, nullable=True)                        # ماء الشرب (مل)

    supplements   = db.Column(JSON, nullable=True)                         # [{"name":"اسم المكمل","qty":"5 مل"}]
    body_condition = db.Column(db.Enum(BodyConditionScale), nullable=True) # كتلة الجسم (Arabic values)
    notes = db.Column(db.Text, nullable=True)

    created_by_user_id = db.Column(get_uuid_column(), db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', backref='feeding_logs')
    dog = db.relationship('Dog', backref='feeding_logs')
    recorder_employee = db.relationship('Employee', backref='feeding_logs')
    created_by_user = db.relationship('User', backref='feeding_logs')

    __table_args__ = (
        db.Index("ix_feeding_log_project_date", "project_id", "date"),
        db.Index("ix_feeding_log_dog_datetime", "dog_id", "date", "time"),
    )
    
    def __repr__(self):
        return f'<FeedingLog {self.id}: {self.dog_id} on {self.date} at {self.time}>'


# ---------- DailyCheckupLog ----------
class DailyCheckupLog(db.Model):
    __tablename__ = "daily_checkup_log"

    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)

    project_id = db.Column(get_uuid_column(), db.ForeignKey("project.id", ondelete="CASCADE"), nullable=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)

    dog_id = db.Column(get_uuid_column(), db.ForeignKey("dog.id", ondelete="CASCADE"), nullable=False)
    examiner_employee_id = db.Column(get_uuid_column(), db.ForeignKey("employee.id", ondelete="SET NULL"), nullable=True)

    # Body parts (using English column names for SQLite compatibility, values will be Arabic strings)
    eyes = db.Column(db.String(50), nullable=True)      # العين
    ears = db.Column(db.String(50), nullable=True)      # الأذن
    nose = db.Column(db.String(50), nullable=True)      # الأنف
    front_legs = db.Column(db.String(50), nullable=True)  # الأطراف الأمامية
    hind_legs = db.Column(db.String(50), nullable=True)   # الأطراف الخلفية
    coat = db.Column(db.String(50), nullable=True)      # الشعر
    tail = db.Column(db.String(50), nullable=True)      # الذيل

    severity = db.Column(db.String(50), nullable=True)  # شدة الحالة
    symptoms = db.Column(db.Text, nullable=True)          # الأعراض المرضية إن وجدت
    initial_diagnosis = db.Column(db.Text, nullable=True)  # تشخيص أولي/ملاحظة
    suggested_treatment = db.Column(db.Text, nullable=True) # علاج أو إجراء مقترح
    notes = db.Column(db.Text, nullable=True)              # ملاحظات

    created_by_user_id = db.Column(get_uuid_column(), db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', backref='daily_checkups')
    dog = db.relationship('Dog', backref='daily_checkups')
    examiner_employee = db.relationship('Employee', backref='daily_checkups')
    created_by_user = db.relationship('User', backref='daily_checkups')

    def __repr__(self):
        return f'<DailyCheckupLog {self.id}: {self.dog_id} on {self.date} at {self.time}>'


# ---------- Arabic enums for Excretion (store Arabic strings) ----------
class StoolColor(Enum):
    شفاف_او_فاتح = "شفاف/فاتح"
    اصفر = "أصفر"
    بني = "بني"
    داكن = "داكن"
    اخضر = "أخضر"
    وردي_دموي = "وردي/دموي"
    اخرى = "أخرى"

class StoolConsistency(Enum):
    سائل = "سائل"
    لين = "لين"
    طبيعي_مشكّل = "طبيعي مُشكّل"
    صلب = "صلب"
    شديد_الصلابة = "شديد الصلابة"

class StoolContent(Enum):
    طبيعي = "طبيعي"
    مخاط = "مخاط"
    دم = "دم"
    طفيليات_او_ديدان = "طفيليات/ديدان"
    بقايا_طعام = "بقايا طعام"
    جسم_غريب = "جسم غريب"
    عشب = "عشب"
    اخرى = "أخرى"

class UrineColor(Enum):
    شفاف = "شفاف"
    اصفر_فاتح = "أصفر فاتح"
    اصفر = "أصفر"
    اصفر_غامق = "أصفر غامق"
    بني_مصفر = "بني مصفر"
    وردي_دموي = "وردي/دموي"

class VomitColor(Enum):
    شفاف = "شفاف"
    اصفر = "أصفر"
    بني = "بني"
    اخضر = "أخضر"
    وردي_دموي = "وردي/دموي"
    رغوي = "رغوي"
    اخرى = "أخرى"

class ExcretionPlace(Enum):
    داخل_البيت = "داخل البيت"
    خارج_البيت = "خارج البيت"
    القفص = "القفص"
    المكان_المخصص = "المكان المخصص"
    اخرى = "أخرى"

# ---------- ExcretionLog table (per observation) ----------
class ExcretionLog(db.Model):
    __tablename__ = "excretion_log"

    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)

    project_id = db.Column(get_uuid_column(), db.ForeignKey("project.id", ondelete="CASCADE"), nullable=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)

    dog_id = db.Column(get_uuid_column(), db.ForeignKey("dog.id", ondelete="CASCADE"), nullable=False)
    recorder_employee_id = db.Column(get_uuid_column(), db.ForeignKey("employee.id", ondelete="SET NULL"), nullable=True)

    # --- Stool (any may be null if not observed) ---
    stool_color = db.Column(db.String(50), nullable=True)              # لون البراز
    stool_consistency = db.Column(db.String(50), nullable=True)        # قوام/شكل البراز
    stool_content = db.Column(db.String(50), nullable=True)            # محتوى البراز
    constipation = db.Column(db.Boolean, nullable=False, default=False)      # إمساك
    stool_place = db.Column(db.String(50), nullable=True)              # مكان التبرز
    stool_notes = db.Column(db.Text, nullable=True)

    # --- Urine ---
    urine_color = db.Column(db.String(50), nullable=True)              # لون البول
    urine_notes = db.Column(db.Text, nullable=True)

    # --- Vomit ---
    vomit_color = db.Column(db.String(50), nullable=True)              # لون القيء
    vomit_count = db.Column(db.Integer, nullable=True)                       # عدد مرات القيء (>=0)
    vomit_notes = db.Column(db.Text, nullable=True)

    # Audit
    created_by_user_id = db.Column(get_uuid_column(), db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', backref='excretion_logs')
    dog = db.relationship('Dog', backref='excretion_logs')
    recorder_employee = db.relationship('Employee', backref='excretion_logs')
    created_by_user = db.relationship('User', backref='excretion_logs')

    __table_args__ = (
        db.Index("ix_excretion_project_date", "project_id", "date"),
        db.Index("ix_excretion_dog_datetime", "dog_id", "date", "time"),
    )

    def __repr__(self):
        return f'<ExcretionLog {self.id}: {self.dog_id} on {self.date} at {self.time}>'


# ---------- GroomingLog table (per grooming action/event) ----------
class GroomingLog(db.Model):
    __tablename__ = "grooming_log"

    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)

    project_id = db.Column(get_uuid_column(), db.ForeignKey("project.id", ondelete="CASCADE"), nullable=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)

    dog_id = db.Column(get_uuid_column(), db.ForeignKey("dog.id", ondelete="CASCADE"), nullable=False)
    recorder_employee_id = db.Column(get_uuid_column(), db.ForeignKey("employee.id", ondelete="SET NULL"), nullable=True)

    # Actions - using English enum values, Arabic display handled in UI
    washed_bathed = db.Column(db.Enum(GroomingYesNo), nullable=True)             # غسل الكلب
    shampoo_type = db.Column(db.String(120), nullable=True)                      # نوع الشامبو
    brushing = db.Column(db.Enum(GroomingYesNo), nullable=True)                  # تمشيط
    nail_trimming = db.Column(db.Enum(GroomingYesNo), nullable=True)             # قص الأظافر
    teeth_brushing = db.Column(db.Enum(GroomingYesNo), nullable=True)            # فرش الأسنان
    ear_cleaning = db.Column(db.Enum(GroomingYesNo), nullable=True)              # تنظيف الأذن
    eye_cleaning = db.Column(db.Enum(GroomingYesNo), nullable=True)              # تنظيف العين

    cleanliness_score = db.Column(db.Enum(GroomingCleanlinessScore), nullable=True) # نظافة عامة 1-5
    notes = db.Column(db.Text, nullable=True)                                    # ملاحظات

    created_by_user_id = db.Column(get_uuid_column(), db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', backref='grooming_logs')
    dog = db.relationship('Dog', backref='grooming_logs')
    recorder_employee = db.relationship('Employee', backref='grooming_logs')
    created_by_user = db.relationship('User', backref='grooming_logs')

    __table_args__ = (
        db.Index("ix_grooming_project_date", "project_id", "date"),
        db.Index("ix_grooming_dog_datetime", "dog_id", "date", "time"),
        db.UniqueConstraint("project_id","dog_id","date","time", name="uq_grooming_project_dog_dt"),
    )

    def __repr__(self):
        return f'<GroomingLog {self.id}: {self.dog_id} on {self.date} at {self.time}>'


# ---------- DewormingLog (per administration) ----------
class DewormingLog(db.Model):
    __tablename__ = "deworming_log"

    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)

    project_id = db.Column(get_uuid_column(), db.ForeignKey("project.id", ondelete="CASCADE"), nullable=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)

    dog_id = db.Column(get_uuid_column(), db.ForeignKey("dog.id", ondelete="CASCADE"), nullable=False)
    specialist_employee_id = db.Column(get_uuid_column(), db.ForeignKey("employee.id", ondelete="SET NULL"), nullable=True)

    dog_weight_kg = db.Column(db.Float, nullable=True)                        # وزن الكلب كغم - > 0 if provided
    product_name = db.Column(db.String(120), nullable=True)                   # اسم المنتج - e.g., Drontal
    active_ingredient = db.Column(db.String(120), nullable=True)              # المادة الفعالة - e.g., praziquantel
    standard_dose_mg_per_kg = db.Column(db.Float, nullable=True)              # جرعة قياسية ملغم لكل كغم - mg/kg rule (optional)
    calculated_dose_mg = db.Column(db.Float, nullable=True)                   # جرعة محسوبة ملغم - auto-calc if weight & rule present

    administered_amount = db.Column(db.Float, nullable=True)                  # كمية معطاة - numeric amount actually given
    amount_unit = db.Column(db.String(20), nullable=True)                     # وحدة الكمية - مل | ملغم | قرص
    administration_route = db.Column(db.String(20), nullable=True)            # طريقة الإعطاء - فموي | موضعي | حقن

    batch_number = db.Column(db.String(60), nullable=True)                    # رقم التشغيلة - batch/lot
    expiry_date = db.Column(db.Date, nullable=True)                           # تاريخ الانتهاء - expiry date

    adverse_reaction = db.Column(db.String(20), nullable=True)                # تفاعل سلبي - adverse reaction category
    notes = db.Column(db.Text, nullable=True)                                 # ملاحظات

    next_due_date = db.Column(db.Date, nullable=True)                         # تاريخ الجرعة القادمة - next due date (optional)

    created_by_user_id = db.Column(get_uuid_column(), db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', backref='deworming_logs')
    dog = db.relationship('Dog', backref='deworming_logs')
    specialist_employee = db.relationship('Employee', backref='deworming_logs')
    created_by_user = db.relationship('User', backref='deworming_logs')

    __table_args__ = (
        db.Index("ix_deworming_project_date", "project_id", "date"),
        db.Index("ix_deworming_dog_datetime", "dog_id", "date", "time"),
        db.UniqueConstraint("project_id","dog_id","date","time", name="uq_deworming_project_dog_dt"),
    )

    def __repr__(self):
        return f'<DewormingLog {self.id}: {self.dog_id} on {self.date} at {self.time}>'


# ---------- CleaningLog (per dog action) ----------
class CleaningLog(db.Model):
    __tablename__ = "cleaning_log"

    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)

    project_id = db.Column(get_uuid_column(), db.ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)

    dog_id = db.Column(get_uuid_column(), db.ForeignKey("dog.id", ondelete="CASCADE"), nullable=False)
    recorder_employee_id = db.Column(get_uuid_column(), db.ForeignKey("employee.id", ondelete="SET NULL"), nullable=True)

    # Target area info (using ASCII column names)
    area_type = db.Column(db.String(50), nullable=True)                   # نوع المكان - بيت الكلب | القفص | ساحة خارجية | ...
    cage_house_number = db.Column(db.String(60), nullable=True)           # رقم البيت او القفص - kennel/cage number
    alternate_place = db.Column(db.String(120), nullable=True)            # مكان بديل - alternate place used

    # Actions (per your spec) - using ASCII column names
    cleaned_house = db.Column(db.String(10), nullable=True)               # تنظيف البيت - sweeping/cleaning
    washed_house = db.Column(db.String(10), nullable=True)                # غسل البيت - washing house
    disinfected_house = db.Column(db.String(10), nullable=True)           # تعقيم البيت - disinfecting house

    group_disinfection = db.Column(db.String(10), nullable=True)          # تطهير بيوت مجموعة كلاب - group disinfection
    group_description = db.Column(db.String(120), nullable=True)          # وصف المجموعة - e.g., "الصف A" or "مجموعة 1"

    materials_used = db.Column(JSON, nullable=True)                       # المواد المستخدمة - list like [{"name":"هيبوكلوريت","qty":"100 مل"}]
    notes = db.Column(Text, nullable=True)                                # ملاحظات

    # For cadence computation (not persisted as enums, computed in API)
    created_by_user_id = db.Column(get_uuid_column(), db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', backref='cleaning_logs')
    dog = db.relationship('Dog', backref='cleaning_logs')
    recorder_employee = db.relationship('Employee', backref='cleaning_logs')
    created_by_user = db.relationship('User', backref='cleaning_logs')

    __table_args__ = (
        db.Index("ix_cleaning_project_date", "project_id", "date"),
        db.Index("ix_cleaning_dog_datetime", "dog_id", "date", "time"),
        db.UniqueConstraint("project_id","dog_id","date","time", name="uq_cleaning_project_dog_dt"),
    )

    def __repr__(self):
        return f'<CleaningLog {self.id}: {self.dog_id} on {self.date} at {self.time}>'


# ---------- BreedingTrainingActivity (Training activities under Breeding module) ----------
class BreedingTrainingActivity(db.Model):
    __tablename__ = "breeding_training_activity"

    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)

    # Optional project assignment (nullable for compatibility with PROJECT_MANAGER scoping)
    project_id = db.Column(get_uuid_column(), db.ForeignKey("project.id", ondelete="CASCADE"), nullable=True)
    
    # Core training session data
    dog_id = db.Column(get_uuid_column(), db.ForeignKey("dog.id", ondelete="CASCADE"), nullable=False)
    trainer_id = db.Column(get_uuid_column(), db.ForeignKey("employee.id", ondelete="SET NULL"), nullable=False)
    
    session_date = db.Column(db.DateTime, nullable=False)
    
    # Training classification
    category = db.Column(db.Enum(TrainingCategory), nullable=False)
    
    # Training subtypes (Arabic-first enums)
    subtype_socialization = db.Column(db.Enum(SocializationType), nullable=True)  # التطبيع
    subtype_ball = db.Column(db.Enum(BallWorkType), nullable=True)               # الكرة
    
    # Session details
    subject = db.Column(Text, nullable=False)                    # موضوع التدريب
    duration = db.Column(db.Integer, nullable=False)             # minutes - مدة التدريب بالدقائق
    duration_days = db.Column(db.Integer, nullable=True)         # days - مدة التدريب بالأيام (اختياري)
    success_rating = db.Column(db.Integer, nullable=False)       # 1-5 scale - تقييم النجاح
    
    # Environment and context
    location = db.Column(db.String(100), nullable=True)          # مكان التدريب
    weather_conditions = db.Column(db.String(100), nullable=True) # أحوال الطقس
    equipment_used = db.Column(JSON, default=list, nullable=True) # المعدات المستخدمة
    notes = db.Column(Text, nullable=True)                       # ملاحظات
    
    # Audit trail
    created_by_user_id = db.Column(get_uuid_column(), db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', backref='breeding_training_activities')
    dog = db.relationship('Dog', backref='breeding_training_activities')
    trainer = db.relationship('Employee', backref='breeding_training_activities')
    created_by_user = db.relationship('User', backref='breeding_training_activities')

    # Database constraints and indexes
    __table_args__ = (
        db.Index("ix_breeding_training_project_date", "project_id", "session_date"),
        db.Index("ix_breeding_training_dog_date", "dog_id", "session_date"),
        db.Index("ix_breeding_training_trainer_date", "trainer_id", "session_date"),
        db.CheckConstraint('success_rating >= 1 AND success_rating <= 5', name='valid_success_rating'),
        db.CheckConstraint('duration > 0', name='positive_duration'),
    )

    def __repr__(self):
        return f'<BreedingTrainingActivity {self.id}: {self.dog.name if self.dog else "N/A"} - {self.subject[:50]}>'


# ---------- CaretakerDailyLog ----------
class CaretakerDailyLog(db.Model):
    """
    Daily caretaker/breeder report log for house and dog maintenance activities
    تقرير يومي للمربي - تسجيل أنشطة صيانة البيت والكلب
    """
    __tablename__ = "caretaker_daily_log"

    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    
    # Core identifiers
    date = db.Column(db.Date, nullable=False)
    project_id = db.Column(get_uuid_column(), db.ForeignKey("project.id", ondelete="CASCADE"), nullable=True)
    dog_id = db.Column(get_uuid_column(), db.ForeignKey("dog.id", ondelete="CASCADE"), nullable=False)
    caretaker_employee_id = db.Column(get_uuid_column(), db.ForeignKey("employee.id", ondelete="SET NULL"), nullable=True)
    
    # House/Kennel information
    kennel_code = db.Column(db.String(50), nullable=True)  # البيت
    
    # HOUSE group activities (البيت)
    house_clean = db.Column(db.Boolean, nullable=False, default=False)        # نظافة
    house_vacuum = db.Column(db.Boolean, nullable=False, default=False)       # مكنس، شفاط
    house_tap_clean = db.Column(db.Boolean, nullable=False, default=False)    # الحنفي
    house_drain_clean = db.Column(db.Boolean, nullable=False, default=False)  # مجرى
    
    # DOG group activities (الكلب)
    dog_clean = db.Column(db.Boolean, nullable=False, default=False)          # نظافته
    dog_washed = db.Column(db.Boolean, nullable=False, default=False)         # غسله
    dog_brushed = db.Column(db.Boolean, nullable=False, default=False)        # تمشيطه
    bowls_bucket_clean = db.Column(db.Boolean, nullable=False, default=False) # صحن، دلو
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)  # ملاحظات
    
    # Audit trail
    created_by_user_id = db.Column(get_uuid_column(), db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', backref='caretaker_daily_logs')
    dog = db.relationship('Dog', backref='caretaker_daily_logs')
    caretaker_employee = db.relationship('Employee', backref='caretaker_daily_logs')
    created_by_user = db.relationship('User', backref='caretaker_daily_logs')

    # Database constraints and indexes
    __table_args__ = (
        db.Index("ix_caretaker_daily_date", "date"),
        db.Index("ix_caretaker_daily_project_date", "project_id", "date"),
        db.Index("ix_caretaker_daily_dog_date", "dog_id", "date"),
        db.UniqueConstraint("dog_id", "date", name="uq_caretaker_daily_dog_date"),
    )

    def __repr__(self):
        return f'<CaretakerDailyLog {self.id}: {self.dog_id} on {self.date}>'


class BackupFrequency(Enum):
    DISABLED = "DISABLED"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class BackupSettings(db.Model):
    __tablename__ = "backup_settings"
    
    id = db.Column(db.Integer, primary_key=True)
    
    auto_backup_enabled = db.Column(db.Boolean, nullable=False, default=False)
    backup_frequency = db.Column(db.Enum(BackupFrequency), nullable=False, default=BackupFrequency.DISABLED)
    backup_hour = db.Column(db.Integer, nullable=False, default=2)
    retention_days = db.Column(db.Integer, nullable=False, default=30)
    
    google_drive_enabled = db.Column(db.Boolean, nullable=False, default=False)
    google_drive_folder_id = db.Column(db.String(255), nullable=True)
    google_drive_credentials = db.Column(Text, nullable=True)
    
    last_backup_at = db.Column(db.DateTime, nullable=True)
    last_backup_status = db.Column(db.String(50), nullable=True)
    last_backup_message = db.Column(Text, nullable=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_user_id = db.Column(get_uuid_column(), db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    
    updated_by_user = db.relationship('User', backref='backup_settings_updates')
    
    def __repr__(self):
        return f'<BackupSettings {self.id}: {self.backup_frequency.value}>'
    
    @classmethod
    def get_settings(cls):
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings


