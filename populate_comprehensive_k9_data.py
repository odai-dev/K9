#!/usr/bin/env python3
"""
Comprehensive K9 Operations Data Population Script

This script populates ALL sections of the K9 Operations Management System with realistic data:
- Dogs (all breeds, ages, specializations, statuses)
- Employees (all roles: handlers, vets, trainers, breeders, project managers)
- Projects (various statuses and resource assignments)
- Training Sessions (all categories and skill levels)
- Veterinary Records (routine, emergency, vaccination)
- Breeding System (maturity, heat cycles, mating, pregnancies, deliveries)
- Puppies and Puppy Training
- Performance Evaluations, Incidents, and Suspicions
"""

from app import app, db
from models import *
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta, time
import random
import uuid

def clear_existing_data():
    """Clear existing sample data but keep admin user"""
    print("🧹 Clearing existing sample data...")
    
    # Clear in proper order to avoid foreign key constraints
    models_to_clear = [
        PuppyTraining, PuppyRecord, DeliveryRecord, PregnancyRecord, 
        MatingRecord, HeatCycle, DogMaturity, VeterinaryVisit, 
        TrainingSession, PerformanceEvaluation, Incident, Suspicion,
        ProjectAttendance, ProjectShiftAssignment, ProjectShift,
        ProjectAssignment, ProductionCycle
    ]
    
    for model in models_to_clear:
        model.query.delete()
    
    # Clear core entities (keep admin)
    Dog.query.delete()
    Project.query.delete() 
    Employee.query.delete()
    User.query.filter(User.username != 'admin').delete()
    
    db.session.commit()
    print("✅ Existing data cleared")

def create_employees():
    """Create diverse employees across all roles"""
    print("👥 Creating employees across all roles...")
    
    employees_data = [
        # Handlers
        {
            'name': 'أحمد محمد السائس', 'employee_id': 'EMP-001', 'role': EmployeeRole.HANDLER,
            'phone': '0501234567', 'email': 'ahmed.handler@k9ops.com',
            'hire_date': date(2020, 1, 15), 'certifications': ['شهادة سائس كلاب', 'دورة الإسعافات الأولية']
        },
        {
            'name': 'محمد عبدالرحمن السائس', 'employee_id': 'EMP-002', 'role': EmployeeRole.HANDLER,
            'phone': '0502345678', 'email': 'mohamed.handler@k9ops.com',
            'hire_date': date(2021, 3, 20), 'certifications': ['شهادة سائس كلاب', 'دورة السلامة']
        },
        {
            'name': 'علي سعد الحارثي', 'employee_id': 'EMP-003', 'role': EmployeeRole.HANDLER,
            'phone': '0503456789', 'email': 'ali.harithi@k9ops.com',
            'hire_date': date(2021, 8, 10), 'certifications': ['شهادة سائس كلاب']
        },
        {
            'name': 'عبدالله فهد القحطاني', 'employee_id': 'EMP-004', 'role': EmployeeRole.HANDLER,
            'phone': '0504567890', 'email': 'abdullah.qahtani@k9ops.com',
            'hire_date': date(2022, 2, 5), 'certifications': ['شهادة سائس كلاب', 'دورة الإسعافات الأولية']
        },
        
        # Trainers
        {
            'name': 'خالد عبدالله المدرب', 'employee_id': 'EMP-005', 'role': EmployeeRole.TRAINER,
            'phone': '0505678901', 'email': 'khaled.trainer@k9ops.com',
            'hire_date': date(2019, 6, 1), 'certifications': ['شهادة في تدريب الكلاب البوليسية', 'دورة السلوك الحيواني']
        },
        {
            'name': 'سالم أحمد المدرب المتقدم', 'employee_id': 'EMP-006', 'role': EmployeeRole.TRAINER,
            'phone': '0506789012', 'email': 'salem.trainer@k9ops.com',
            'hire_date': date(2018, 9, 15), 'certifications': ['شهادة تدريب متقدم', 'دورة تدريب الهجوم والحراسة']
        },
        {
            'name': 'نواف محمد المدرب المختص', 'employee_id': 'EMP-007', 'role': EmployeeRole.TRAINER,
            'phone': '0507890123', 'email': 'nawaf.trainer@k9ops.com',
            'hire_date': date(2020, 4, 12), 'certifications': ['شهادة تدريب الكشف', 'دورة التدريب الرياضي']
        },
        
        # Veterinarians
        {
            'name': 'د. سارة علي الطبيبة', 'employee_id': 'EMP-008', 'role': EmployeeRole.VET,
            'phone': '0508901234', 'email': 'sara.vet@k9ops.com',
            'hire_date': date(2019, 1, 1), 'certifications': ['دكتوراه في الطب البيطري', 'شهادة في طب الحيوانات المتخصصة']
        },
        {
            'name': 'د. عبدالرحمن الطبيب المتخصص', 'employee_id': 'EMP-009', 'role': EmployeeRole.VET,
            'phone': '0509012345', 'email': 'abdulrahman.vet@k9ops.com',
            'hire_date': date(2020, 7, 20), 'certifications': ['دكتوراه في الطب البيطري', 'شهادة جراحة']
        },
        
        # Breeders
        {
            'name': 'فهد سالم المربي', 'employee_id': 'EMP-010', 'role': EmployeeRole.BREEDER,
            'phone': '0510123456', 'email': 'fahd.breeder@k9ops.com',
            'hire_date': date(2020, 11, 5), 'certifications': ['شهادة تربية الكلاب', 'دورة الوراثة والتربية']
        },
        {
            'name': 'عمر عبدالله المربي المتقدم', 'employee_id': 'EMP-011', 'role': EmployeeRole.BREEDER,
            'phone': '0511234567', 'email': 'omar.breeder@k9ops.com',
            'hire_date': date(2019, 5, 18), 'certifications': ['شهادة متقدمة في التربية', 'دورة إدارة المراعي']
        },
        
        # Project Managers
        {
            'name': 'فهد سعد مسؤول المشروع', 'employee_id': 'EMP-012', 'role': EmployeeRole.PROJECT_MANAGER,
            'phone': '0512345678', 'email': 'fahd.pm@k9ops.com',
            'hire_date': date(2018, 4, 10), 'certifications': ['شهادة إدارة المشاريع', 'دورة القيادة']
        },
        {
            'name': 'ناصر علي مدير المشاريع', 'employee_id': 'EMP-013', 'role': EmployeeRole.PROJECT_MANAGER,
            'phone': '0513456789', 'email': 'nasser.pm@k9ops.com',
            'hire_date': date(2019, 8, 22), 'certifications': ['شهادة إدارة المشاريع المتقدمة', 'دورة الأمن والسلامة']
        }
    ]
    
    created_employees = []
    for emp_data in employees_data:
        employee = Employee()
        for key, value in emp_data.items():
            setattr(employee, key, value)
        employee.is_active = True
        db.session.add(employee)
        created_employees.append(employee)
    
    db.session.commit()
    print(f"✅ Created {len(created_employees)} employees across all roles")
    return created_employees

