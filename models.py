from app import db
from flask_login import UserMixin
from datetime import datetime, date
from enum import Enum
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import Text

class UserRole(Enum):
    GENERAL_ADMIN = "GENERAL_ADMIN"
    PROJECT_MANAGER = "PROJECT_MANAGER"

class EmployeeRole(Enum):
    HANDLER = "سائس"
    TRAINER = "مدرب"
    VET = "طبيب"
    PROJECT_MANAGER = "مسؤول مشروع"
    OPERATIONS = "عمليات"

class DogStatus(Enum):
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"
    DECEASED = "DECEASED"
    TRAINING = "TRAINING"

class DogGender(Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"

class TrainingCategory(Enum):
    OBEDIENCE = "OBEDIENCE"
    DETECTION = "DETECTION"
    AGILITY = "AGILITY"
    ATTACK = "ATTACK"
    FITNESS = "FITNESS"

class VisitType(Enum):
    ROUTINE = "ROUTINE"
    EMERGENCY = "EMERGENCY"
    VACCINATION = "VACCINATION"

class BreedingCycleType(Enum):
    NATURAL = "NATURAL"
    ARTIFICIAL = "ARTIFICIAL"

class BreedingResult(Enum):
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

class PregnancyStatus(Enum):
    NOT_PREGNANT = "غير حامل"
    PREGNANT = "حامل"
    DELIVERED = "ولدت"

class ProjectStatus(Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ProjectRole(Enum):
    PROJECT_MANAGER = "PROJECT_MANAGER"
    HANDLER = "HANDLER"
    TRAINER = "TRAINER"
    VET = "VET"

class PeriodType(Enum):
    MORNING = "MORNING"
    EVENING = "EVENING"
    NIGHT = "NIGHT"

class LeaveType(Enum):
    ANNUAL = "ANNUAL"
    OFFICIAL = "OFFICIAL"
    EMERGENCY = "EMERGENCY"

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
    DELETE = "DELETE"
    EXPORT = "EXPORT"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"

# Association table for many-to-many relationship between employees and dogs
employee_dog_assignment = db.Table('employee_dog_assignment',
    db.Column('employee_id', UUID(as_uuid=True), db.ForeignKey('employee.id'), primary_key=True),
    db.Column('dog_id', UUID(as_uuid=True), db.ForeignKey('dog.id'), primary_key=True)
)

# Association table for many-to-many relationship between projects and dogs
project_dog_assignment = db.Table('project_dog_assignment',
    db.Column('project_id', UUID(as_uuid=True), db.ForeignKey('project.id'), primary_key=True),
    db.Column('dog_id', UUID(as_uuid=True), db.ForeignKey('dog.id'), primary_key=True)
)

# Association table for many-to-many relationship between projects and employees
project_employee_assignment = db.Table('project_employee_assignment',
    db.Column('project_id', UUID(as_uuid=True), db.ForeignKey('project.id'), primary_key=True),
    db.Column('employee_id', UUID(as_uuid=True), db.ForeignKey('employee.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.PROJECT_MANAGER)
    full_name = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean, default=True)
    
    @property
    def is_active(self):
        return self.active
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # For project managers - which sections they can access
    allowed_sections = db.Column(JSON, default=list)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Dog(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to_user = db.relationship('User', backref='assigned_dogs')
    
    # Parent relationships for breeding
    father_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dog.id'))
    mother_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dog.id'))
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
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to_user = db.relationship('User', foreign_keys=[assigned_to_user_id], backref='assigned_employees')
    
    # For project managers - link to their user account
    user_account_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_account = db.relationship('User', foreign_keys=[user_account_id], backref='employee_profile')
    
    # Many-to-many relationships
    assigned_dogs = db.relationship('Dog', secondary=employee_dog_assignment, back_populates='assigned_employees')
    projects = db.relationship('Project', secondary=project_employee_assignment, back_populates='assigned_employees')
    
    def __repr__(self):
        return f'<Employee {self.name} ({self.employee_id})>'

class TrainingSession(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dog_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dog.id'), nullable=False)
    trainer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('employee.id'), nullable=False)
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
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TrainingSession {self.subject} - {self.dog.name}>'

class VeterinaryVisit(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dog_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dog.id'), nullable=False)
    vet_id = db.Column(UUID(as_uuid=True), db.ForeignKey('employee.id'), nullable=False)
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
    
    # Relationships
    dog = db.relationship('Dog', backref='veterinary_visits')
    vet = db.relationship('Employee', backref='veterinary_visits')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<VeterinaryVisit {self.visit_type.value} - {self.dog.name}>'

class BreedingCycle(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    female_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dog.id'), nullable=False)
    male_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dog.id'), nullable=False)
    cycle_type = db.Column(db.Enum(BreedingCycleType), nullable=False)
    
    # Cycle dates
    heat_start_date = db.Column(db.Date)
    mating_date = db.Column(db.Date, nullable=False)
    expected_delivery_date = db.Column(db.Date)
    actual_delivery_date = db.Column(db.Date)
    
    # Results
    result = db.Column(db.Enum(BreedingResult), default=BreedingResult.UNKNOWN)
    number_of_puppies = db.Column(db.Integer, default=0)
    puppies_survived = db.Column(db.Integer, default=0)
    puppies_info = db.Column(JSON, default=list)  # [{name, gender, chip_id, birth_weight}]
    
    # Care information
    prenatal_care = db.Column(Text)
    delivery_notes = db.Column(Text)
    complications = db.Column(Text)
    
    # Relationships
    female = db.relationship('Dog', foreign_keys=[female_id], backref='breeding_as_female')
    male = db.relationship('Dog', foreign_keys=[male_id], backref='breeding_as_male')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<BreedingCycle {self.female.name} x {self.male.name}>'

class Project(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    manager = db.relationship('User', backref='managed_projects')
    
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

class ProjectAssignment(db.Model):
    """Employee assignments to projects with periods and attendance tracking"""
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('project.id'), nullable=False)
    employee_id = db.Column(UUID(as_uuid=True), db.ForeignKey('employee.id'), nullable=False)
    role = db.Column(db.Enum(ProjectRole), nullable=False)
    period = db.Column(db.Enum(PeriodType), nullable=False)  # صباحي/مسائي/ثالثة
    is_present = db.Column(db.Boolean, default=True)  # حضور/غياب
    leave_type = db.Column(db.Enum(LeaveType))  # نوع الإجازة
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='employee_assignments')
    employee = db.relationship('Employee', backref='project_assignments')
    
    # Unique constraint to prevent duplicate assignments
    __table_args__ = (db.UniqueConstraint('project_id', 'employee_id', name='unique_project_employee'),)
    
    def __repr__(self):
        return f'<ProjectAssignment {self.employee.name} -> {self.project.name}>'

class ProjectDog(db.Model):
    """Dog assignments to projects"""
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('project.id'), nullable=False)
    dog_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dog.id'), nullable=False)
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

class Incident(db.Model):
    """Incident logging for projects"""
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)  # اسم الحادث
    incident_date = db.Column(db.Date, nullable=False)
    incident_time = db.Column(db.Time, nullable=False)
    incident_type = db.Column(db.String(100), nullable=False)  # نوع الحادث
    description = db.Column(Text)
    location = db.Column(db.String(200))
    severity = db.Column(db.String(20), default='MEDIUM')  # LOW, MEDIUM, HIGH
    
    # People involved
    reported_by = db.Column(UUID(as_uuid=True), db.ForeignKey('employee.id'))
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
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('project.id'), nullable=False)
    element_type = db.Column(db.Enum(ElementType), nullable=False)  # سلاح/مخدرات/متفجرات/أخرى
    subtype = db.Column(db.String(100))  # نوع السلاح/العبوة
    discovery_date = db.Column(db.Date, nullable=False)
    discovery_time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    
    # Detection details
    detected_by_dog = db.Column(UUID(as_uuid=True), db.ForeignKey('dog.id'))
    handler = db.Column(UUID(as_uuid=True), db.ForeignKey('employee.id'))
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
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('project.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_type = db.Column(db.Enum(TargetType), nullable=False)  # EMPLOYEE or DOG
    
    # Target identification (generic approach)
    target_employee_id = db.Column(UUID(as_uuid=True), db.ForeignKey('employee.id'))
    target_dog_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dog.id'))
    
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
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = db.Column(UUID(as_uuid=True), db.ForeignKey('employee.id'), nullable=False)
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
    substitute_employee_id = db.Column(UUID(as_uuid=True), db.ForeignKey('employee.id'))
    
    notes = db.Column(Text)
    
    # Relationships
    employee = db.relationship('Employee', foreign_keys=[employee_id], backref='attendance_records')
    substitute = db.relationship('Employee', foreign_keys=[substitute_employee_id])
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate attendance records
    __table_args__ = (db.UniqueConstraint('employee_id', 'date', 'shift', name='unique_attendance'),)
    
    def __repr__(self):
        return f'<AttendanceRecord {self.employee.name} - {self.date}>'

class AuditLog(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action_type = db.Column(db.Enum(AuditAction), nullable=False)
    model_target = db.Column(db.String(50), nullable=False)
    object_id = db.Column(db.String(50))
    changes = db.Column(JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action_type.value} - {self.model_target}>'

# Production System Models (8 sections as requested)

class DogMaturity(db.Model):
    """Section 1: General Information + Section 2: Maturity (البلوغ)"""
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dog_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dog.id'), nullable=False)
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
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dog_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dog.id'), nullable=False)
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
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    female_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dog.id'), nullable=False)
    male_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dog.id'), nullable=False)
    heat_cycle_id = db.Column(UUID(as_uuid=True), db.ForeignKey('heat_cycle.id'), nullable=False)
    
    mating_date = db.Column(db.Date, nullable=False)
    mating_time = db.Column(db.Time)
    location = db.Column(db.String(100))
    supervised_by = db.Column(UUID(as_uuid=True), db.ForeignKey('employee.id'))
    
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
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mating_record_id = db.Column(UUID(as_uuid=True), db.ForeignKey('mating_record.id'), nullable=False)
    dog_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dog.id'), nullable=False)
    
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
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pregnancy_record_id = db.Column(UUID(as_uuid=True), db.ForeignKey('pregnancy_record.id'), nullable=False)
    
    # Delivery details
    delivery_date = db.Column(db.Date, nullable=False)
    delivery_start_time = db.Column(db.Time)
    delivery_end_time = db.Column(db.Time)
    location = db.Column(db.String(100))
    
    # Assistance
    vet_present = db.Column(UUID(as_uuid=True), db.ForeignKey('employee.id'))
    handler_present = db.Column(UUID(as_uuid=True), db.ForeignKey('employee.id'))
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
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_record_id = db.Column(UUID(as_uuid=True), db.ForeignKey('delivery_record.id'), nullable=False)
    
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
    current_status = db.Column(db.String(50), default='جيد')  # جيد، ضعيف، متوفي
    
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
    adult_dog_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dog.id'))
    
    notes = db.Column(Text)
    
    # Relationships
    delivery_record = db.relationship('DeliveryRecord', backref='puppies')
    adult_dog = db.relationship('Dog', backref='puppy_record')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PuppyTraining(db.Model):
    """Section 8: Puppy Training (تدريب الجراء)"""
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    puppy_id = db.Column(UUID(as_uuid=True), db.ForeignKey('puppy_record.id'), nullable=False)
    trainer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('employee.id'), nullable=False)
    
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

class ProjectAttendance(db.Model):
    """Daily attendance tracking for project personnel (كشف التحضير اليومي)"""
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('project.id'), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False, default=date.today)
    period = db.Column(db.Enum(PeriodType), nullable=False)  # صباحي/مسائي/ليلي
    
    # Project manager for this shift
    shift_manager_id = db.Column(UUID(as_uuid=True), db.ForeignKey('employee.id'))
    manager_signature = db.Column(db.String(200))  # Could store signature image path
    
    # Overall attendance notes
    notes = db.Column(Text)
    weather_conditions = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='attendance_records')
    shift_manager = db.relationship('Employee', backref='managed_shifts')
    
    # Unique constraint to prevent duplicate records for same project/date/period
    __table_args__ = (db.UniqueConstraint('project_id', 'attendance_date', 'period', name='unique_project_attendance'),)
    
    def __repr__(self):
        return f'<ProjectAttendance {self.project.name} - {self.attendance_date}>'

class AttendanceEntry(db.Model):
    """Individual attendance entries for employees and dogs (إدخالات الحضور)"""
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attendance_record_id = db.Column(UUID(as_uuid=True), db.ForeignKey('project_attendance.id'), nullable=False)
    group_number = db.Column(db.Integer, default=1)  # المجموعة الأولى/الثانية
    
    # Employee information
    employee_id = db.Column(UUID(as_uuid=True), db.ForeignKey('employee.id'), nullable=False)
    substitute_employee_id = db.Column(UUID(as_uuid=True), db.ForeignKey('employee.id'))  # الموظف البديل
    
    # Dog information
    dog_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dog.id'))
    
    # Attendance times
    arrival_time = db.Column(db.Time)  # وقت الحضور
    departure_time = db.Column(db.Time)  # وقت الانصراف
    
    # Signatures (could store image paths or just text confirmation)
    arrival_signature = db.Column(db.String(200))  # توقيع الحضور
    departure_signature = db.Column(db.String(200))  # توقيع الانصراف
    
    # Status flags
    present = db.Column(db.Boolean, default=True)
    late_arrival = db.Column(db.Boolean, default=False)
    early_departure = db.Column(db.Boolean, default=False)
    
    # Notes for this entry
    notes = db.Column(Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendance_record = db.relationship('ProjectAttendance', backref='entries')
    employee = db.relationship('Employee', foreign_keys=[employee_id], backref='attendance_entries')
    substitute = db.relationship('Employee', foreign_keys=[substitute_employee_id], backref='substitute_entries')
    dog = db.relationship('Dog', backref='attendance_entries')
    
    def __repr__(self):
        return f'<AttendanceEntry {self.employee.name} - {self.attendance_record.attendance_date}>'

class LeaveRequest(db.Model):
    """Leave requests tracking (الإجازات)"""
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('project.id'), nullable=False)
    attendance_record_id = db.Column(UUID(as_uuid=True), db.ForeignKey('project_attendance.id'))
    
    employee_id = db.Column(UUID(as_uuid=True), db.ForeignKey('employee.id'), nullable=False)
    leave_type = db.Column(db.Enum(LeaveType), nullable=False)  # سنوية/مرضية/طارئة/أخرى
    leave_date = db.Column(db.Date, nullable=False)
    
    # Additional leave types not in enum
    other_leave_type = db.Column(db.String(100))  # for "أخرى" type
    
    # Leave details
    reason = db.Column(Text)
    approved = db.Column(db.Boolean, default=False)
    approved_by = db.Column(UUID(as_uuid=True), db.ForeignKey('employee.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='leave_requests')
    attendance_record = db.relationship('ProjectAttendance', backref='leave_requests')
    employee = db.relationship('Employee', foreign_keys=[employee_id], backref='leave_requests')
    approver = db.relationship('Employee', foreign_keys=[approved_by], backref='approved_leaves')
    
    def __repr__(self):
        return f'<LeaveRequest {self.employee.name} - {self.leave_type.value}>'
