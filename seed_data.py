#!/usr/bin/env python
"""
Interactive Data Seeding Script for K9 Operations Management System
This script provides an interactive menu to populate the database with realistic test data.
"""

import os
import sys
from datetime import datetime, date, timedelta, time
import random
from uuid import uuid4

from app import app, db
from k9.models.models import (
    User, Dog, Employee, TrainingSession, VeterinaryVisit, ProductionCycle,
    Project, Incident, PerformanceEvaluation, AttendanceRecord,
    DogMaturity, HeatCycle, MatingRecord, PregnancyRecord, DeliveryRecord, PuppyRecord,
    ProjectShift, ProjectShiftAssignment, ProjectAttendance,
    AttendanceDay, Shift, ShiftAssignment, Attendance,
    FeedingLog, DailyCheckupLog, ExcretionLog, GroomingLog, DewormingLog, CleaningLog,
    BreedingTrainingActivity, CaretakerDailyLog, BackupSettings,
    UserRole, EmployeeRole, DogStatus, DogGender, TrainingCategory,
    VisitType, ProductionCycleType, ProjectStatus,
    MaturityStatus, HeatStatus, MatingResult, PregnancyStatus, DeliveryStatus,
    BodyConditionScale, GroomingYesNo, GroomingCleanlinessScore
)
from k9.models.models_handler_daily import (
    DailySchedule, DailyScheduleItem, HandlerReport,
    HandlerReportHealth, HandlerReportTraining, HandlerReportCare,
    HandlerReportBehavior, HandlerReportIncident,
    Notification, Task,
    ScheduleStatus, ScheduleItemStatus, ReportStatus,
    HealthCheckStatus, TrainingType, BehaviorType, IncidentType,
    StoolColor, StoolShape, NotificationType, TaskStatus, TaskPriority
)
# Attendance reporting models removed - now using DailySchedule system
from werkzeug.security import generate_password_hash


ARABIC_MALE_NAMES = [
    "محمد", "أحمد", "علي", "حسن", "حسين", "عمر", "خالد", "سعيد", "فهد", "عبدالله",
    "عبدالرحمن", "يوسف", "إبراهيم", "سلمان", "طارق", "ماجد", "فيصل", "نواف", "بندر", "تركي"
]

ARABIC_SURNAMES = [
    "العتيبي", "الدوسري", "القحطاني", "الشمري", "الحربي", "العنزي", "الغامدي", "الزهراني",
    "السبيعي", "المطيري", "العمري", "الشهري", "اليامي", "البقمي", "الأحمدي"
]

DOG_NAMES = [
    "ريكس", "ماكس", "روكي", "بوليس", "تايسون", "زيوس", "أسد", "صقر", "نمر", "فهد",
    "ثور", "كينج", "برنس", "تشامب", "سبارتا", "أطلس", "رعد", "برق", "شهاب", "نجم"
]

PROJECT_NAMES = [
    "أمن المطار", "أمن الميناء", "دوريات الحدود", "فحص المتفجرات", "فحص المخدرات",
    "أمن الفعاليات", "دوريات المدينة", "أمن المنشآت", "فحص الأمتعة", "حراسة VIP"
]