def create_dogs():
    """Create diverse dogs with various breeds, ages, and specializations"""
    print("🐕 Creating diverse dog population...")
    
    dogs_data = [
        # German Shepherds - Detection specialists
        {
            'name': 'ريكس', 'code': 'K9-001', 'breed': 'الراعي الألماني',
            'gender': DogGender.MALE, 'birth_date': date(2020, 3, 15),
            'microchip_id': 'MC001REX', 'current_status': DogStatus.ACTIVE,
            'location': 'المعسكر الأول', 'specialization': 'كشف المتفجرات',
            'color': 'أسود وبني', 'weight': 35.5, 'height': 65.0
        },
        {
            'name': 'أسطورة', 'code': 'K9-002', 'breed': 'الراعي الألماني',
            'gender': DogGender.FEMALE, 'birth_date': date(2019, 8, 20),
            'microchip_id': 'MC002AST', 'current_status': DogStatus.ACTIVE,
            'location': 'المعسكر الأول', 'specialization': 'كشف المخدرات',
            'color': 'أسود وبني فاتح', 'weight': 32.0, 'height': 62.0
        },
        
        # Belgian Malinois - Attack and patrol
        {
            'name': 'لونا', 'code': 'K9-003', 'breed': 'الراعي البلجيكي',
            'gender': DogGender.FEMALE, 'birth_date': date(2021, 1, 20),
            'microchip_id': 'MC003LUN', 'current_status': DogStatus.ACTIVE,
            'location': 'المعسكر الثاني', 'specialization': 'الهجوم والحراسة',
            'color': 'بني فاتح', 'weight': 28.0, 'height': 58.0
        },
        {
            'name': 'فايكنغ', 'code': 'K9-004', 'breed': 'الراعي البلجيكي',
            'gender': DogGender.MALE, 'birth_date': date(2020, 11, 5),
            'microchip_id': 'MC004VIK', 'current_status': DogStatus.ACTIVE,
            'location': 'المعسكر الثاني', 'specialization': 'الهجوم والحراسة',
            'color': 'بني غامق', 'weight': 33.0, 'height': 63.0
        },
        
        # Rottweilers - Guard and attack
        {
            'name': 'ماكس', 'code': 'K9-005', 'breed': 'الروت وايلر',
            'gender': DogGender.MALE, 'birth_date': date(2019, 8, 10),
            'microchip_id': 'MC005MAX', 'current_status': DogStatus.ACTIVE,
            'location': 'المعسكر الأول', 'specialization': 'الهجوم والحراسة',
            'color': 'أسود وبني', 'weight': 45.0, 'height': 70.0
        },
        {
            'name': 'ملكة', 'code': 'K9-006', 'breed': 'الروت وايلر',
            'gender': DogGender.FEMALE, 'birth_date': date(2020, 6, 25),
            'microchip_id': 'MC006QUE', 'current_status': DogStatus.ACTIVE,
            'location': 'المعسكر الثاني', 'specialization': 'الحراسة',
            'color': 'أسود وبني', 'weight': 38.0, 'height': 65.0
        },
        
        # Labradors - Search and rescue
        {
            'name': 'بيلا', 'code': 'K9-007', 'breed': 'اللابرادور',
            'gender': DogGender.FEMALE, 'birth_date': date(2022, 2, 5),
            'microchip_id': 'MC007BEL', 'current_status': DogStatus.TRAINING,
            'location': 'مركز التدريب', 'specialization': 'البحث والإنقاذ',
            'color': 'ذهبي', 'weight': 25.0, 'height': 55.0
        },
        {
            'name': 'كوبر', 'code': 'K9-008', 'breed': 'اللابرادور',
            'gender': DogGender.MALE, 'birth_date': date(2021, 9, 12),
            'microchip_id': 'MC008COP', 'current_status': DogStatus.ACTIVE,
            'location': 'المعسكر الثالث', 'specialization': 'البحث والإنقاذ',
            'color': 'أسود', 'weight': 30.0, 'height': 58.0
        },
        
        # Dutch Shepherds - Multi-purpose
        {
            'name': 'زيوس', 'code': 'K9-009', 'breed': 'الراعي الهولندي',
            'gender': DogGender.MALE, 'birth_date': date(2020, 4, 18),
            'microchip_id': 'MC009ZEU', 'current_status': DogStatus.ACTIVE,
            'location': 'المعسكر الأول', 'specialization': 'متعدد المهام',
            'color': 'بني مقلم', 'weight': 34.0, 'height': 64.0
        },
        
        # Retired veterans
        {
            'name': 'شادو', 'code': 'K9-010', 'breed': 'الراعي الألماني',
            'gender': DogGender.MALE, 'birth_date': date(2016, 11, 30),
            'microchip_id': 'MC010SHA', 'current_status': DogStatus.RETIRED,
            'location': 'منطقة التقاعد', 'specialization': 'خبير متعدد المهام',
            'color': 'أسود', 'weight': 40.0, 'height': 68.0
        },
        
        # Young trainees
        {
            'name': 'روكي', 'code': 'K9-011', 'breed': 'الراعي البلجيكي',
            'gender': DogGender.MALE, 'birth_date': date(2023, 1, 8),
            'microchip_id': 'MC011ROC', 'current_status': DogStatus.TRAINING,
            'location': 'مركز التدريب', 'specialization': 'في التدريب',
            'color': 'بني فاتح', 'weight': 20.0, 'height': 50.0
        },
        {
            'name': 'نوفا', 'code': 'K9-012', 'breed': 'اللابرادور',
            'gender': DogGender.FEMALE, 'birth_date': date(2023, 3, 22),
            'microchip_id': 'MC012NOV', 'current_status': DogStatus.TRAINING,
            'location': 'مركز التدريب', 'specialization': 'في التدريب',
            'color': 'شوكولاتي', 'weight': 18.0, 'height': 48.0
        },
        
        # Breeding females
        {
            'name': 'أميرة', 'code': 'K9-013', 'breed': 'الراعي الألماني',
            'gender': DogGender.FEMALE, 'birth_date': date(2019, 5, 14),
            'microchip_id': 'MC013AMI', 'current_status': DogStatus.ACTIVE,
            'location': 'مركز التربية', 'specialization': 'أم للتربية',
            'color': 'بني وأسود', 'weight': 30.0, 'height': 60.0
        },
        {
            'name': 'ليلى', 'code': 'K9-014', 'breed': 'الراعي البلجيكي',
            'gender': DogGender.FEMALE, 'birth_date': date(2020, 7, 9),
            'microchip_id': 'MC014LAY', 'current_status': DogStatus.ACTIVE,
            'location': 'مركز التربية', 'specialization': 'أم للتربية',
            'color': 'بني محمر', 'weight': 27.0, 'height': 57.0
        },
        
        # Breeding males
        {
            'name': 'أسد', 'code': 'K9-015', 'breed': 'الراعي الألماني',
            'gender': DogGender.MALE, 'birth_date': date(2018, 12, 3),
            'microchip_id': 'MC015LIO', 'current_status': DogStatus.ACTIVE,
            'location': 'مركز التربية', 'specialization': 'فحل للتربية',
            'color': 'أسود وبني', 'weight': 38.0, 'height': 67.0
        }
    ]
    
    created_dogs = []
    for dog_data in dogs_data:
        dog = Dog()
        for key, value in dog_data.items():
            setattr(dog, key, value)
        db.session.add(dog)
        created_dogs.append(dog)
    
    db.session.commit()
    print(f"✅ Created {len(created_dogs)} dogs with diverse breeds and specializations")
    return created_dogs

