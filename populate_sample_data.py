#!/usr/bin/env python3
"""
Populate K9 Operations Management System with comprehensive sample data
"""

import sys
sys.path.insert(0, '.')

from app import app, db
from k9.models.models import *
from k9.models.models_attendance_reporting import *
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
import random
import uuid

def populate_data():
    with app.app_context():
        print("🐕 Populating K9 Operations Management System with sample data...")
        
        # Clear existing data except admin user
        print("Clearing existing sample data...")
        admin_user = User.query.filter_by(username='admin').first()
        
        # Clear dependent tables first
        db.session.execute(db.text('DELETE FROM feeding_log'))
        db.session.execute(db.text('DELETE FROM daily_checkup_log'))
        db.session.execute(db.text('DELETE FROM excretion_log'))
        db.session.execute(db.text('DELETE FROM grooming_log'))
        db.session.execute(db.text('DELETE FROM cleaning_log'))
        db.session.execute(db.text('DELETE FROM training_session'))
        db.session.execute(db.text('DELETE FROM veterinary_visit'))
        db.session.execute(db.text('DELETE FROM heat_cycle'))
        db.session.execute(db.text('DELETE FROM mating_record'))
        db.session.execute(db.text('DELETE FROM pregnancy_record'))
        db.session.execute(db.text('DELETE FROM delivery_record'))
        db.session.execute(db.text('DELETE FROM puppy_record'))
        db.session.execute(db.text('DELETE FROM project_dog_assignment'))
        db.session.execute(db.text('DELETE FROM project_employee_assignment'))
        db.session.execute(db.text('DELETE FROM project_attendance'))
        db.session.execute(db.text('DELETE FROM project_shift_assignment'))
        db.session.execute(db.text('DELETE FROM project_shift'))
        db.session.execute(db.text('DELETE FROM attendance'))
        db.session.execute(db.text('DELETE FROM shift_assignment'))
        db.session.execute(db.text('DELETE FROM shift'))
        db.session.execute(db.text('DELETE FROM project'))
        db.session.execute(db.text('DELETE FROM dog'))
        db.session.execute(db.text('DELETE FROM employee'))
        db.session.execute(db.text("DELETE FROM \"user\" WHERE username != 'admin'"))
        
        db.session.commit()
        print("✓ Cleared existing sample data")
        
        # 1. Create additional users
        print("Creating additional users...")
        users_data = [
            ("pm1", "pm1@k9system.com", "Project Manager 1", "pm123", UserRole.PROJECT_MANAGER),
            ("pm2", "pm2@k9system.com", "Project Manager 2", "pm123", UserRole.PROJECT_MANAGER),
        ]
        
        users = {}
        for username, email, full_name, password, role in users_data:
            user = User()
            user.username = username
            user.email = email
            user.full_name = full_name
            user.password_hash = generate_password_hash(password)
            user.role = role
            user.active = True
            db.session.add(user)
            users[username] = user
        
        users['admin'] = admin_user
        db.session.commit()
        print(f"✓ Created {len(users_data)} additional users")
        
        # 2. Create employees
        print("Creating employees...")
        employees_data = [
            ("أحمد محمد", "EMP001", EmployeeRole.HANDLER, "01012345678", "ahmed@k9unit.gov", date(2020, 1, 15)),
            ("فاطمة علي", "EMP002", EmployeeRole.TRAINER, "01087654321", "fatma@k9unit.gov", date(2019, 6, 10)),
            ("محمود حسن", "EMP003", EmployeeRole.BREEDER, "01055512345", "mahmoud@k9unit.gov", date(2021, 3, 20)),
            ("دكتور سارة أحمد", "EMP004", EmployeeRole.VET, "01099887766", "sara@k9unit.gov", date(2018, 9, 5)),
            ("خالد عمر", "EMP005", EmployeeRole.HANDLER, "01033221100", "khaled@k9unit.gov", date(2022, 1, 8)),
            ("نورا إبراهيم", "EMP006", EmployeeRole.TRAINER, "01044556677", "nora@k9unit.gov", date(2020, 7, 12)),
            ("عبدالله محمد", "EMP007", EmployeeRole.BREEDER, "01066778899", "abdullah@k9unit.gov", date(2021, 11, 3)),
            ("دكتور حسام علي", "EMP008", EmployeeRole.VET, "01077889900", "hossam@k9unit.gov", date(2017, 4, 18)),
        ]
        
        employees = {}
        for name, emp_id, role, phone, email, hire_date in employees_data:
            employee = Employee()
            employee.name = name
            employee.employee_id = emp_id
            employee.role = role
            employee.phone = phone
            employee.email = email
            employee.hire_date = hire_date
            employee.is_active = True
            # Assign to project managers or admin
            if role in [EmployeeRole.HANDLER, EmployeeRole.TRAINER]:
                employee.assigned_to_user_id = users['pm1'].id
            elif role in [EmployeeRole.BREEDER, EmployeeRole.VET]:
                employee.assigned_to_user_id = users['pm2'].id
            db.session.add(employee)
            employees[emp_id] = employee
        
        db.session.commit()
        print(f"✓ Created {len(employees_data)} employees")
        
        # 3. Create dogs
        print("Creating dogs...")
        dogs_data = [
            ("ريكس", "DOG001", "جيرمان شيبرد", DogGender.MALE, date(2020, 3, 15), "بني وأسود", 35.5, 65.0),
            ("بيلا", "DOG002", "جيرمان شيبرد", DogGender.FEMALE, date(2019, 8, 22), "بني وأسود", 28.0, 58.0),
            ("ماكس", "DOG003", "مالينوا بلجيكي", DogGender.MALE, date(2021, 1, 10), "بني فاتح", 32.0, 62.0),
            ("لونا", "DOG004", "مالينوا بلجيكي", DogGender.FEMALE, date(2020, 11, 5), "بني فاتح", 25.5, 55.0),
            ("روكي", "DOG005", "روت وايلر", DogGender.MALE, date(2019, 5, 18), "أسود وبني", 45.0, 68.0),
            ("زيرا", "DOG006", "جيرمان شيبرد", DogGender.FEMALE, date(2021, 7, 3), "بني وأسود", 27.5, 57.0),
            ("أكسل", "DOG007", "دوبرمان", DogGender.MALE, date(2020, 9, 12), "أسود وبني", 38.0, 66.0),
            ("نوفا", "DOG008", "مالينوا بلجيكي", DogGender.FEMALE, date(2022, 2, 28), "بني فاتح", 24.0, 54.0),
            ("تايتان", "DOG009", "روت وايلر", DogGender.MALE, date(2018, 12, 8), "أسود وبني", 48.5, 70.0),
            ("أريا", "DOG010", "جيرمان شيبرد", DogGender.FEMALE, date(2021, 4, 20), "بني وأسود", 29.0, 59.0),
        ]
        
        dogs = {}
        for name, code, breed, gender, birth_date, color, weight, height in dogs_data:
            dog = Dog()
            dog.name = name
            dog.code = code
            dog.breed = breed
            dog.gender = gender
            dog.birth_date = birth_date
            dog.color = color
            dog.weight = weight
            dog.height = height
            dog.current_status = DogStatus.ACTIVE
            dog.location = random.choice(["القاعدة الرئيسية", "مركز التدريب", "القطاع الشمالي", "القطاع الجنوبي"])
            dog.specialization = random.choice(["كشف المتفجرات", "كشف المخدرات", "الحراسة", "التدريب العام"])
            # Assign to project managers
            if code in ["DOG001", "DOG002", "DOG003", "DOG004", "DOG005"]:
                dog.assigned_to_user_id = users['pm1'].id
            else:
                dog.assigned_to_user_id = users['pm2'].id
            db.session.add(dog)
            dogs[code] = dog
        
        db.session.commit()
        print(f"✓ Created {len(dogs_data)} dogs")
        
        # 4. Create projects
        print("Creating projects...")
        projects_data = [
            ("عملية الحدود الشمالية", "مشروع أمني لمراقبة الحدود الشمالية", ProjectStatus.ACTIVE, date(2024, 1, 1), date(2024, 12, 31)),
            ("تدريب الوحدة الخاصة", "برنامج تدريب متقدم للوحدة الخاصة", ProjectStatus.ACTIVE, date(2024, 3, 1), date(2024, 9, 30)),
            ("مهمة المطار الدولي", "تأمين المطار الدولي", ProjectStatus.COMPLETED, date(2023, 6, 1), date(2023, 12, 31)),
        ]
        
        projects = {}
        for i, (name, description, status, start_date, end_date) in enumerate(projects_data):
            project = Project()
            project.name = name
            project.description = description
            project.status = status
            project.start_date = start_date
            project.end_date = end_date
            # Assign project managers
            if i == 0:
                project.manager_id = users['pm1'].id
            else:
                project.manager_id = users['pm2'].id
            db.session.add(project)
            projects[i] = project
        
        db.session.commit()
        print(f"✓ Created {len(projects_data)} projects")
        
        # 5. Create training sessions
        print("Creating training sessions...")
        training_categories = [TrainingCategory.OBEDIENCE, TrainingCategory.DETECTION, TrainingCategory.AGILITY, TrainingCategory.ATTACK]
        
        for dog_code, dog in list(dogs.items())[:6]:  # First 6 dogs
            for i in range(5):  # 5 training sessions per dog
                training = TrainingSession()
                training.dog_id = dog.id
                training.trainer_id = random.choice([emp.id for emp in employees.values() if emp.role == EmployeeRole.TRAINER])
                training.category = random.choice(training_categories)
                training.date = date.today() - timedelta(days=random.randint(1, 90))
                training.duration_hours = random.uniform(1.0, 3.0)
                training.notes = f"جلسة تدريب {training.category.value} - أداء جيد"
                training.performance_score = random.randint(7, 10)
                db.session.add(training)
        
        db.session.commit()
        print("✓ Created training sessions")
        
        # 6. Create veterinary visits
        print("Creating veterinary visits...")
        visit_types = [VisitType.ROUTINE, VisitType.EMERGENCY, VisitType.VACCINATION]
        
        for dog_code, dog in dogs.items():
            for i in range(3):  # 3 vet visits per dog
                visit = VeterinaryVisit()
                visit.dog_id = dog.id
                visit.vet_id = random.choice([emp.id for emp in employees.values() if emp.role == EmployeeRole.VET])
                visit.visit_type = random.choice(visit_types)
                visit.visit_date = datetime.now() - timedelta(days=random.randint(1, 180))
                visit.weight = dog.weight + random.uniform(-2.0, 2.0)
                visit.temperature = random.uniform(38.0, 39.5)
                visit.heart_rate = random.randint(60, 120)
                visit.symptoms = random.choice(["فحص دوري", "تطعيم", "فحص أسنان", "فحص عام"])
                visit.diagnosis = "حالة صحية جيدة"
                visit.treatment = random.choice(["تطعيم", "فيتامينات", "لا يوجد", "علاج وقائي"])
                visit.cost = random.uniform(100.0, 500.0)
                db.session.add(visit)
        
        db.session.commit()
        print("✓ Created veterinary visits")
        
        # 7. Create heat cycles (breeding data)
        print("Creating heat cycles and breeding records...")
        female_dogs = [dog for dog in dogs.values() if dog.gender == DogGender.FEMALE]
        male_dogs = [dog for dog in dogs.values() if dog.gender == DogGender.MALE]
        
        for female_dog in female_dogs[:4]:  # First 4 female dogs
            # Create heat cycles
            for i in range(3):  # 3 heat cycles per female
                heat_cycle = HeatCycle()
                heat_cycle.female_id = female_dog.id
                heat_cycle.start_date = date.today() - timedelta(days=random.randint(30, 365))
                heat_cycle.end_date = heat_cycle.start_date + timedelta(days=random.randint(14, 21))
                heat_cycle.status = random.choice([HeatStatus.PROESTRUS, HeatStatus.ESTRUS, HeatStatus.DIESTRUS])
                heat_cycle.notes = f"دورة شبق طبيعية - {heat_cycle.status.value}"
                db.session.add(heat_cycle)
                
                # Create mating record for some heat cycles
                if random.choice([True, False]) and male_dogs:
                    mating = MatingRecord()
                    mating.female_id = female_dog.id
                    mating.male_id = random.choice(male_dogs).id
                    mating.mating_date = heat_cycle.start_date + timedelta(days=random.randint(5, 10))
                    mating.result = random.choice([MatingResult.SUCCESSFUL, MatingResult.UNSUCCESSFUL])
                    mating.notes = f"تزاوج {mating.result.value}"
                    db.session.add(mating)
                    
                    # Create pregnancy record if mating was successful
                    if mating.result == MatingResult.SUCCESSFUL and random.choice([True, False]):
                        pregnancy = PregnancyRecord()
                        pregnancy.female_id = female_dog.id
                        pregnancy.male_id = mating.male_id
                        pregnancy.mating_date = mating.mating_date
                        pregnancy.expected_delivery_date = mating.mating_date + timedelta(days=63)
                        pregnancy.status = random.choice([PregnancyStatus.CONFIRMED, PregnancyStatus.COMPLETED])
                        pregnancy.notes = "حمل مؤكد"
                        db.session.add(pregnancy)
                        
                        # Create delivery record if pregnancy completed
                        if pregnancy.status == PregnancyStatus.COMPLETED:
                            delivery = DeliveryRecord()
                            delivery.pregnancy_id = pregnancy.id
                            delivery.delivery_date = pregnancy.expected_delivery_date + timedelta(days=random.randint(-3, 3))
                            delivery.total_puppies = random.randint(3, 8)
                            delivery.alive_puppies = delivery.total_puppies - random.randint(0, 1)
                            delivery.stillborn_puppies = delivery.total_puppies - delivery.alive_puppies
                            delivery.complications = random.choice(["لا توجد", "ولادة طبيعية", "تدخل بيطري بسيط"])
                            db.session.add(delivery)
        
        db.session.commit()
        print("✓ Created heat cycles and breeding records")
        
        # 8. Create feeding logs
        print("Creating feeding logs...")
        for dog in list(dogs.values())[:6]:  # First 6 dogs
            for days_back in range(30):  # Last 30 days
                feeding_date = date.today() - timedelta(days=days_back)
                
                feeding = FeedingLog()
                feeding.dog_id = dog.id
                feeding.date = feeding_date
                feeding.feeder_id = random.choice([emp.id for emp in employees.values() if emp.role in [EmployeeRole.HANDLER, EmployeeRole.BREEDER]])
                feeding.food_type = random.choice(["علف جاف", "علف رطب", "علف مختلط"])
                feeding.amount_grams = random.randint(400, 800)
                feeding.meal_time = random.choice(["صباح", "ظهر", "مساء"])
                feeding.prep_method = random.choice([PrepMethod.DRY, PrepMethod.MIXED, PrepMethod.WET])
                feeding.body_condition_score = random.choice([BodyConditionScale.IDEAL, BodyConditionScale.SLIGHTLY_OVERWEIGHT, BodyConditionScale.SLIGHTLY_UNDERWEIGHT])
                feeding.notes = "وجبة عادية"
                db.session.add(feeding)
        
        db.session.commit()
        print("✓ Created feeding logs")
        
        # 9. Create daily checkup logs
        print("Creating daily checkup logs...")
        for dog in list(dogs.values())[:6]:  # First 6 dogs
            for days_back in range(14):  # Last 14 days
                checkup_date = date.today() - timedelta(days=days_back)
                
                checkup = DailyCheckupLog()
                checkup.dog_id = dog.id
                checkup.date = checkup_date
                checkup.checker_id = random.choice([emp.id for emp in employees.values() if emp.role in [EmployeeRole.HANDLER, EmployeeRole.VET]])
                checkup.general_health = "جيد"
                checkup.appetite = random.choice(["ممتاز", "جيد", "متوسط"])
                checkup.energy_level = random.choice(["عالي", "متوسط", "منخفض"])
                checkup.behavior_notes = "سلوك طبيعي"
                checkup.physical_condition = "حالة بدنية جيدة"
                checkup.notes = "فحص يومي - لا توجد مشاكل"
                db.session.add(checkup)
        
        db.session.commit()
        print("✓ Created daily checkup logs")
        
        # 10. Create excretion logs
        print("Creating excretion logs...")
        for dog in list(dogs.values())[:4]:  # First 4 dogs
            for days_back in range(7):  # Last 7 days
                excretion_date = date.today() - timedelta(days=days_back)
                
                excretion = ExcretionLog()
                excretion.dog_id = dog.id
                excretion.date = excretion_date
                excretion.recorder_id = random.choice([emp.id for emp in employees.values() if emp.role in [EmployeeRole.HANDLER, EmployeeRole.BREEDER]])
                excretion.stool_count = random.randint(2, 4)
                excretion.stool_color = random.choice([StoolColor.BROWN, StoolColor.DARK_BROWN])
                excretion.stool_consistency = random.choice([StoolConsistency.NORMAL, StoolConsistency.SOFT])
                excretion.urine_frequency = random.randint(4, 8)
                excretion.urine_color = random.choice([UrineColor.YELLOW, UrineColor.LIGHT_YELLOW])
                excretion.notes = "طبيعي"
                db.session.add(excretion)
        
        db.session.commit()
        print("✓ Created excretion logs")
        
        # 11. Create shifts and attendance
        print("Creating shifts and attendance records...")
        # Create shifts
        shifts_data = [
            ("الوردية الصباحية", "06:00", "14:00"),
            ("الوردية المسائية", "14:00", "22:00"),
            ("الوردية الليلية", "22:00", "06:00"),
        ]
        
        shifts = {}
        for name, start_time, end_time in shifts_data:
            shift = Shift()
            shift.name = name
            shift.start_time = datetime.strptime(start_time, "%H:%M").time()
            shift.end_time = datetime.strptime(end_time, "%H:%M").time()
            shift.is_active = True
            db.session.add(shift)
            shifts[name] = shift
        
        db.session.commit()
        
        # Create shift assignments
        for employee in list(employees.values())[:4]:  # First 4 employees
            assignment = ShiftAssignment()
            assignment.employee_id = employee.id
            assignment.shift_id = random.choice(list(shifts.values())).id
            assignment.assigned_date = date.today() - timedelta(days=random.randint(1, 30))
            assignment.is_active = True
            db.session.add(assignment)
        
        db.session.commit()
        
        # Create attendance records
        for employee in list(employees.values())[:4]:  # First 4 employees
            for days_back in range(14):  # Last 14 days
                attendance_date = date.today() - timedelta(days=days_back)
                
                attendance = Attendance()
                attendance.employee_id = employee.id
                attendance.date = attendance_date
                attendance.shift_id = random.choice(list(shifts.values())).id
                attendance.status = random.choice([AttendanceStatus.PRESENT, AttendanceStatus.ABSENT, AttendanceStatus.LATE])
                if attendance.status == AttendanceStatus.PRESENT:
                    attendance.time_in = datetime.combine(attendance_date, datetime.strptime("08:00", "%H:%M").time())
                    attendance.time_out = datetime.combine(attendance_date, datetime.strptime("16:00", "%H:%M").time())
                attendance.notes = "حضور عادي" if attendance.status == AttendanceStatus.PRESENT else "غياب"
                db.session.add(attendance)
        
        db.session.commit()
        print("✓ Created shifts and attendance records")
        
        print("\n🎉 Sample data population completed successfully!")
        print("\nSummary of created data:")
        print(f"- Users: {User.query.count()}")
        print(f"- Employees: {Employee.query.count()}")
        print(f"- Dogs: {Dog.query.count()}")
        print(f"- Projects: {Project.query.count()}")
        print(f"- Training sessions: {TrainingSession.query.count()}")
        print(f"- Veterinary visits: {VeterinaryVisit.query.count()}")
        print(f"- Heat cycles: {HeatCycle.query.count()}")
        print(f"- Mating records: {MatingRecord.query.count()}")
        print(f"- Pregnancy records: {PregnancyRecord.query.count()}")
        print(f"- Feeding logs: {FeedingLog.query.count()}")
        print(f"- Daily checkups: {DailyCheckupLog.query.count()}")
        print(f"- Excretion logs: {ExcretionLog.query.count()}")
        print(f"- Shifts: {Shift.query.count()}")
        print(f"- Attendance records: {Attendance.query.count()}")
        
        print("\n📊 You can now test all features including:")
        print("- Heat cycles and breeding management")
        print("- Comprehensive reporting")
        print("- Training and veterinary tracking")
        print("- Attendance management")
        print("- Daily care logs")

if __name__ == "__main__":
    populate_data()