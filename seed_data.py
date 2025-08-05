#!/usr/bin/env python3
"""
Seed script to populate the K9 Operations Management System with sample data.
Run this script to add demo data for testing and demonstration purposes.
"""

import os
import sys
from datetime import datetime, date, timedelta
import random
from app import app, db
from models import (
    User, UserRole, Dog, DogGender, DogStatus, Employee, EmployeeRole,
    Project, ProjectStatus, TrainingSession, TrainingCategory,
    VeterinaryVisit, VisitType, BreedingCycle, BreedingCycleType,
    ProjectAssignment, Incident, Suspicion, PerformanceEvaluation,
    PerformanceRating, TargetType, AuditLog, AuditAction,
    ProjectShift, ProjectShiftAssignment, ProjectAttendance,
    AttendanceStatus, AbsenceReason, EntityType, ElementType
)
from werkzeug.security import generate_password_hash
import uuid

def clear_existing_data():
    """Clear existing data (except admin user) to start fresh."""
    print("🧹 Clearing existing data...")
    
    # Delete in reverse dependency order
    db.session.query(ProjectAttendance).delete()
    db.session.query(ProjectShiftAssignment).delete()
    db.session.query(ProjectShift).delete()
    db.session.query(PerformanceEvaluation).delete()
    db.session.query(Suspicion).delete()
    db.session.query(Incident).delete()
    db.session.query(ProjectAssignment).delete()
    db.session.query(BreedingCycle).delete()
    db.session.query(VeterinaryVisit).delete()
    db.session.query(TrainingSession).delete()
    db.session.query(Project).delete()
    db.session.query(Employee).delete()
    db.session.query(Dog).delete()
    db.session.query(AuditLog).delete()
    
    # Keep admin user, delete others
    db.session.query(User).filter(User.username != 'admin').delete()
    
    db.session.commit()
    print("✅ Existing data cleared")

def create_users():
    """Create sample users."""
    print("👥 Creating users...")
    
    users = [
        {
            'username': 'manager1',
            'email': 'manager1@k9ops.com',
            'password': 'manager123',
            'role': UserRole.PROJECT_MANAGER,
            'full_name': 'أحمد محمد العلي',
            'active': True
        },
        {
            'username': 'manager2',
            'email': 'manager2@k9ops.com',
            'password': 'manager123',
            'role': UserRole.PROJECT_MANAGER,
            'full_name': 'فاطمة سعد الدين',
            'active': True
        },
        {
            'username': 'manager3',
            'email': 'manager3@k9ops.com',
            'password': 'manager123',
            'role': UserRole.PROJECT_MANAGER,
            'full_name': 'خالد عبد الرحمن',
            'active': True
        }
    ]
    
    created_users = []
    for user_data in users:
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            password_hash=generate_password_hash(user_data['password']),
            role=user_data['role'],
            full_name=user_data['full_name'],
            active=user_data['active']
        )
        db.session.add(user)
        created_users.append(user)
    
    db.session.commit()
    print(f"✅ Created {len(created_users)} users")
    return created_users

def create_dogs():
    """Create sample dogs."""
    print("🐕 Creating dogs...")
    
    dog_names = [
        'ريكس', 'ماكس', 'بيلا', 'تشارلي', 'لونا', 'روكي', 'ديزي', 'بادي',
        'مولي', 'جاك', 'صوفيا', 'تايتان', 'زوي', 'كوبر', 'ليلى', 'هنتر'
    ]
    
    breeds = [
        'الراعي الألماني', 'الراعي البلجيكي', 'اللابرادور', 'الروت وايلر',
        'الدوبرمان', 'البيتبول', 'الجولدن ريتريفر', 'الهاسكي السيبيري'
    ]
    
    colors = ['أسود', 'بني', 'أبيض', 'رمادي', 'ذهبي', 'مختلط']
    
    dogs = []
    for i, name in enumerate(dog_names):
        # Create birth date between 1-8 years ago
        birth_date = date.today() - timedelta(days=random.randint(365, 365*8))
        
        dog = Dog(
            name=name,
            code=f"DOG{1000 + i}",
            breed=random.choice(breeds),
            gender=random.choice(list(DogGender)),
            birth_date=birth_date,
            color=random.choice(colors),
            weight=round(random.uniform(20.0, 45.0), 1),
            height=round(random.uniform(55.0, 70.0), 1),
            microchip_id=f"MC{random.randint(100000, 999999)}",
            current_status=random.choice([DogStatus.ACTIVE, DogStatus.TRAINING, DogStatus.ACTIVE]),
            specialization=random.choice([
                'كشف المتفجرات',
                'كشف المخدرات', 
                'التتبع والبحث',
                'الحراسة الأمنية',
                'البحث والإنقاذ'
            ]) if random.random() > 0.3 else None
        )
        db.session.add(dog)
        dogs.append(dog)
    
    db.session.commit()
    print(f"✅ Created {len(dogs)} dogs")
    return dogs