def create_projects(employees):
    """Create various projects with different statuses"""
    print("📋 Creating projects with various statuses...")
    
    # Find project managers
    project_managers = [emp for emp in employees if emp.role == EmployeeRole.PROJECT_MANAGER]
    
    projects_data = [
        {
            'name': 'أمن المطار الدولي', 'code': 'PROJ-001',
            'main_task': 'تأمين المطار الدولي بالكلاب البوليسية',
            'description': 'مشروع تأمين شامل للمطار الدولي باستخدام فرق K9 متخصصة في كشف المتفجرات والمخدرات',
            'status': ProjectStatus.ACTIVE,
            'start_date': date(2024, 1, 15),
            'expected_completion_date': date(2024, 12, 31),
            'location': 'مطار الملك عبدالعزيز الدولي',
            'mission_type': 'أمن المطارات',
            'priority': 'HIGH',
            'project_manager': project_managers[0] if project_managers else None
        },
        {
            'name': 'تأمين الحدود الشمالية', 'code': 'PROJ-002',
            'main_task': 'مراقبة وتأمين الحدود الشمالية',
            'description': 'مشروع تأمين الحدود الشمالية باستخدام فرق K9 للكشف والمراقبة',
            'status': ProjectStatus.ACTIVE,
            'start_date': date(2024, 3, 1),
            'expected_completion_date': date(2024, 11, 30),
            'location': 'المنطقة الحدودية الشمالية',
            'mission_type': 'أمن الحدود',
            'priority': 'HIGH'
        },
        {
            'name': 'تدريب الوحدة الجديدة', 'code': 'PROJ-003',
            'main_task': 'تدريب دفعة جديدة من الكلاب والسائسين',
            'description': 'برنامج تدريبي شامل للكلاب الجديدة والسائسين المستجدين',
            'status': ProjectStatus.PLANNED,
            'start_date': date(2024, 6, 1),
            'expected_completion_date': date(2024, 9, 30),
            'location': 'مركز التدريب المتقدم',
            'mission_type': 'تدريب وتطوير',
            'priority': 'MEDIUM'
        },
        {
            'name': 'أمن المنشآت الحساسة', 'code': 'PROJ-004',
            'main_task': 'تأمين المنشآت الحيوية والحساسة',
            'description': 'تأمين المنشآت الحكومية والحساسة باستخدام فرق K9 متخصصة',
            'status': ProjectStatus.COMPLETED,
            'start_date': date(2023, 8, 1),
            'end_date': date(2024, 2, 28),
            'location': 'مختلف المدن',
            'mission_type': 'أمن المنشآت',
            'priority': 'HIGH',
            'success_rating': 9,
            'final_report': 'تم تنفيذ المشروع بنجاح مع تحقيق 98% من الأهداف المحددة'
        },
        {
            'name': 'برنامج التربية المتقدم', 'code': 'PROJ-005',
            'main_task': 'تطوير برنامج التربية وإنتاج سلالات متميزة',
            'description': 'مشروع لتطوير برنامج تربية متقدم لإنتاج كلاب عالية الجودة',
            'status': ProjectStatus.ACTIVE,
            'start_date': date(2024, 2, 1),
            'expected_completion_date': date(2025, 2, 28),
            'location': 'مركز التربية المتخصص',
            'mission_type': 'تربية وإنتاج',
            'priority': 'MEDIUM'
        }
    ]
    
    created_projects = []
    for proj_data in projects_data:
        project = Project()
        for key, value in proj_data.items():
            if key != 'project_manager':
                setattr(project, key, value)
        
        if 'project_manager' in proj_data and proj_data['project_manager']:
            project.project_manager_id = proj_data['project_manager'].id
        
        db.session.add(project)
        created_projects.append(project)
    
    db.session.commit()
    print(f"✅ Created {len(created_projects)} projects with various statuses")
    return created_projects