class DataSeeder:
    def __init__(self):
        self.users = []
        self.employees = []
        self.dogs = []
        self.projects = []
        self.shifts = []
        self._ensure_enum_values()
    
    def _ensure_enum_values(self):
        """Ensure all required enum values exist in the database"""
        with app.app_context():
            try:
                result = db.session.execute(db.text(
                    "SELECT enumlabel FROM pg_enum WHERE enumtypid = "
                    "(SELECT oid FROM pg_type WHERE typname = 'userrole')"
                )).fetchall()
                
                existing_roles = [row[0] for row in result]
                
                if 'HANDLER' not in existing_roles:
                    print("⚠️  Adding missing HANDLER role to database enum...")
                    db.session.execute(db.text("ALTER TYPE userrole ADD VALUE 'HANDLER'"))
                    db.session.commit()
                    print("✅ HANDLER role added successfully")
            except Exception as e:
                print(f"⚠️  Warning: Could not check/add enum values: {e}")
        
    def clear_all_data(self):
        """Clear all data from database (use with caution!)"""
        print("\n⚠️  WARNING: This will delete ALL data from the database!")
        confirm = input("Type 'DELETE ALL' to confirm: ")
        if confirm != 'DELETE ALL':
            print("❌ Cancelled")
            return
        
        print("🗑️  Clearing all data...")
        with app.app_context():
            db.session.query(Notification).delete()
            db.session.query(Task).delete()
            db.session.query(HandlerReportIncident).delete()
            db.session.query(HandlerReportBehavior).delete()
            db.session.query(HandlerReportCare).delete()
            db.session.query(HandlerReportTraining).delete()
            db.session.query(HandlerReportHealth).delete()
            db.session.query(HandlerReport).delete()
            db.session.query(DailyScheduleItem).delete()
            db.session.query(DailySchedule).delete()
            # Legacy attendance reporting tables removed
            db.session.query(CaretakerDailyLog).delete()
            db.session.query(BreedingTrainingActivity).delete()
            db.session.query(CleaningLog).delete()
            db.session.query(DewormingLog).delete()
            db.session.query(GroomingLog).delete()
            db.session.query(ExcretionLog).delete()
            db.session.query(DailyCheckupLog).delete()
            db.session.query(FeedingLog).delete()
            db.session.query(Attendance).delete()
            db.session.query(ShiftAssignment).delete()
            db.session.query(Shift).delete()
            db.session.query(AttendanceDay).delete()
            db.session.query(ProjectAttendance).delete()
            db.session.query(ProjectShiftAssignment).delete()
            db.session.query(ProjectShift).delete()
            db.session.query(PuppyRecord).delete()
            db.session.query(DeliveryRecord).delete()
            db.session.query(PregnancyRecord).delete()
            db.session.query(MatingRecord).delete()
            db.session.query(HeatCycle).delete()
            db.session.query(DogMaturity).delete()
            db.session.query(AttendanceRecord).delete()
            db.session.query(PerformanceEvaluation).delete()
            db.session.query(Incident).delete()
            db.session.query(TrainingSession).delete()
            db.session.query(VeterinaryVisit).delete()
            db.session.query(ProductionCycle).delete()
            db.session.query(Project).delete()
            db.session.query(Dog).delete()
            db.session.query(Employee).delete()
            db.session.query(User).delete()
            db.session.query(BackupSettings).delete()
            db.session.commit()
        print("✅ All data cleared!")
    
    def seed_users(self, count=10):
        """Create users with different roles"""
        print(f"🔐 Creating {count} users...")
        created = 0
        with app.app_context():
            for i in range(count):
                if i == 0:
                    role = UserRole.GENERAL_ADMIN
                    username = "admin"
                    email = "admin@k9.local"
                elif i <= 3:
                    role = UserRole.PROJECT_MANAGER
                    username = f"pm_{i}"
                    email = f"pm{i}@k9.local"
                else:
                    role = UserRole.HANDLER
                    username = f"handler_{i}"
                    email = f"handler{i}@k9.local"
                
                existing = User.query.filter_by(username=username).first()
                if existing:
                    self.users.append(existing)
                    continue
                
                user = User(
                    id=uuid4(),
                    username=username,
                    email=email,
                    password_hash=generate_password_hash("password123"),
                    role=role,
                    is_active=True,
                    full_name=f"{random.choice(ARABIC_MALE_NAMES)} {random.choice(ARABIC_SURNAMES)}"
                )
                db.session.add(user)
                self.users.append(user)
                created += 1
            
            db.session.commit()
        print(f"✅ Created {created} users (skipped {count - created} existing)")
    
    def seed_employees(self, count=20):
        """Create employee records"""
        print(f"👥 Creating {count} employees...")
        created = 0
        with app.app_context():
            for i in range(count):
                emp_id = f"EMP{1000+i}"
                existing = Employee.query.filter_by(employee_id=emp_id).first()
                if existing:
                    self.employees.append(existing)
                    continue
                
                role = random.choice(list(EmployeeRole))
                employee = Employee(
                    id=uuid4(),
                    name=f"{random.choice(ARABIC_MALE_NAMES)} {random.choice(ARABIC_SURNAMES)}",
                    employee_id=emp_id,
                    role=role,
                    phone=f"+966 5{random.randint(10000000, 99999999)}",
                    email=f"emp{i}@k9.local",
                    hire_date=date.today() - timedelta(days=random.randint(30, 1000)),
                    is_active=True
                )
                db.session.add(employee)
                self.employees.append(employee)
                created += 1
            
            db.session.commit()
        print(f"✅ Created {created} employees (skipped {count - created} existing)")
    
    def seed_dogs(self, count=30):
        """Create dog records"""
        print(f"🐕 Creating {count} dogs...")
        created = 0
        with app.app_context():
            breeds = ["جيرمن شيبرد", "بلجيكي مالينو", "لابرادور", "روت وايلر", "دوبرمان"]
            for i in range(count):
                dog_code = f"K9-{1000+i}"
                existing = Dog.query.filter_by(code=dog_code).first()
                if existing:
                    self.dogs.append(existing)
                    continue
                
                dog = Dog(
                    id=uuid4(),
                    name=random.choice(DOG_NAMES),
                    code=dog_code,
                    breed=random.choice(breeds),
                    gender=random.choice(list(DogGender)),
                    birth_date=date.today() - timedelta(days=random.randint(365, 2555)),
                    current_status=random.choice(list(DogStatus)),
                    weight=random.uniform(25.0, 45.0),
                    height=random.uniform(55.0, 70.0),
                    color=random.choice(["أسود", "بني", "أسود وبني", "رمادي"]),
                    microchip_id=f"MC{random.randint(100000000, 999999999)}",
                    specialization=random.choice(['المخدرات', 'المتفجرات', 'الهجوم', 'البحث والإنقاذ'])
                )
                db.session.add(dog)
                self.dogs.append(dog)
                created += 1
            
            db.session.commit()
        print(f"✅ Created {created} dogs (skipped {count - created} existing)")
    
    def seed_projects(self, count=8):
        """Create project records"""
        print(f"📋 Creating {count} projects...")
        created = 0
        with app.app_context():
            if not self.users:
                self.users = User.query.all()
            
            managers = [u for u in self.users if u.role == UserRole.PROJECT_MANAGER]
            
            for i in range(count):
                project_code = f"PRJ-{1000+i}"
                existing = Project.query.filter_by(code=project_code).first()
                if existing:
                    self.projects.append(existing)
                    continue
                
                project = Project(
                    id=uuid4(),
                    name=PROJECT_NAMES[i % len(PROJECT_NAMES)],
                    code=project_code,
                    description=f"مشروع أمني لـ {PROJECT_NAMES[i % len(PROJECT_NAMES)]}",
                    status=random.choice(list(ProjectStatus)),
                    start_date=date.today() - timedelta(days=random.randint(30, 365)),
                    end_date=date.today() + timedelta(days=random.randint(30, 365)),
                    location=random.choice(["الرياض", "جدة", "الدمام", "مكة", "المدينة"]),
                    manager_id=random.choice(managers).id if managers else None
                )
                db.session.add(project)
                self.projects.append(project)
                created += 1
            
            db.session.commit()
        print(f"✅ Created {created} projects (skipped {count - created} existing)")
    
    def seed_training_sessions(self, count=50):
        """Create training session records"""
        print(f"🎯 Creating {count} training sessions...")
        with app.app_context():
            if not self.dogs:
                self.dogs = Dog.query.all()
            if not self.employees:
                self.employees = Employee.query.all()
            
            if not self.dogs or not self.employees:
                print("⚠️  Need dogs and employees first. Run seed_dogs and seed_employees.")
                return
            
            for i in range(count):
                session = TrainingSession(
                    id=uuid4(),
                    dog_id=random.choice(self.dogs).id,
                    trainer_id=random.choice(self.employees).id,
                    category=random.choice(list(TrainingCategory)),
                    subject=random.choice([
                        "تدريب الطاعة الأساسية",
                        "تدريب الكشف عن المتفجرات",
                        "تدريب الكشف عن المخدرات",
                        "تدريب الهجوم والحراسة",
                        "تدريب اللياقة البدنية"
                    ]),
                    session_date=datetime.now() - timedelta(days=random.randint(0, 90)),
                    duration=random.randint(30, 120),
                    success_rating=random.randint(6, 10),
                    location=random.choice(["مركز التدريب الرئيسي", "الميدان", "منطقة التدريب الخارجية"]),
                    notes=random.choice([
                        "أداء ممتاز في التدريب",
                        "يحتاج مزيد من التدريب",
                        "تقدم ملحوظ",
                        "أداء جيد"
                    ])
                )
                db.session.add(session)
            
            db.session.commit()
        print(f"✅ Created {count} training sessions")
    
    def seed_veterinary_visits(self, count=40):
        """Create veterinary visit records"""
        print(f"🏥 Creating {count} veterinary visits...")
        with app.app_context():
            if not self.dogs:
                self.dogs = Dog.query.all()
            if not self.employees:
                self.employees = Employee.query.all()
            
            if not self.dogs or not self.employees:
                print("⚠️  Need dogs and employees first. Run seed_dogs and seed_employees.")
                return
            
            vets = [e for e in self.employees if e.role == EmployeeRole.VET]
            if not vets:
                vets = self.employees[:3]
            
            for i in range(count):
                visit = VeterinaryVisit(
                    id=uuid4(),
                    dog_id=random.choice(self.dogs).id,
                    vet_id=random.choice(vets).id,
                    visit_type=random.choice(list(VisitType)),
                    visit_date=datetime.now() - timedelta(days=random.randint(0, 180)),
                    weight=random.uniform(25.0, 45.0),
                    temperature=random.uniform(37.5, 39.2),
                    diagnosis=random.choice([
                        "فحص دوري - سليم",
                        "تطعيم ضد الأمراض",
                        "فحص الأسنان",
                        "فحص عام - لا توجد مشاكل"
                    ]),
                    treatment=random.choice(["تطعيم", "فحص فقط", "علاج وقائي"]),
                    cost=random.uniform(100, 500),
                    location=random.choice(["العيادة البيطرية", "مركز الكلاب", "الميدان"]),
                    notes=random.choice(["الكلب بصحة جيدة", "يحتاج متابعة", "تطعيم سنوي"])
                )
                db.session.add(visit)
            
            db.session.commit()
        print(f"✅ Created {count} veterinary visits")
    
    def seed_breeding_operations(self, count=15):
        """Create breeding operation records (heat cycles, mating, pregnancy, delivery, puppies)"""
        print(f"🐾 Creating {count} breeding operations...")
        with app.app_context():
            if not self.dogs:
                self.dogs = Dog.query.all()
            
            female_dogs = [d for d in self.dogs if d.gender == DogGender.FEMALE]
            male_dogs = [d for d in self.dogs if d.gender == DogGender.MALE]
            
            if not female_dogs or not male_dogs:
                print("⚠️  Need both male and female dogs for breeding operations")
                return
            
            for i in range(min(count, len(female_dogs))):
                mother = female_dogs[i]
                father = random.choice(male_dogs)
                
                heat_cycle = HeatCycle(
                    id=uuid4(),
                    dog_id=mother.id,
                    start_date=date.today() - timedelta(days=random.randint(150, 300)),
                    end_date=date.today() - timedelta(days=random.randint(130, 280)),
                    status=HeatStatus.COMPLETED,
                    notes="دورة حرارة طبيعية"
                )
                db.session.add(heat_cycle)
                db.session.flush()
                
                mating = MatingRecord(
                    id=uuid4(),
                    mother_id=mother.id,
                    father_id=father.id,
                    mating_date=heat_cycle.start_date + timedelta(days=3),
                    result=MatingResult.SUCCESSFUL,
                    notes="تزاوج ناجح"
                )
                db.session.add(mating)
                db.session.flush()
                
                pregnancy = PregnancyRecord(
                    id=uuid4(),
                    dog_id=mother.id,
                    mating_record_id=mating.id,
                    start_date=mating.mating_date,
                    expected_delivery_date=mating.mating_date + timedelta(days=63),
                    status=PregnancyStatus.DELIVERED,
                    confirmed=True
                )
                db.session.add(pregnancy)
                db.session.flush()
                
                delivery = DeliveryRecord(
                    id=uuid4(),
                    pregnancy_record_id=pregnancy.id,
                    delivery_date=pregnancy.expected_delivery_date,
                    total_puppies=random.randint(4, 8),
                    alive_puppies=random.randint(3, 7),
                    status=DeliveryStatus.COMPLETED,
                    notes="ولادة ناجحة"
                )
                db.session.add(delivery)
                db.session.flush()
                
                for j in range(delivery.live_births):
                    puppy = PuppyRecord(
                        id=uuid4(),
                        delivery_record_id=delivery.id,
                        name=f"{random.choice(DOG_NAMES)}-{j+1}",
                        gender=random.choice(list(DogGender)),
                        birth_weight=random.uniform(0.3, 0.6),
                        current_weight=random.uniform(8.0, 15.0),
                        is_alive=True,
                        notes="جرو صحي"
                    )
                    db.session.add(puppy)
            
            db.session.commit()
        print(f"✅ Created breeding operation records")
    
    def seed_shifts(self, count=4):
        """Create shift records"""
        print(f"⏰ Creating {count} shifts...")
        with app.app_context():
            shift_times = [
                ("الصباحية", time(6, 0), time(14, 0)),
                ("المسائية", time(14, 0), time(22, 0)),
                ("الليلية", time(22, 0), time(6, 0)),
                ("الكاملة", time(8, 0), time(16, 0))
            ]
            
            for i in range(min(count, len(shift_times))):
                name, start, end = shift_times[i]
                shift = Shift(
                    id=uuid4(),
                    name=name,
                    start_time=start,
                    end_time=end,
                    description=f"فترة {name}"
                )
                db.session.add(shift)
                self.shifts.append(shift)
            
            db.session.commit()
        print(f"✅ Created {count} shifts")
    
    def seed_daily_schedules(self, count=10):
        """Create daily schedules with items"""
        print(f"📅 Creating {count} daily schedules...")
        with app.app_context():
            if not self.projects:
                self.projects = Project.query.all()
            if not self.users:
                self.users = User.query.all()
            if not self.dogs:
                self.dogs = Dog.query.all()
            if not self.shifts:
                self.shifts = Shift.query.all()
            
            handlers = [u for u in self.users if u.role == UserRole.HANDLER]
            
            for i in range(count):
                schedule_date = date.today() - timedelta(days=count - i - 1)
                schedule = DailySchedule(
                    id=uuid4(),
                    date=schedule_date,
                    project_id=random.choice(self.projects).id if self.projects else None,
                    status=ScheduleStatus.LOCKED if i < count - 2 else ScheduleStatus.OPEN,
                    notes=f"جدول يوم {schedule_date}"
                )
                db.session.add(schedule)
                db.session.flush()
                
                for j in range(random.randint(3, 8)):
                    item = DailyScheduleItem(
                        id=uuid4(),
                        daily_schedule_id=schedule.id,
                        handler_user_id=random.choice(handlers).id if handlers else self.users[0].id,
                        dog_id=random.choice(self.dogs).id if self.dogs else None,
                        shift_id=random.choice(self.shifts).id if self.shifts else None,
                        status=random.choice(list(ScheduleItemStatus))
                    )
                    db.session.add(item)
            
            db.session.commit()
        print(f"✅ Created {count} daily schedules")
    
    def seed_handler_reports(self, count=20):
        """Create handler reports with all sections"""
        print(f"📝 Creating {count} handler reports...")
        with app.app_context():
            if not self.users:
                self.users = User.query.all()
            if not self.dogs:
                self.dogs = Dog.query.all()
            if not self.projects:
                self.projects = Project.query.all()
            
            handlers = [u for u in self.users if u.role == UserRole.HANDLER]
            
            for i in range(count):
                report_date = date.today() - timedelta(days=random.randint(0, 30))
                report = HandlerReport(
                    id=uuid4(),
                    date=report_date,
                    handler_user_id=random.choice(handlers).id if handlers else self.users[0].id,
                    dog_id=random.choice(self.dogs).id,
                    project_id=random.choice(self.projects).id if self.projects else None,
                    location=random.choice(["الموقع الرئيسي", "الميدان", "مركز التدريب"]),
                    status=random.choice(list(ReportStatus))
                )
                db.session.add(report)
                db.session.flush()
                
                health = HandlerReportHealth(
                    id=uuid4(),
                    handler_report_id=report.id,
                    general_health=random.choice(list(HealthCheckStatus)),
                    appetite=random.choice(["طبيعي", "جيد", "ممتاز"]),
                    energy_level=random.choice(["طبيعي", "نشيط", "متوسط"]),
                    temperature=random.uniform(37.5, 39.0),
                    notes="الكلب بصحة جيدة"
                )
                db.session.add(health)
                
                training = HandlerReportTraining(
                    id=uuid4(),
                    handler_report_id=report.id,
                    training_type=random.choice(list(TrainingType)),
                    duration_minutes=random.randint(30, 90),
                    performance=random.choice(["ممتاز", "جيد", "متوسط"]),
                    notes="تدريب منتظم"
                )
                db.session.add(training)
                
                care = HandlerReportCare(
                    id=uuid4(),
                    handler_report_id=report.id,
                    feeding_time=time(8, 0),
                    food_amount=random.uniform(0.5, 2.0),
                    water_intake=random.choice(["طبيعي", "جيد"]),
                    grooming_done=random.choice([True, False]),
                    exercise_duration=random.randint(20, 60)
                )
                db.session.add(care)
                
                behavior = HandlerReportBehavior(
                    id=uuid4(),
                    handler_report_id=report.id,
                    behavior_type=random.choice(list(BehaviorType)),
                    description=random.choice(["سلوك طبيعي", "متعاون", "هادئ"]),
                    notes="لا ملاحظات"
                )
                db.session.add(behavior)
            
            db.session.commit()
        print(f"✅ Created {count} handler reports")
    
    def seed_caretaker_logs(self, count=30):
        """Create caretaker daily logs (feeding, grooming, excretion, etc.)"""
        print(f"📊 Creating {count} caretaker logs...")
        with app.app_context():
            if not self.dogs:
                self.dogs = Dog.query.all()
            if not self.employees:
                self.employees = Employee.query.all()
            
            for i in range(count):
                log_date = date.today() - timedelta(days=random.randint(0, 30))
                
                feeding = FeedingLog(
                    id=uuid4(),
                    dog_id=random.choice(self.dogs).id,
                    date=log_date,
                    time=time(random.randint(7, 9), random.randint(0, 59)),
                    food_type=random.choice(["دراي فود", "طعام معلب", "طعام طازج"]),
                    amount=random.uniform(0.5, 2.0),
                    notes="وجبة منتظمة - كمية بالكيلوجرام"
                )
                db.session.add(feeding)
                
                checkup = DailyCheckupLog(
                    id=uuid4(),
                    dog_id=random.choice(self.dogs).id,
                    date=log_date,
                    time=time(random.randint(8, 10), 0),
                    body_condition=random.choice(list(BodyConditionScale)),
                    temperature=random.uniform(37.5, 39.0),
                    notes="فحص يومي طبيعي"
                )
                db.session.add(checkup)
                
                grooming = GroomingLog(
                    id=uuid4(),
                    dog_id=random.choice(self.dogs).id,
                    date=log_date,
                    bath_given=random.choice(list(GroomingYesNo)),
                    nail_trim=random.choice(list(GroomingYesNo)),
                    ear_clean=random.choice(list(GroomingYesNo)),
                    brush=random.choice(list(GroomingYesNo)),
                    cleanliness_score=random.choice(list(GroomingCleanlinessScore)),
                    notes="نظافة منتظمة"
                )
                db.session.add(grooming)
            
            db.session.commit()
        print(f"✅ Created {count} caretaker logs")
    
    def seed_tasks_notifications(self, count=15):
        """Create tasks and notifications"""
        print(f"🔔 Creating {count} tasks and notifications...")
        with app.app_context():
            if not self.users:
                self.users = User.query.all()
            if not self.projects:
                self.projects = Project.query.all()
            
            for i in range(count):
                task = Task(
                    id=uuid4(),
                    title=random.choice([
                        "فحص الكلاب البوليسية",
                        "تنظيف الحظائر",
                        "تحديث السجلات",
                        "إعداد التقرير الشهري",
                        "فحص المعدات"
                    ]),
                    description=f"مهمة رقم {i+1}",
                    priority=random.choice(list(TaskPriority)),
                    status=random.choice(list(TaskStatus)),
                    assigned_to_user_id=random.choice(self.users).id,
                    created_by_user_id=self.users[0].id,
                    project_id=random.choice(self.projects).id if self.projects and random.random() > 0.5 else None,
                    due_date=datetime.now() + timedelta(days=random.randint(1, 30))
                )
                db.session.add(task)
                
                notification = Notification(
                    id=uuid4(),
                    user_id=random.choice(self.users).id,
                    type=random.choice(list(NotificationType)),
                    title="إشعار جديد",
                    message=f"لديك إشعار بخصوص {task.title}",
                    read=random.choice([True, False])
                )
                db.session.add(notification)
            
            db.session.commit()
        print(f"✅ Created {count} tasks and notifications")
    
    def seed_backup_settings(self):
        """Create backup settings record"""
        print("💾 Creating backup settings...")
        with app.app_context():
            if BackupSettings.query.first():
                print("⚠️  Backup settings already exist")
                return
            
            settings = BackupSettings(
                id=uuid4(),
                auto_backup_enabled=True,
                backup_frequency="DAILY",
                backup_hour=2,
                retention_days=30,
                google_drive_enabled=False
            )
            db.session.add(settings)
            db.session.commit()
        print("✅ Created backup settings")
    
    def seed_all(self):
        """Seed all models with default counts"""
        print("\n🌱 Seeding all models with realistic data...\n")
        self.seed_users(15)
        self.seed_employees(25)
        self.seed_dogs(40)
        self.seed_projects(10)
        self.seed_training_sessions(60)
        self.seed_veterinary_visits(50)
        self.seed_breeding_operations(12)
        self.seed_shifts(4)
        self.seed_daily_schedules(15)
        self.seed_handler_reports(30)
        self.seed_caretaker_logs(40)
        self.seed_tasks_notifications(20)
        self.seed_backup_settings()
        print("\n🎉 All data seeded successfully!\n")