def create_employees():
    """Create sample employees."""
    print("👨‍💼 Creating employees...")
    
    handlers = [
        'محمد أحمد السالم', 'علي حسن الطويل', 'سارة محمود فتحي', 'نور الدين عباس',
        'رامي خالد الشمري', 'ليلى عمر القاسم', 'يوسف إبراهيم النجار', 'دينا سمير حسن'
    ]
    
    vets = [
        'د. أحمد محمد البيطري', 'د. فاطمة علي الحكيم', 'د. خالد سعد الطبيب'
    ]
    
    project_managers = [
        'عمر محمد الإداري', 'نادية أحمد المشرفة', 'سامي خالد المنسق'
    ]
    
    employees = []
    
    # Create handlers
    for i, name in enumerate(handlers):
        employee = Employee(
            employee_id=f"H{1000 + i}",
            name=name,
            role=EmployeeRole.HANDLER,
            phone=f"+966{random.randint(500000000, 599999999)}",
            email=f"handler{i+1}@k9ops.com",
            hire_date=date.today() - timedelta(days=random.randint(30, 1800)),
            is_active=random.choice([True, True, True, False])  # 75% active
        )
        db.session.add(employee)
        employees.append(employee)
    
    # Create veterinarians
    for i, name in enumerate(vets):
        employee = Employee(
            employee_id=f"V{2000 + i}",
            name=name,
            role=EmployeeRole.VET,
            phone=f"+966{random.randint(500000000, 599999999)}",
            email=f"vet{i+1}@k9ops.com",
            hire_date=date.today() - timedelta(days=random.randint(365, 2500)),
            is_active=True
        )
        db.session.add(employee)
        employees.append(employee)
    
    # Create project managers
    for i, name in enumerate(project_managers):
        employee = Employee(
            employee_id=f"PM{3000 + i}",
            name=name,
            role=EmployeeRole.PROJECT_MANAGER,
            phone=f"+966{random.randint(500000000, 599999999)}",
            email=f"pm{i+1}@k9ops.com",
            hire_date=date.today() - timedelta(days=random.randint(180, 2000)),
            is_active=True
        )
        db.session.add(employee)
        employees.append(employee)
    
    db.session.commit()
    print(f"✅ Created {len(employees)} employees")
    return employees

