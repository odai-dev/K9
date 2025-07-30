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

class ProjectStatus(Enum):
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class AuditAction(Enum):
    CREATE = "CREATE"
    EDIT = "EDIT"
    DELETE = "DELETE"
    EXPORT = "EXPORT"
    LOGIN = "LOGIN"

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
    id_number = db.Column(db.String(20), unique=True, nullable=False)
    role = db.Column(db.Enum(EmployeeRole), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    hire_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Additional info
    department = db.Column(db.String(100))
    rank = db.Column(db.String(50))
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
    description = db.Column(Text)
    status = db.Column(db.Enum(ProjectStatus), default=ProjectStatus.PLANNING)
    
    # Dates
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
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
    
    def __repr__(self):
        return f'<Project {self.name} ({self.code})>'

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