def create_training_sessions(dogs, employees):
    """Create comprehensive training sessions across all categories"""
    print("🎯 Creating training sessions across all categories...")
    
    trainers = [emp for emp in employees if emp.role == EmployeeRole.TRAINER]
    if not trainers:
        print("⚠️ No trainers found, skipping training sessions")
        return []
    
    training_sessions = []
    
    # Training categories and their sessions
    training_categories = {
        TrainingCategory.OBEDIENCE: [
            'تدريب الجلوس والوقوف', 'تدريب المشي بجانب السائس', 'تدريب عدم القفز',
            'تدريب الاستجابة للأوامر الصوتية', 'تدريب الهدوء في الأماكن المزدحمة'
        ],
        TrainingCategory.DETECTION: [
            'كشف المتفجرات في الأماكن المفتوحة', 'كشف المخدرات في المركبات',
            'كشف الأسلحة في الأمتعة', 'تدريب الكشف في الطائرات', 'كشف المواد المحظورة'
        ],
        TrainingCategory.AGILITY: [
            'عبور الحواجز', 'المرور في الأنفاق', 'التسلق والقفز',
            'التوازن على الأسطح المرتفعة', 'السرعة والمرونة'
        ],
        TrainingCategory.ATTACK: [
            'الهجوم المحكم', 'الدفاع عن السائس', 'مطاردة المشتبه بهم',
            'تدريب العض والإمساك', 'تدريب التحكم في الهجوم'
        ],
        TrainingCategory.FITNESS: [
            'تدريب اللياقة البدنية', 'تمارين القوة والتحمل', 'تدريب الجري لمسافات طويلة',
            'تمارين التنسيق والتوازن', 'برنامج إعادة التأهيل'
        ]
    }
    
    # Create sessions for active and training dogs
    active_dogs = [dog for dog in dogs if dog.current_status in [DogStatus.ACTIVE, DogStatus.TRAINING]]
    
    for dog in active_dogs[:8]:  # Focus on first 8 dogs
        trainer = random.choice(trainers)
        
        # Each dog gets 3-5 recent training sessions
        num_sessions = random.randint(3, 5)
        
        for i in range(num_sessions):
            category = random.choice(list(training_categories.keys()))
            session_name = random.choice(training_categories[category])
            
            # Create session within last 60 days
            session_date = datetime.now() - timedelta(days=random.randint(1, 60))
            
            session = TrainingSession()
            session.dog_id = dog.id
            session.trainer_id = trainer.id
            session.subject = session_name
            session.category = category
            session.session_date = session_date
            session.duration = random.randint(30, 120)  # 30-120 minutes
            session.success_rating = random.randint(6, 10)  # Good to excellent ratings
            session.location = random.choice(['مركز التدريب الأول', 'مركز التدريب الثاني', 'الميدان الخارجي'])
            session.weather_conditions = random.choice(['مشمس', 'غائم', 'معتدل', 'حار'])
            session.equipment_used = random.choice([
                ['معدات كشف', 'أهداف تدريبية'],
                ['حواجز', 'أنفاق'],
                ['دمى تدريب', 'واقيات'],
                ['كرات', 'حبال'],
                ['أجهزة قياس الأداء']
            ])
            session.notes = f"جلسة تدريبية ممتازة. أظهر {dog.name} تحسناً ملحوظاً في المهارات المطلوبة."
            
            training_sessions.append(session)
            db.session.add(session)
    
    db.session.commit()
    print(f"✅ Created {len(training_sessions)} training sessions across all categories")
    return training_sessions