def create_projects(users, dogs, employees):
    """Create sample projects."""
    print("📋 Creating projects...")
    
    project_names = [
        'أمن المطار الملكي', 'حراسة القصر الملكي', 'عمليات مكافحة المخدرات',
        'أمن الحدود الشمالية', 'حماية المنشآت الحيوية', 'عمليات البحث والإنقاذ',
        'أمن المهرجانات والفعاليات', 'دوريات المناطق الحضرية'
    ]
    
    locations = [
        'مطار الملك خالد الدولي', 'القصر الملكي', 'الحدود مع الأردن',
        'منطقة نجران', 'محطة الكهرباء الرئيسية', 'الرياض وسط المدينة',
        'ملعب الجوهرة', 'حي الدبلوماسيين'
    ]
    
    mission_types = [
        'كشف المتفجرات', 'كشف المخدرات', 'الحراسة الأمنية',
        'التتبع والبحث', 'الإنقاذ', 'الدوريات'
    ]
    
    projects = []
    for i, name in enumerate(project_names):
        start_date = date.today() - timedelta(days=random.randint(0, 180))
        
        # Some projects completed, some active, some planned
        if i < 3:
            status = ProjectStatus.ACTIVE
            end_date = None
        elif i < 5:
            status = ProjectStatus.COMPLETED
            end_date = start_date + timedelta(days=random.randint(30, 120))
        else:
            status = ProjectStatus.PLANNED
            start_date = date.today() + timedelta(days=random.randint(1, 60))
            end_date = None
        
        project = Project(
            name=name,
            code=f"PRJ{1000 + i}",
            description=f"مشروع {name} يهدف إلى تعزيز الأمن والسلامة في المنطقة المحددة",
            main_task=f"المهمة الأساسية: {random.choice(mission_types)}",
            start_date=start_date,
            expected_completion_date=start_date + timedelta(days=random.randint(90, 365)) if status != ProjectStatus.COMPLETED else None,
            end_date=end_date,
            status=status,
            manager_id=random.choice(users).id,
            location=locations[i],
            mission_type=mission_types[i % len(mission_types)],
            priority=random.choice(['HIGH', 'MEDIUM', 'LOW', 'CRITICAL'])
        )
        db.session.add(project)
        projects.append(project)
    
    db.session.commit()
    print(f"✅ Created {len(projects)} projects")
    return projects

def create_assignments(projects, dogs, employees):
    """Create project assignments."""
    print("🔗 Creating project assignments...")
    
    assignments = []
    
    for project in projects:
        # Assign 2-4 dogs per project
        assigned_dogs = random.sample(dogs, random.randint(2, min(4, len(dogs))))
        for dog in assigned_dogs:
            assignment = ProjectAssignment(
                project_id=project.id,
                dog_id=dog.id,
                assigned_date=project.start_date,
                is_active=project.status in [ProjectStatus.ACTIVE, ProjectStatus.PLANNED]
            )
            db.session.add(assignment)
            assignments.append(assignment)
        
        # Assign 2-3 employees per project
        # Get handlers and one vet
        handlers = [e for e in employees if e.role == EmployeeRole.HANDLER and e.is_active]
        vets = [e for e in employees if e.role == EmployeeRole.VET]
        
        assigned_handlers = random.sample(handlers, random.randint(2, min(3, len(handlers))))
        for handler in assigned_handlers:
            assignment = ProjectAssignment(
                project_id=project.id,
                employee_id=handler.id,
                assigned_date=project.start_date,
                is_active=project.status in [ProjectStatus.ACTIVE, ProjectStatus.PLANNED]
            )
            db.session.add(assignment)
            assignments.append(assignment)
        
        # Add one vet to some projects
        if random.random() > 0.4 and vets:
            vet = random.choice(vets)
            assignment = ProjectAssignment(
                project_id=project.id,
                employee_id=vet.id,
                assigned_date=project.start_date,
                is_active=project.status in [ProjectStatus.ACTIVE, ProjectStatus.PLANNED]
            )
            db.session.add(assignment)
            assignments.append(assignment)
    
    db.session.commit()
    print(f"✅ Created {len(assignments)} project assignments")
    return assignments

