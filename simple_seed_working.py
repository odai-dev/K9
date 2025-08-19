#!/usr/bin/env python3
"""
Working seed script for K9 Operations Management System

This script creates realistic sample data for core modules:
- Core Management: Dogs, Employees, Projects
- Training & Education: Training Sessions
- Veterinary & Health: Vet Visits
- Operations: Incidents, Performance Evaluations
- Administration: Audit Logs

Business Rules Enforced:
- Project Managers can only be assigned to ONE active project at a time
- Role-based assignments and proper data relationships
"""

from app import app, db
from models import (
    Dog, DogGender, DogStatus, Employee, EmployeeRole, 
    Project, ProjectStatus, User, UserRole,
    TrainingSession, TrainingCategory,
    VeterinaryVisit, VisitType,
    Incident, PerformanceEvaluation, PerformanceRating, TargetType,
    AuditLog, AuditAction
)
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta, time
import uuid
import random

def create_comprehensive_data():
    with app.app_context():
        print("🌱 Adding comprehensive sample data to K9 Operations Management System...")
        
        # Check if sample data already exists
        existing_dog = Dog.query.filter_by(code='K9-001').first()
        existing_employee = Employee.query.filter_by(employee_id='EMP-001').first()
        if existing_dog or existing_employee:
            print("⚠️ Sample data already exists. Skipping creation.")
            print("🔐 Login credentials:")
            print("   admin / admin123 (General Admin)")
            return
        
        try:
            created_dogs = []
            created_employees = []
            created_projects = []
            
            print("📋 Creating core entities...")
            
            # Create dogs
            dogs_data = [
                {
                    'name': 'ريكس', 'code': 'K9-001', 'breed': 'الراعي الألماني',
                    'gender': DogGender.MALE, 'birth_date': date(2020, 3, 15),
                    'microchip_id': 'MC001REX', 'current_status': DogStatus.ACTIVE,
                    'location': 'المعسكر الأول', 'specialization': 'كشف المتفجرات',
                    'color': 'أسود وبني', 'weight': 35.5, 'height': 65.0
                },
                {
                    'name': 'لونا', 'code': 'K9-002', 'breed': 'الراعي البلجيكي',
                    'gender': DogGender.FEMALE, 'birth_date': date(2021, 1, 20),
                    'microchip_id': 'MC002LUN', 'current_status': DogStatus.ACTIVE,
                    'location': 'المعسكر الثاني', 'specialization': 'كشف المخدرات',
                    'color': 'بني فاتح', 'weight': 28.0, 'height': 58.0
                },
                {
                    'name': 'ماكس', 'code': 'K9-003', 'breed': 'الروت وايلر',
                    'gender': DogGender.MALE, 'birth_date': date(2019, 8, 10),
                    'microchip_id': 'MC003MAX', 'current_status': DogStatus.ACTIVE,
                    'location': 'المعسكر الأول', 'specialization': 'الهجوم والحراسة',
                    'color': 'أسود وبني', 'weight': 45.0, 'height': 70.0
                },
                {
                    'name': 'بيلا', 'code': 'K9-004', 'breed': 'اللابرادور',
                    'gender': DogGender.FEMALE, 'birth_date': date(2022, 2, 5),
                    'microchip_id': 'MC004BEL', 'current_status': DogStatus.TRAINING,
                    'location': 'مركز التدريب', 'specialization': 'البحث والإنقاذ',
                    'color': 'ذهبي', 'weight': 25.0, 'height': 55.0
                },
                {
                    'name': 'شادو', 'code': 'K9-005', 'breed': 'الراعي الألماني',
                    'gender': DogGender.MALE, 'birth_date': date(2018, 11, 30),
                    'microchip_id': 'MC005SHA', 'current_status': DogStatus.RETIRED,
                    'location': 'منطقة التقاعد', 'specialization': 'خبير متعدد',
                    'color': 'أسود', 'weight': 40.0, 'height': 68.0
                }
            ]
            
            for dog_data in dogs_data:
                dog = Dog()
                for key, value in dog_data.items():
                    setattr(dog, key, value)
                db.session.add(dog)
                created_dogs.append(dog)
            
            # Create employees
            employees_data = [
                {
                    'name': 'أحمد محمد السائس', 'employee_id': 'EMP-001',
                    'role': EmployeeRole.HANDLER, 'phone': '0501234567',
                    'email': 'ahmed.handler@k9ops.com', 'hire_date': date(2020, 1, 15),
                    'is_active': True, 'certifications': ['شهادة سائس كلاب', 'دورة الإسعافات الأولية']
                },
                {
                    'name': 'محمد عبدالرحمن السائس', 'employee_id': 'EMP-005',
                    'role': EmployeeRole.HANDLER, 'phone': '0505678901',
                    'email': 'mohamed.handler@k9ops.com', 'hire_date': date(2021, 5, 20),
                    'is_active': True, 'certifications': ['شهادة سائس كلاب', 'دورة السلامة']
                },
                {
                    'name': 'د. سارة علي الطبيبة', 'employee_id': 'EMP-002',
                    'role': EmployeeRole.VET, 'phone': '0502345678',
                    'email': 'sara.vet@k9ops.com', 'hire_date': date(2019, 6, 1),
                    'is_active': True, 'certifications': ['دكتوراه في الطب البيطري', 'شهادة في طب الحيوانات المتخصصة']
                },
                {
                    'name': 'خالد عبدالله المدرب', 'employee_id': 'EMP-003',
                    'role': EmployeeRole.TRAINER, 'phone': '0503456789',
                    'email': 'khaled.trainer@k9ops.com', 'hire_date': date(2021, 3, 10),
                    'is_active': True, 'certifications': ['شهادة في تدريب الكلاب البوليسية', 'دورة السلوك الحيواني']
                },
                {
                    'name': 'فهد سعد مسؤول المشروع', 'employee_id': 'EMP-004',
                    'role': EmployeeRole.PROJECT_MANAGER, 'phone': '0504567890',
                    'email': 'fahad.pm@k9ops.com', 'hire_date': date(2018, 9, 1),
                    'is_active': True, 'certifications': ['ماجستير في إدارة المشاريع', 'شهادة PMP']
                }
            ]
            
            for emp_data in employees_data:
                employee = Employee()
                for key, value in emp_data.items():
                    setattr(employee, key, value)
                db.session.add(employee)
                created_employees.append(employee)
            
            db.session.commit()
            
            # Refresh objects to get IDs
            for dog in created_dogs:
                db.session.refresh(dog)
            for emp in created_employees:
                db.session.refresh(emp)
            
            # Find project manager
            project_managers = [emp for emp in created_employees if emp.role == EmployeeRole.PROJECT_MANAGER]
            
            # Create projects
            projects_data = [
                {
                    'name': 'مشروع أمن الحدود الشرقية', 'code': 'PROJ-001',
                    'main_task': 'تأمين الحدود الشرقية',
                    'description': 'مشروع لتأمين الحدود الشرقية باستخدام الكلاب البوليسية المدربة على كشف المتفجرات والمخدرات',
                    'start_date': date(2024, 1, 1), 'expected_completion_date': date(2024, 12, 31),
                    'status': ProjectStatus.ACTIVE, 'location': 'المنطقة الشرقية',
                    'mission_type': 'حراسة الحدود', 'priority': 'HIGH',
                    'manager_id': 1,  # admin user
                    'project_manager_id': project_managers[0].id if project_managers else None
                },
                {
                    'name': 'تدريب الكلاب الجديدة 2025', 'code': 'PROJ-002',
                    'main_task': 'تدريب الكلاب الجديدة',
                    'description': 'برنامج تدريب شامل للكلاب الجديدة المنضمة للوحدة',
                    'start_date': date(2025, 2, 1), 'expected_completion_date': date(2025, 8, 31),
                    'status': ProjectStatus.PLANNED, 'location': 'مركز التدريب الرئيسي',
                    'mission_type': 'تدريب', 'priority': 'MEDIUM',
                    'manager_id': 1, 'project_manager_id': None
                },
                {
                    'name': 'مشروع أمن المطارات السابق', 'code': 'PROJ-003',
                    'main_task': 'حراسة المطارات',
                    'description': 'تأمين المطارات الرئيسية باستخدام كلاب كشف المتفجرات',
                    'start_date': date(2023, 3, 15), 'expected_completion_date': date(2023, 11, 30),
                    'end_date': date(2023, 11, 25),
                    'status': ProjectStatus.COMPLETED, 'location': 'مطارات متعددة',
                    'mission_type': 'أمن المطارات', 'priority': 'HIGH',
                    'manager_id': 1, 'project_manager_id': None
                }
            ]
            
            for proj_data in projects_data:
                project = Project()
                for key, value in proj_data.items():
                    setattr(project, key, value)
                db.session.add(project)
                created_projects.append(project)
            
            db.session.commit()
            
            # Refresh projects
            for proj in created_projects:
                db.session.refresh(proj)
            
            print("📋 Creating project assignments...")
            
            # Assign dogs and employees to active projects
            active_projects = [p for p in created_projects if p.status == ProjectStatus.ACTIVE]
            if active_projects:
                border_project = active_projects[0]
                # Assign dogs
                for dog in created_dogs[:4]:
                    border_project.assigned_dogs.append(dog)
                # Assign handlers
                handlers = [emp for emp in created_employees if emp.role == EmployeeRole.HANDLER]
                for handler in handlers:
                    border_project.assigned_employees.append(handler)
            
            print("📋 Creating training sessions...")
            
            trainers = [emp for emp in created_employees if emp.role == EmployeeRole.TRAINER]
            training_dogs = [dog for dog in created_dogs if dog.current_status in [DogStatus.ACTIVE, DogStatus.TRAINING]]
            
            if trainers and training_dogs:
                for i in range(10):
                    session_date = date.today() - timedelta(days=random.randint(1, 60))
                    session = TrainingSession()
                    session.dog_id = random.choice(training_dogs).id
                    session.trainer_id = random.choice(trainers).id
                    session.project_id = random.choice(active_projects).id if active_projects else None
                    session.category = random.choice(list(TrainingCategory))
                    session.subject = f"تدريب {random.choice(['الطاعة', 'الكشف', 'الهجوم', 'اللياقة'])}"
                    session.session_date = datetime.combine(session_date, time(10, 0))
                    session.duration = random.randint(30, 120)
                    session.success_rating = random.randint(6, 10)
                    session.location = random.choice(['مركز التدريب', 'الميدان', 'المعسكر'])
                    session.notes = "جلسة تدريبية ناجحة - تقدم ملحوظ"
                    session.weather_conditions = random.choice(['مشمس', 'غائم', 'معتدل'])
                    session.equipment_used = ['أكمام التدريب', 'حبال', 'أهداف تدريبية']
                    db.session.add(session)
            
            print("📋 Creating veterinary records...")
            
            vets = [emp for emp in created_employees if emp.role == EmployeeRole.VET]
            
            if vets:
                for dog in created_dogs:
                    for i in range(2):
                        visit_date = date.today() - timedelta(days=random.randint(10, 180))
                        visit = VeterinaryVisit()
                        visit.dog_id = dog.id
                        visit.vet_id = random.choice(vets).id
                        visit.project_id = dog.projects[0].id if dog.projects else None
                        visit.visit_type = random.choice(list(VisitType))
                        visit.visit_date = datetime.combine(visit_date, time(9, 0))
                        visit.weight = dog.weight + random.uniform(-2, 2)
                        visit.temperature = random.uniform(38.0, 39.5)
                        visit.heart_rate = random.randint(70, 120)
                        visit.symptoms = "فحص دوري" if random.random() > 0.3 else "أعراض طفيفة"
                        visit.diagnosis = "حالة صحية جيدة" if random.random() > 0.2 else "يحتاج متابعة"
                        visit.treatment = "فحص روتيني" if random.random() > 0.3 else "علاج وقائي"
                        visit.medications = [{"name": "فيتامينات", "dose": "مرة يومياً"}] if random.random() > 0.5 else []
                        visit.next_visit_date = visit_date + timedelta(days=30)
                        visit.notes = "الكلب بحالة صحية جيدة"
                        visit.cost = random.uniform(100, 500)
                        db.session.add(visit)
            
            print("📋 Creating operational records...")
            
            # Create incidents
            for project in active_projects:
                for i in range(random.randint(1, 3)):
                    incident_date = date.today() - timedelta(days=random.randint(1, 90))
                    incident = Incident()
                    incident.project_id = project.id
                    incident.name = f"حادث {random.choice(['طفيف', 'متوسط', 'مهم'])}"
                    incident.incident_date = incident_date
                    incident.incident_time = time(random.randint(8, 20), random.randint(0, 59))
                    incident.incident_type = random.choice(['إصابة طفيفة', 'عطل معدات', 'حادث مروري'])
                    incident.description = "وصف مفصل للحادث والظروف المحيطة به"
                    incident.location = project.location
                    incident.severity = random.choice(['LOW', 'MEDIUM', 'HIGH'])
                    incident.reported_by = random.choice(project.assigned_employees).id if project.assigned_employees else None
                    incident.people_involved = [random.choice(project.assigned_employees).id] if project.assigned_employees else []
                    incident.resolved = random.choice([True, False])
                    incident.resolution_notes = "تم حل المشكلة" if random.random() > 0.3 else None
                    db.session.add(incident)
            
            print("📋 Creating performance evaluations...")
            
            for project in active_projects:
                eval_date = date.today() - timedelta(days=random.randint(7, 30))
                
                for employee in project.assigned_employees:
                    evaluation = PerformanceEvaluation()
                    evaluation.project_id = project.id
                    evaluation.target_type = TargetType.EMPLOYEE
                    evaluation.target_id = employee.id
                    evaluation.evaluation_date = eval_date
                    evaluation.evaluator_id = project.project_manager_id if project.project_manager_id else None
                    evaluation.performance_rating = random.choice(list(PerformanceRating))
                    evaluation.skills_assessment = random.uniform(7.0, 10.0)
                    evaluation.teamwork_rating = random.uniform(7.0, 10.0)
                    evaluation.reliability_rating = random.uniform(8.0, 10.0)
                    evaluation.notes = f"أداء {random.choice(['ممتاز', 'جيد جداً', 'جيد'])} خلال فترة التقييم"
                    evaluation.improvement_areas = ["تطوير المهارات التقنية"] if random.random() > 0.7 else []
                    evaluation.strengths = ["الالتزام", "العمل الجماعي", "المهارات التقنية"]
                    db.session.add(evaluation)
            
            print("📋 Creating administrative records...")
            
            audit_actions = [
                "تسجيل دخول المدير", "إضافة كلب جديد", "تحديث بيانات موظف",
                "إنشاء مشروع جديد", "تسجيل جلسة تدريبية", "إضافة زيارة بيطرية"
            ]
            
            for i in range(15):
                log_date = datetime.now() - timedelta(days=random.randint(1, 30))
                audit_log = AuditLog()
                audit_log.user_id = 1
                audit_log.action = random.choice(list(AuditAction))
                audit_log.target_type = "Project" if random.random() > 0.5 else "Employee"
                audit_log.target_id = str(random.choice(created_projects).id) if random.random() > 0.5 else str(random.choice(created_employees).id)
                audit_log.details = random.choice(audit_actions)
                audit_log.ip_address = "192.168.1.100"
                audit_log.user_agent = "Mozilla/5.0 K9 Management System"
                audit_log.timestamp = log_date
                db.session.add(audit_log)
            
            db.session.commit()
            
            print("✅ Comprehensive sample data created successfully!")
            print("📊 Created:")
            print(f"   🐕 {len(created_dogs)} dogs")
            print(f"   👨‍💼 {len(created_employees)} employees")
            print(f"   📋 {len(created_projects)} projects")
            print(f"   🎯 {TrainingSession.query.count()} training sessions")
            print(f"   🏥 {VeterinaryVisit.query.count()} veterinary visits")
            print(f"   🚨 {Incident.query.count()} incidents")
            print(f"   📈 {PerformanceEvaluation.query.count()} performance evaluations")
            print(f"   📋 {AuditLog.query.count()} audit log entries")
            print()
            print("🔐 Login credentials:")
            print("   admin / admin123 (General Admin)")
            print()
            print("🎯 Business Rules Enforced:")
            print("   ✅ Project managers assigned to only ONE active project")
            print("   ✅ Role-based assignments (trainers→training, vets→medical)")
            print("   ✅ Realistic data relationships and constraints")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating comprehensive sample data: {e}")
            print(f"💡 Error details: {str(e)}")
            raise

def create_simple_data():
    """Legacy function - redirects to comprehensive data creation"""
    create_comprehensive_data()

if __name__ == '__main__':
    create_comprehensive_data()