def create_veterinary_visits(dogs, employees):
    """Create veterinary records with routine, emergency, and vaccination visits"""
    print("🏥 Creating veterinary visits across all types...")
    
    vets = [emp for emp in employees if emp.role == EmployeeRole.VET]
    if not vets:
        print("⚠️ No veterinarians found, skipping veterinary visits")
        return []
    
    veterinary_visits = []
    
    # Each dog gets 2-4 veterinary visits
    for dog in dogs[:10]:  # Focus on first 10 dogs
        vet = random.choice(vets)
        num_visits = random.randint(2, 4)
        
        for i in range(num_visits):
            visit_type = random.choice(list(VisitType))
            visit_date = datetime.now() - timedelta(days=random.randint(7, 180))
            
            visit = VeterinaryVisit()
            visit.dog_id = dog.id
            visit.vet_id = vet.id
            visit.visit_type = visit_type
            visit.visit_date = visit_date
            
            # Physical examination data
            visit.weight = round(dog.weight + random.uniform(-2, 2), 1)
            visit.temperature = round(random.uniform(38.0, 39.5), 1)
            visit.heart_rate = random.randint(60, 120)
            visit.blood_pressure = f"{random.randint(110, 140)}/{random.randint(70, 90)}"
            
            # Visit-specific details
            if visit_type == VisitType.ROUTINE:
                visit.symptoms = "فحص دوري شامل"
                visit.diagnosis = "حالة صحية جيدة"
                visit.treatment = "لا يوجد علاج مطلوب"
                visit.cost = random.randint(150, 300)
                
            elif visit_type == VisitType.EMERGENCY:
                emergencies = [
                    ("جرح في الكفة الأمامية", "جرح سطحي", "تنظيف الجرح وضمادة"),
                    ("إسهال شديد", "اضطراب في الجهاز الهضمي", "مضادات حيوية ونظام غذائي خاص"),
                    ("عرج في الساق الخلفية", "التواء في المفصل", "راحة ومضادات الالتهاب"),
                    ("قيء متكرر", "تسمم غذائي محتمل", "غسيل معدة ومراقبة")
                ]
                emergency = random.choice(emergencies)
                visit.symptoms = emergency[0]
                visit.diagnosis = emergency[1] 
                visit.treatment = emergency[2]
                visit.cost = random.randint(400, 800)
                
            elif visit_type == VisitType.VACCINATION:
                vaccines = [
                    "لقاح السعار",
                    "لقاح الكلب الخماسي",
                    "لقاح البارفو",
                    "لقاح الكورونا الكلبي"
                ]
                vaccine = random.choice(vaccines)
                visit.symptoms = "تطعيم وقائي"
                visit.diagnosis = "حالة صحية جيدة للتطعيم"
                visit.treatment = f"تم إعطاء {vaccine}"
                visit.vaccinations_given = [{"name": vaccine, "date": visit_date.date().isoformat()}]
                visit.next_visit_date = (visit_date + timedelta(days=365)).date()
                visit.cost = random.randint(100, 200)
            
            # Stool and urine analysis
            visit.stool_color = random.choice(['طبيعي', 'بني فاتح', 'بني غامق'])
            visit.stool_consistency = random.choice(['صلب', 'متوسط', 'طري'])
            visit.urine_color = random.choice(['أصفر فاتح', 'أصفر متوسط'])
            
            visit.location = random.choice(['العيادة البيطرية الرئيسية', 'العيادة الميدانية', 'المستشفى البيطري'])
            visit.weather = random.choice(['مشمس', 'غائم', 'ماطر', 'معتدل'])
            visit.notes = f"زيارة {visit_type.value} لـ {dog.name}. الحالة العامة مستقرة."
            
            veterinary_visits.append(visit)
            db.session.add(visit)
    
    db.session.commit()
    print(f"✅ Created {len(veterinary_visits)} veterinary visits across all types")
    return veterinary_visits