def create_training_sessions(dogs, employees):
    """Create sample training sessions."""
    print("🎯 Creating training sessions...")
    
    trainers = [e for e in employees if e.role == EmployeeRole.HANDLER and e.is_active]
    training_sessions = []
    
    for dog in dogs[:10]:  # Create sessions for first 10 dogs
        # Create 3-8 training sessions per dog over the last 6 months
        num_sessions = random.randint(3, 8)
        for _ in range(num_sessions):
            session_date = datetime.now() - timedelta(days=random.randint(1, 180))
            
            session = TrainingSession(
                dog_id=dog.id,
                trainer_id=random.choice(trainers).id,
                session_date=session_date,
                category=random.choice(list(TrainingCategory)),
                duration=random.randint(30, 120),
                subject=random.choice([
                    'تدريب على الطاعة الأساسية',
                    'تمارين كشف المتفجرات', 
                    'تدريب التتبع والبحث',
                    'تمارين اللياقة البدنية',
                    'تدريب الهجوم والدفاع'
                ]),
                notes=random.choice([
                    'أداء ممتاز، تحسن واضح',
                    'يحتاج المزيد من التدريب',
                    'استجابة جيدة للأوامر',
                    'تقدم مرضي في الأداء'
                ]) if random.random() > 0.3 else None,
                success_rating=random.randint(7, 10)
            )
            db.session.add(session)
            training_sessions.append(session)
    
    db.session.commit()
    print(f"✅ Created {len(training_sessions)} training sessions")
    return training_sessions

def create_veterinary_visits(dogs, employees):
    """Create sample veterinary visits."""
    print("🏥 Creating veterinary visits...")
    
    vets = [e for e in employees if e.role == EmployeeRole.VET]
    if not vets:
        print("⚠️ No veterinarians found, skipping vet visits")
        return []
    
    vet_visits = []
    
    for dog in dogs:
        # Create 1-4 visits per dog over the last year
        num_visits = random.randint(1, 4)
        for _ in range(num_visits):
            visit_date = datetime.now() - timedelta(days=random.randint(1, 365))
            
            visit = VeterinaryVisit(
                dog_id=dog.id,
                vet_id=random.choice(vets).id,
                visit_date=visit_date,
                visit_type=random.choice(list(VisitType)),
                symptoms=random.choice([
                    'فحص دوري شامل',
                    'تطعيمات سنوية',
                    'فحص الأسنان والفم',
                    'مشكلة في الجهاز الهضمي',
                    'إصابة طفيفة في القدم',
                    'فحص العيون'
                ]),
                diagnosis=random.choice([
                    'حالة صحية جيدة',
                    'التهاب طفيف في الأذن',
                    'تم إعطاء التطعيمات المطلوبة',
                    'حساسية جلدية بسيطة',
                    'كل شيء طبيعي'
                ]),
                treatment=random.choice([
                    'لا يحتاج علاج',
                    'مضاد حيوي لمدة 5 أيام',
                    'قطرة للعين مرتين يومياً',
                    'كريم مضاد للحساسية',
                    'مراجعة بعد أسبوعين'
                ]),
                cost=round(random.uniform(100.0, 800.0), 2),
                weight=round(random.uniform(20.0, 45.0), 1),
                temperature=round(random.uniform(38.0, 39.2), 1),
                notes=random.choice([
                    'الكلب بحالة ممتازة',
                    'يحتاج متابعة دورية',
                    'استجاب جيداً للعلاج',
                    None
                ])
            )
            db.session.add(visit)
            vet_visits.append(visit)
    
    db.session.commit()
    print(f"✅ Created {len(vet_visits)} veterinary visits")
    return vet_visits