def show_menu():
    """Display interactive menu"""
    print("\n" + "="*60)
    print("🐕 K9 Operations - Interactive Data Seeding Tool")
    print("="*60)
    print("\n📋 Select what to seed:")
    print("\n Core Entities:")
    print("  1. Users (Admin, Project Managers, Handlers)")
    print("  2. Employees (Trainers, Vets, Breeders, etc.)")
    print("  3. Dogs (K9 Units)")
    print("  4. Projects (Security Operations)")
    print("\n Operations:")
    print("  5. Training Sessions")
    print("  6. Veterinary Visits")
    print("  7. Breeding Operations (Heat/Mating/Pregnancy/Puppies)")
    print("  8. Shifts")
    print("\n Daily Management:")
    print("  9. Daily Schedules (with assignments)")
    print(" 10. Handler Reports (with health/training/care sections)")
    print(" 11. Caretaker Logs (feeding/grooming/checkup)")
    print(" 12. Tasks & Notifications")
    print("\n System:")
    print(" 13. Backup Settings")
    print("\n Special Options:")
    print(" 99. Seed ALL models (recommended for first run)")
    print("  0. Exit")
    print("\n⚠️  Danger Zone:")
    print(" -1. Clear ALL data from database")
    print("\n" + "="*60)


def main():
    """Main interactive loop"""
    seeder = DataSeeder()
    
    while True:
        show_menu()
        try:
            choice = input("\n👉 Enter your choice: ").strip()
            
            if choice == '0':
                print("\n👋 Goodbye!\n")
                break
            
            elif choice == '-1':
                seeder.clear_all_data()
            
            elif choice == '99':
                seeder.seed_all()
            
            elif choice == '1':
                count = int(input("How many users? [10]: ") or 10)
                seeder.seed_users(count)
            
            elif choice == '2':
                count = int(input("How many employees? [20]: ") or 20)
                seeder.seed_employees(count)
            
            elif choice == '3':
                count = int(input("How many dogs? [30]: ") or 30)
                seeder.seed_dogs(count)
            
            elif choice == '4':
                count = int(input("How many projects? [8]: ") or 8)
                seeder.seed_projects(count)
            
            elif choice == '5':
                count = int(input("How many training sessions? [50]: ") or 50)
                seeder.seed_training_sessions(count)
            
            elif choice == '6':
                count = int(input("How many veterinary visits? [40]: ") or 40)
                seeder.seed_veterinary_visits(count)
            
            elif choice == '7':
                count = int(input("How many breeding operations? [15]: ") or 15)
                seeder.seed_breeding_operations(count)
            
            elif choice == '8':
                count = int(input("How many shifts? [4]: ") or 4)
                seeder.seed_shifts(count)
            
            elif choice == '9':
                count = int(input("How many daily schedules? [10]: ") or 10)
                seeder.seed_daily_schedules(count)
            
            elif choice == '10':
                count = int(input("How many handler reports? [20]: ") or 20)
                seeder.seed_handler_reports(count)
            
            elif choice == '11':
                count = int(input("How many caretaker logs? [30]: ") or 30)
                seeder.seed_caretaker_logs(count)
            
            elif choice == '12':
                count = int(input("How many tasks/notifications? [15]: ") or 15)
                seeder.seed_tasks_notifications(count)
            
            elif choice == '13':
                seeder.seed_backup_settings()
            
            else:
                print("❌ Invalid choice. Please try again.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