def create_breeding_system(dogs, employees):
    """Create comprehensive breeding system data"""
    print("🐕‍🦺 Creating breeding system data...")
    
    breeders = [emp for emp in employees if emp.role == EmployeeRole.BREEDER]
    vets = [emp for emp in employees if emp.role == EmployeeRole.VET]
    
    if not breeders or not vets:
        print("⚠️ Missing breeders or vets, skipping breeding system")
        return {}
    
    # Get breeding dogs
    breeding_females = [dog for dog in dogs if dog.gender == DogGender.FEMALE and 'تربية' in dog.specialization]
    breeding_males = [dog for dog in dogs if dog.gender == DogGender.MALE and 'تربية' in dog.specialization]
    
    if not breeding_females or not breeding_males:
        # Use some regular dogs for breeding
        breeding_females = [dog for dog in dogs if dog.gender == DogGender.FEMALE][:3]
        breeding_males = [dog for dog in dogs if dog.gender == DogGender.MALE][:2]
    
    created_records = {
        'maturity': [],
        'heat_cycles': [],
        'matings': [],
        'pregnancies': [],
        'deliveries': [],
        'puppies': [],
        'puppy_training': []
    }
    
    # 1. Create maturity records for breeding dogs
    print("📊 Creating maturity records...")
    for dog in breeding_females + breeding_males:
        maturity = DogMaturity()
        maturity.dog_id = dog.id
        maturity.maturity_date = dog.birth_date + timedelta(days=random.randint(365, 547))  # 1-1.5 years
        maturity.maturity_status = MaturityStatus.MATURE
        maturity.weight_at_maturity = dog.weight
        maturity.height_at_maturity = dog.height
        maturity.notes = f"وصل {dog.name} إلى البلوغ في عمر مناسب وبصحة جيدة"
        
        created_records['maturity'].append(maturity)
        db.session.add(maturity)
    
    # 2. Create heat cycles for females
    print("🌡️ Creating heat cycles...")
    for female in breeding_females:
        # Each female gets 2-3 heat cycles
        for cycle_num in range(1, random.randint(2, 4)):
            heat_cycle = HeatCycle()
            heat_cycle.dog_id = female.id
            heat_cycle.cycle_number = cycle_num
            heat_cycle.start_date = date.today() - timedelta(days=random.randint(30, 365))
            heat_cycle.end_date = heat_cycle.start_date + timedelta(days=random.randint(14, 21))
            heat_cycle.duration_days = (heat_cycle.end_date - heat_cycle.start_date).days
            heat_cycle.status = HeatStatus.COMPLETED
            heat_cycle.behavioral_changes = "زيادة النشاط وطلب الانتباه"
            heat_cycle.physical_signs = "تغيرات هرمونية طبيعية"
            heat_cycle.appetite_changes = "زيادة في الشهية"
            heat_cycle.notes = f"دورة طبيعية رقم {cycle_num} لـ {female.name}"
            
            created_records['heat_cycles'].append(heat_cycle)
            db.session.add(heat_cycle)
    
    db.session.commit()  # Commit to get IDs for foreign keys
    
    # 3. Create mating records
    print("💕 Creating mating records...")
    for i, female in enumerate(breeding_females[:2]):  # Limit to 2 females for demo
        male = breeding_males[i % len(breeding_males)]
        female_heat_cycles = [hc for hc in created_records['heat_cycles'] if hc.dog_id == female.id]
        
        if female_heat_cycles:
            heat_cycle = random.choice(female_heat_cycles)
            
            mating = MatingRecord()
            mating.female_id = female.id
            mating.male_id = male.id
            mating.heat_cycle_id = heat_cycle.id
            mating.mating_date = heat_cycle.start_date + timedelta(days=random.randint(5, 10))
            mating.mating_time = time(random.randint(8, 16), random.randint(0, 59))
            mating.location = 'مركز التربية المتخصص'
            mating.supervised_by = random.choice(breeders).id
            mating.success_rate = random.randint(7, 10)
            mating.duration_minutes = random.randint(15, 45)
            mating.behavior_observed = "سلوك طبيعي من كلا الكلبين"
            mating.notes = f"تزاوج ناجح بين {female.name} و {male.name}"
            
            created_records['matings'].append(mating)
            db.session.add(mating)
    
    db.session.commit()
    
    # 4. Create pregnancy records
    print("🤰 Creating pregnancy records...")
    for mating in created_records['matings']:
        pregnancy = PregnancyRecord()
        pregnancy.mating_record_id = mating.id
        pregnancy.dog_id = mating.female_id
        pregnancy.confirmed_date = mating.mating_date + timedelta(days=21)
        pregnancy.expected_delivery_date = mating.mating_date + timedelta(days=63)
        pregnancy.status = PregnancyStatus.DELIVERED
        
        # Weekly checkups
        for week in range(1, 9):
            checkup_data = {
                "weight": round(random.uniform(28, 35), 1),
                "appetite": random.choice(["جيد", "ممتاز", "متوسط"]),
                "behavior": random.choice(["طبيعي", "هادئ", "نشط"])
            }
            setattr(pregnancy, f"week_{week}_checkup", checkup_data)
        
        pregnancy.ultrasound_results = [
            {
                "date": (pregnancy.confirmed_date + timedelta(days=14)).isoformat(),
                "puppies_count": random.randint(3, 6),
                "notes": "تطور طبيعي للأجنة"
            }
        ]
        pregnancy.special_diet = "نظام غذائي عالي البروتين للكلاب الحوامل"
        pregnancy.exercise_restrictions = "تمارين خفيفة ومشي قصير"
        pregnancy.notes = "حمل طبيعي بدون مضاعفات"
        
        created_records['pregnancies'].append(pregnancy)
        db.session.add(pregnancy)
    
    db.session.commit()
    
    # 5. Create delivery records
    print("👶 Creating delivery records...")
    for pregnancy in created_records['pregnancies']:
        delivery = DeliveryRecord()
        delivery.pregnancy_record_id = pregnancy.id
        delivery.delivery_date = pregnancy.expected_delivery_date
        delivery.delivery_start_time = time(random.randint(6, 20), random.randint(0, 59))
        delivery.delivery_end_time = time(
            delivery.delivery_start_time.hour + random.randint(2, 6),
            random.randint(0, 59)
        )
        delivery.location = 'غرفة الولادة المجهزة'
        delivery.vet_present = random.choice(vets).id
        delivery.handler_present = random.choice(breeders).id
        delivery.assistance_required = random.choice([True, False])
        delivery.assistance_type = "مساعدة طبيعية" if delivery.assistance_required else "ولادة طبيعية"
        delivery.total_puppies = random.randint(3, 6)
        delivery.live_births = delivery.total_puppies
        delivery.stillbirths = 0
        delivery.mother_condition = "ممتازة"
        delivery.notes = f"ولادة ناجحة لـ {delivery.total_puppies} جراء أصحاء"
        
        created_records['deliveries'].append(delivery)
        db.session.add(delivery)
    
    db.session.commit()
    
    # 6. Create puppy records
    print("🐶 Creating puppy records...")
    for delivery in created_records['deliveries']:
        for puppy_num in range(1, delivery.total_puppies + 1):
            puppy = PuppyRecord()
            puppy.delivery_record_id = delivery.id
            puppy.puppy_number = puppy_num
            puppy.name = f"جرو {puppy_num}"
            puppy.temporary_id = f"PUP-{str(delivery.id)[-4:]}-{puppy_num:02d}"
            puppy.gender = random.choice(list(DogGender))
            puppy.birth_weight = round(random.uniform(0.3, 0.6), 2)
            puppy.birth_time = delivery.delivery_start_time
            puppy.birth_order = puppy_num
            puppy.alive_at_birth = True
            puppy.current_status = "صحي ونشط"
            puppy.color = random.choice(['بني فاتح', 'بني غامق', 'أسود', 'أسود وبني'])
            puppy.markings = "علامات طبيعية"
            
            # Weekly weight progression
            base_weight = puppy.birth_weight
            for week in range(1, 9):
                weight_gain = base_weight + (week * random.uniform(0.2, 0.4))
                setattr(puppy, f"week_{week}_weight", round(weight_gain, 2))
            
            puppy.weaning_date = delivery.delivery_date + timedelta(days=56)  # 8 weeks
            puppy.notes = f"جرو صحي رقم {puppy_num} من هذه الولادة"
            
            created_records['puppies'].append(puppy)
            db.session.add(puppy)
    
    db.session.commit()
    
    # 7. Create puppy training sessions
    print("🎓 Creating puppy training sessions...")
    trainers = [emp for emp in employees if emp.role == EmployeeRole.TRAINER]
    
    for puppy in created_records['puppies'][:6]:  # Focus on first 6 puppies
        trainer = random.choice(trainers)
        
        # Each puppy gets 2-3 training sessions
        for session_num in range(random.randint(2, 3)):
            training = PuppyTraining()
            training.puppy_id = puppy.id
            training.trainer_id = trainer.id
            training.training_name = random.choice([
                'التطبيع الاجتماعي الأساسي',
                'تدريب النظافة',
                'الأوامر البسيطة',
                'التعود على الأصوات',
                'تدريب المشي'
            ])
            training.training_type = random.choice(list(TrainingCategory))
            training.session_date = datetime.now() - timedelta(days=random.randint(1, 30))
            training.duration = random.randint(15, 30)  # Shorter sessions for puppies
            training.puppy_age_weeks = random.randint(8, 16)
            training.developmental_stage = random.choice([
                'مرحلة التطبيع',
                'مرحلة التعلم الأساسي',
                'مرحلة التطوير'
            ])
            training.success_rating = random.randint(6, 10)
            training.skills_learned = random.choice([
                ['الجلوس', 'الهدوء'],
                ['المشي', 'الاستجابة للاسم'],
                ['التفاعل الاجتماعي']
            ])
            training.behavior_observations = "سلوك ممتاز وتجاوب جيد مع التدريب"
            training.location = 'مركز تدريب الجراء'
            training.weather_conditions = 'معتدل'
            training.equipment_used = ['ألعاب تعليمية', 'مكافآت']
            training.notes = f"جلسة تدريبية ناجحة للجرو {puppy.name}"
            
            created_records['puppy_training'].append(training)
            db.session.add(training)
    
    db.session.commit()
    
    # Print summary
    for category, records in created_records.items():
        print(f"✅ Created {len(records)} {category} records")
    
    return created_records