def create_incidents_and_suspicions(projects):
    """Create sample incidents and suspicions."""
    print("⚠️ Creating incidents and suspicions...")
    
    active_projects = [p for p in projects if p.status == ProjectStatus.ACTIVE]
    incidents = []
    suspicions = []
    
    # Create incidents
    for project in active_projects[:4]:  # Add incidents to first 4 active projects
        num_incidents = random.randint(1, 3)
        for _ in range(num_incidents):
            incident_date = datetime.now() - timedelta(days=random.randint(1, 90))
            
            incident = Incident(
                project_id=project.id,
                name=random.choice([
                    'إصابة طفيفة', 'عطل في المعدات', 'مشكلة أمنية',
                    'عدم امتثال للبروتوكول', 'حادث مروري'
                ]),
                incident_date=incident_date.date(),
                incident_time=incident_date.time(),
                incident_type=random.choice([
                    'إصابة', 'عطل', 'أمني', 'إجرائي', 'مروري'
                ]),
                description=random.choice([
                    'إصابة طفيفة في يد أحد السائسين أثناء التدريب',
                    'عطل في جهاز كشف المعادن',
                    'اشتباه في دخول شخص غير مصرح له',
                    'عدم اتباع إجراءات السلامة المحددة',
                    'حادث بسيط للمركبة أثناء الدورية'
                ]),
                severity=random.choice(['LOW', 'MEDIUM', 'HIGH']),
                resolved=random.choice([True, False]),
                resolution_notes=random.choice([
                    'تم حل المشكلة بنجاح',
                    'اتخذت الإجراءات التصحيحية اللازمة',
                    'في انتظار قطع الغيار',
                    None
                ]) if random.random() > 0.3 else None
            )
            db.session.add(incident)
            incidents.append(incident)
    
    # Create suspicions
    for project in active_projects[:3]:  # Add suspicions to first 3 active projects
        num_suspicions = random.randint(1, 2)
        for _ in range(num_suspicions):
            discovery_date = datetime.now() - timedelta(days=random.randint(1, 60))
            
            suspicion = Suspicion(
                project_id=project.id,
                element_type=random.choice(list(ElementType)),
                subtype=random.choice([
                    'مواد مشبوهة', 'سلوك مريب', 'صوت غريب',
                    'رائحة مشبوهة', 'حركة غير طبيعية'
                ]),
                discovery_date=discovery_date.date(),
                discovery_time=discovery_date.time(),
                location=f"{project.location} - {random.choice(['البوابة الرئيسية', 'الجانب الشرقي', 'المدخل الخلفي'])}",
                description=random.choice([
                    'الكلب أظهر اهتماماً غير عادي بحقيبة معينة',
                    'لوحظ سلوك مريب من أحد الزوار',
                    'سمع صوت غريب من المنطقة المحظورة',
                    'الكلب أشار إلى وجود رائحة مشبوهة',
                    'حركة غير طبيعية في الكاميرات الأمنية'
                ]),
                evidence_collected=random.choice([True, False]),
                follow_up_required=random.choice([True, False]),
                follow_up_notes=random.choice([
                    'إنذار كاذب - لا يوجد خطر',
                    'تم العثور على مواد محظورة',
                    'تحت التحقيق',
                    None
                ]) if random.random() > 0.4 else None
            )
            db.session.add(suspicion)
            suspicions.append(suspicion)
    
    db.session.commit()
    print(f"✅ Created {len(incidents)} incidents and {len(suspicions)} suspicions")
    return incidents, suspicions

def main():
    """Main function to seed all data."""
    print("🌱 Starting data seeding process...")
    print("=" * 50)
    
    with app.app_context():
        try:
            # Clear existing data
            clear_existing_data()
            
            # Create all sample data
            users = create_users()
            dogs = create_dogs()
            employees = create_employees()
            projects = create_projects(users, dogs, employees)
            assignments = create_assignments(projects, dogs, employees)
            training_sessions = create_training_sessions(dogs, employees)
            vet_visits = create_veterinary_visits(dogs, employees)
            incidents, suspicions = create_incidents_and_suspicions(projects)
            
            print("=" * 50)
            print("🎉 Data seeding completed successfully!")
            print(f"📊 Summary:")
            print(f"   👥 Users: {len(users) + 1} (including admin)")  # +1 for admin
            print(f"   🐕 Dogs: {len(dogs)}")
            print(f"   👨‍💼 Employees: {len(employees)}")
            print(f"   📋 Projects: {len(projects)}")
            print(f"   🔗 Assignments: {len(assignments)}")
            print(f"   🎯 Training sessions: {len(training_sessions)}")
            print(f"   🏥 Veterinary visits: {len(vet_visits)}")
            print(f"   ⚠️ Incidents: {len(incidents)}")
            print(f"   🔍 Suspicions: {len(suspicions)}")
            print()
            print("🔑 Default login credentials:")
            print("   Admin: username=admin, password=admin123")
            print("   Manager 1: username=manager1, password=manager123")
            print("   Manager 2: username=manager2, password=manager123")
            print("   Manager 3: username=manager3, password=manager123")
            
        except Exception as e:
            print(f"❌ Error during seeding: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    main()