def create_additional_data(dogs, employees, projects):
    """Create performance evaluations, incidents, and suspicions"""
    print("📈 Creating additional operational data...")
    
    # Create performance evaluations
    evaluations = []
    for project in projects[:3]:  # Focus on first 3 projects
        # Evaluate some employees and dogs
        for i in range(random.randint(2, 4)):
            evaluation = PerformanceEvaluation()
            evaluation.project_id = project.id
            evaluation.evaluator_id = 1  # Admin user
            
            if random.choice([True, False]):
                # Evaluate employee
                employee = random.choice(employees[:5])
                evaluation.target_type = TargetType.EMPLOYEE
                evaluation.target_employee_id = employee.id
                evaluation.uniform_ok = True
                evaluation.id_card_ok = True
                evaluation.appearance_ok = True
                evaluation.cleanliness_ok = True
                evaluation.punctuality = random.randint(7, 10)
                evaluation.job_knowledge = random.randint(7, 10)
                evaluation.teamwork = random.randint(7, 10)
                evaluation.communication = random.randint(7, 10)
            else:
                # Evaluate dog
                dog = random.choice(dogs[:8])
                evaluation.target_type = TargetType.DOG
                evaluation.target_dog_id = dog.id
                evaluation.obedience_level = random.randint(7, 10)
                evaluation.detection_accuracy = random.randint(7, 10)
                evaluation.physical_condition = random.randint(7, 10)
                evaluation.handler_relationship = random.randint(7, 10)
            
            evaluation.evaluation_date = date.today() - timedelta(days=random.randint(1, 60))
            evaluation.rating = random.choice(list(PerformanceRating))
            evaluation.strengths = "أداء ممتاز في المهام المطلوبة"
            evaluation.areas_for_improvement = "مواصلة التطوير في بعض المجالات"
            evaluation.comments = "تقييم إيجابي بشكل عام"
            
            evaluations.append(evaluation)
            db.session.add(evaluation)
    
    # Create some incidents
    incidents = []
    for project in projects[:2]:  # Active projects only
        if project.status == ProjectStatus.ACTIVE:
            incident = Incident()
            incident.project_id = project.id
            incident.name = random.choice([
                'تأخير في الوصول',
                'خلل في المعدات',
                'إنذار كاذب',
                'مشكلة في التواصل'
            ])
            incident.incident_date = date.today() - timedelta(days=random.randint(1, 30))
            incident.incident_time = time(random.randint(8, 17), random.randint(0, 59))
            incident.incident_type = 'عملياتي'
            incident.description = f"حادث {incident.name} في مشروع {project.name}"
            incident.location = project.location
            incident.severity = random.choice(['LOW', 'MEDIUM'])
            incident.reported_by = random.choice(employees).id
            incident.resolved = True
            incident.resolution_notes = "تم حل المشكلة بنجاح"
            incident.resolution_date = incident.incident_date + timedelta(days=1)
            
            incidents.append(incident)
            db.session.add(incident)
    
    # Create some suspicions/detections
    suspicions = []
    for project in projects[:2]:
        if project.status == ProjectStatus.ACTIVE:
            suspicion = Suspicion()
            suspicion.project_id = project.id
            suspicion.element_type = random.choice(list(ElementType))
            suspicion.suspicion_type = f"اشتباه {suspicion.element_type.value}"
            suspicion.risk_level = random.choice(['LOW', 'MEDIUM'])
            suspicion.discovery_date = date.today() - timedelta(days=random.randint(1, 30))
            suspicion.discovery_time = time(random.randint(8, 17), random.randint(0, 59))
            suspicion.location = project.location
            suspicion.detected_by_dog = random.choice(dogs[:5]).id
            suspicion.handler = random.choice(employees[:3]).id
            suspicion.detection_method = 'K9 Alert'
            suspicion.description = f"تم اكتشاف {suspicion.element_type.value} مشتبه به"
            suspicion.authorities_notified = True
            suspicion.evidence_collected = True
            suspicion.follow_up_required = False
            suspicion.follow_up_notes = "تم التعامل مع الحالة بنجاح"
            
            suspicions.append(suspicion)
            db.session.add(suspicion)
    
    db.session.commit()
    
    print(f"✅ Created {len(evaluations)} performance evaluations")
    print(f"✅ Created {len(incidents)} incidents")
    print(f"✅ Created {len(suspicions)} suspicions")

def main():
    """Main function to populate comprehensive K9 system data"""
    with app.app_context():
        print("🌟 Starting comprehensive K9 operations data population...")
        
        # Clear existing data
        clear_existing_data()
        
        # Create all data in proper order
        employees = create_employees()
        dogs = create_dogs()
        projects = create_projects(employees)
        training_sessions = create_training_sessions(dogs, employees)
        veterinary_visits = create_veterinary_visits(dogs, employees)
        breeding_records = create_breeding_system(dogs, employees)
        create_additional_data(dogs, employees, projects)
        
        print("\n🎉 Comprehensive K9 Operations data population completed!")
        print("\n📊 Summary:")
        print(f"   👥 Employees: {len(employees)} (across all roles)")
        print(f"   🐕 Dogs: {len(dogs)} (diverse breeds and specializations)")
        print(f"   📋 Projects: {len(projects)} (various statuses)")
        print(f"   🎯 Training Sessions: {len(training_sessions)} (all categories)")
        print(f"   🏥 Veterinary Visits: {len(veterinary_visits)} (all types)")
        print(f"   🐕‍🦺 Breeding Records: {sum(len(records) for records in breeding_records.values())}")
        print("\n🔐 Login credentials:")
        print("   admin / admin123 (General Admin)")
        print("\n✨ Your K9 Operations Management System is now fully populated with realistic data!")

if __name__ == "__main__":
    main()