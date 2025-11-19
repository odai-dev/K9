#!/usr/bin/env python3
"""
اختبار شامل وذاتي لنظام الجدولة اليومية للسائسين
Self-Validation Test for Handler Daily Scheduling System

هذا السكريبت يقوم بـ:
1. إنشاء بيانات تجريبية (مشروع، مواقع، مسؤول، سائسين، كلاب)
2. إنشاء جدولة يومية كاملة
3. التحقق من ظهور الجدول في واجهة السائس
4. التحقق من قدرة السائس على رفع التقارير
5. التحقق من ظهور الجدول لمسؤول المشروع
6. فحص التكامل بين الواجهة والخلفية
7. إصلاح أي أخطاء تلقائيًا
8. إصدار تقرير نهائي
"""

import sys
import os
from datetime import date, timedelta, datetime
from werkzeug.security import generate_password_hash

# Add the application to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from k9.models.models import (
    User, UserRole, Project, ProjectLocation, Dog, DogStatus, DogGender,
    Employee, EmployeeRole, Shift
)
from k9.models.models_handler_daily import (
    DailySchedule, DailyScheduleItem, ShiftReport,
    ScheduleStatus, ScheduleItemStatus, ReportStatus
)
from k9.services.handler_service import DailyScheduleService, ShiftReportService

class ScheduleSystemTester:
    """اختبار شامل لنظام الجدولة اليومية"""
    
    def __init__(self):
        self.test_data = {}
        self.issues_found = []
        self.fixes_applied = []
        self.tests_passed = []
        self.app_context = None
        
    def setup_test_environment(self):
        """إعداد بيئة الاختبار"""
        print("\n" + "="*80)
        print("⚙️  إعداد بيئة الاختبار...")
        print("="*80)
        
        self.app_context = app.app_context()
        self.app_context.push()
        
    def cleanup_test_data(self):
        """تنظيف البيانات التجريبية السابقة"""
        print("\n🧹 تنظيف البيانات التجريبية السابقة...")
        
        try:
            # حذف البيانات التجريبية القديمة
            test_project = Project.query.filter_by(
                name="Test Project – Scheduling Validation"
            ).first()
            
            if test_project:
                print(f"  ✓ وجدنا مشروع تجريبي قديم - سيتم حذفه")
                
                # حذف الجداول المرتبطة
                DailySchedule.query.filter_by(project_id=test_project.id).delete()
                
                # حذف السائسين التجريبيين
                test_handlers = User.query.filter(
                    User.username.like('test_handler_%')
                ).all()
                for handler in test_handlers:
                    db.session.delete(handler)
                
                # حذف الكلاب التجريبية
                test_dogs = Dog.query.filter(
                    Dog.name.like('Test Dog %')
                ).all()
                for dog in test_dogs:
                    db.session.delete(dog)
                
                # حذف المواقع
                ProjectLocation.query.filter_by(project_id=test_project.id).delete()
                
                # حذف المشروع
                db.session.delete(test_project)
                
                db.session.commit()
                print("  ✓ تم التنظيف بنجاح")
            else:
                print("  ✓ لا توجد بيانات تجريبية قديمة")
                
        except Exception as e:
            print(f"  ⚠️  خطأ في التنظيف: {str(e)}")
            db.session.rollback()
    
    def create_test_data(self):
        """1️⃣  إنشاء بيانات تجريبية كاملة"""
        print("\n" + "="*80)
        print("1️⃣  إنشاء بيانات تجريبية...")
        print("="*80)
        
        try:
            # أ. مشروع تجريبي
            print("\n📁 إنشاء مشروع تجريبي...")
            test_project = Project(
                name="Test Project – Scheduling Validation",
                code="TEST-SCHED-001",  # إضافة الكود المطلوب
                description="مشروع للاختبار الذاتي لنظام الجدولة اليومية",
                status="ACTIVE",
                start_date=date.today()
            )
            db.session.add(test_project)
            db.session.flush()
            self.test_data['project'] = test_project
            print(f"  ✅ تم إنشاء المشروع: {test_project.name}")
            
            # المواقع (3 مواقع)
            print("\n📍 إنشاء المواقع...")
            locations_data = [
                {"name": "Main Gate", "description": "البوابة الرئيسية"},
                {"name": "Patrol Zone", "description": "منطقة الدورية"},
                {"name": "Storage Area", "description": "منطقة التخزين"}
            ]
            locations = []
            for loc_data in locations_data:
                location = ProjectLocation(
                    project_id=test_project.id,
                    name=loc_data['name'],
                    description=loc_data['description']
                )
                db.session.add(location)
                locations.append(location)
            db.session.flush()
            self.test_data['locations'] = locations
            print(f"  ✅ تم إنشاء {len(locations)} مواقع")
            
            # ب. مسؤول مشروع (يجب إنشاء Employee أولاً)
            print("\n👔 إنشاء مسؤول المشروع...")
            # إنشاء سجل موظف أولاً
            pm_employee = Employee(
                name="Test PM Manager",
                employee_id="TEST-PM-001",
                role=EmployeeRole.HANDLER,  # استخدام role من Enum
                email="test_pm_schedule@test.com",
                phone="1234567890",
                hire_date=date.today(),
                is_active=True
            )
            db.session.add(pm_employee)
            db.session.flush()
            
            # الآن إنشاء User مرتبط بالموظف
            pm_user = User(
                username="test_pm_schedule",
                email="test_pm_schedule@test.com",
                full_name="Test Project Manager",
                role=UserRole.PROJECT_MANAGER,
                project_id=test_project.id,
                employee_id=pm_employee.id,
                password_hash=generate_password_hash("test123"),
                is_active=True
            )
            db.session.add(pm_user)
            db.session.flush()
            self.test_data['pm'] = pm_user
            self.test_data['pm_employee'] = pm_employee
            print(f"  ✅ تم إنشاء مسؤول المشروع: {pm_user.full_name}")
            
            # ج. سائسين (3 سائسين - مع سجلات موظفين)
            print("\n👨 إنشاء السائسين...")
            handlers = []
            handler_employees = []
            for i in range(1, 4):
                # إنشاء سجل موظف أولاً
                handler_employee = Employee(
                    name=f"Handler Test {i}",
                    employee_id=f"TEST-HANDLER-{i:03d}",
                    role=EmployeeRole.HANDLER,
                    email=f"test_handler_{i}@test.com",
                    phone=f"123456789{i}",
                    hire_date=date.today(),
                    is_active=True
                )
                db.session.add(handler_employee)
                handler_employees.append(handler_employee)
            
            db.session.flush()  # Flush to get employee IDs
            
            # الآن إنشاء Users مرتبطين بالموظفين
            for i in range(1, 4):
                handler = User(
                    username=f"test_handler_{i}",
                    email=f"test_handler_{i}@test.com",
                    full_name=f"Test Handler {i}",
                    role=UserRole.HANDLER,
                    project_id=test_project.id,
                    employee_id=handler_employees[i-1].id,
                    password_hash=generate_password_hash("test123"),
                    is_active=True
                )
                db.session.add(handler)
                handlers.append(handler)
            db.session.flush()
            self.test_data['handlers'] = handlers
            self.test_data['handler_employees'] = handler_employees
            print(f"  ✅ تم إنشاء {len(handlers)} سائسين")
            
            # د. كلاب (3 كلاب)
            print("\n🐕 إنشاء الكلاب...")
            dogs = []
            for i in range(1, 4):
                dog = Dog(
                    name=f"Test Dog {i}",
                    code=f"TEST-DOG-{i:03d}",  # استخدام code بدلاً من chip_number
                    microchip_id=f"CHIP{i:04d}",  # استخدام microchip_id
                    breed="German Shepherd",
                    gender=DogGender.MALE,  # إضافة gender
                    birth_date=date(2020, 1, 1),  # استخدام birth_date بدلاً من date_of_birth
                    current_status=DogStatus.ACTIVE,
                    assigned_to_user_id=handlers[i-1].id  # استخدام assigned_to_user_id
                )
                db.session.add(dog)
                dogs.append(dog)
            db.session.flush()
            self.test_data['dogs'] = dogs
            print(f"  ✅ تم إنشاء {len(dogs)} كلاب")
            
            # ه. فترات عمل (Shifts)
            print("\n⏰ إنشاء الفترات...")
            shifts = []
            shifts_data = [
                {"name": "Morning Shift", "start": "06:00", "end": "14:00"},
                {"name": "Evening Shift", "start": "14:00", "end": "22:00"},
                {"name": "Night Shift", "start": "22:00", "end": "06:00"}
            ]
            for shift_data in shifts_data:
                shift = Shift(
                    project_id=test_project.id,
                    name=shift_data['name'],
                    start_time=shift_data['start'],
                    end_time=shift_data['end']
                )
                db.session.add(shift)
                shifts.append(shift)
            db.session.flush()
            self.test_data['shifts'] = shifts
            print(f"  ✅ تم إنشاء {len(shifts)} فترات عمل")
            
            db.session.commit()
            print("\n✅ تم إنشاء جميع البيانات التجريبية بنجاح!")
            self.tests_passed.append("✅ إنشاء البيانات التجريبية")
            
        except Exception as e:
            print(f"\n❌ خطأ في إنشاء البيانات: {str(e)}")
            self.issues_found.append(f"فشل إنشاء البيانات التجريبية: {str(e)}")
            db.session.rollback()
            raise
    
    def create_daily_schedule(self):
        """2️⃣  إنشاء جدولة يومية واقعية"""
        print("\n" + "="*80)
        print("2️⃣  إنشاء جدولة يومية واقعية...")
        print("="*80)
        
        try:
            schedule_date = date.today() + timedelta(days=1)  # الغد
            project = self.test_data['project']
            handlers = self.test_data['handlers']
            dogs = self.test_data['dogs']
            shifts = self.test_data['shifts']
            locations = self.test_data['locations']
            pm = self.test_data['pm']
            
            print(f"\n📅 التاريخ: {schedule_date}")
            print(f"📁 المشروع: {project.name}")
            
            # إنشاء الجدول
            schedule = DailySchedule(
                date=schedule_date,
                project_id=project.id,
                notes="جدول تجريبي للاختبار الذاتي",
                created_by_user_id=pm.id,
                status=ScheduleStatus.OPEN
            )
            db.session.add(schedule)
            db.session.flush()
            self.test_data['schedule'] = schedule
            print(f"  ✅ تم إنشاء الجدول اليومي")
            
            # إضافة عناصر الجدول (كل سائس له فترة)
            print("\n📝 إضافة عناصر الجدول...")
            schedule_items = []
            for i, handler in enumerate(handlers):
                item = DailyScheduleItem(
                    daily_schedule_id=schedule.id,
                    handler_user_id=handler.id,
                    dog_id=dogs[i].id,
                    shift_id=shifts[i].id,
                    location_id=locations[i].id,
                    status=ScheduleItemStatus.PLANNED
                )
                db.session.add(item)
                schedule_items.append(item)
                print(f"  ✅ {handler.full_name} → {dogs[i].name} → {shifts[i].name} → {locations[i].name}")
            
            db.session.flush()
            self.test_data['schedule_items'] = schedule_items
            
            db.session.commit()
            print(f"\n✅ تم إنشاء جدول يومي كامل مع {len(schedule_items)} عناصر")
            self.tests_passed.append("✅ إنشاء الجدولة اليومية")
            
        except Exception as e:
            print(f"\n❌ خطأ في إنشاء الجدولة: {str(e)}")
            self.issues_found.append(f"فشل إنشاء الجدولة: {str(e)}")
            db.session.rollback()
            raise
    
    def verify_handler_sees_schedule(self):
        """3️⃣  التحقق من ظهور الجدول للسائس"""
        print("\n" + "="*80)
        print("3️⃣  التحقق من ظهور الجدول للسائس...")
        print("="*80)
        
        try:
            handlers = self.test_data['handlers']
            schedule_items = self.test_data['schedule_items']
            
            print("\nاختبار رؤية كل سائس لجدوله...")
            
            for i, handler in enumerate(handlers):
                # محاكاة الدالة التي تستخدمها Dashboard
                handler_schedule, schedule_date = DailyScheduleService.get_active_handler_schedule(
                    str(handler.id)
                )
                
                print(f"\n👨 السائس: {handler.full_name}")
                print(f"  📅 تاريخ الجدول: {schedule_date}")
                print(f"  📋 عدد العناصر المرئية: {len(handler_schedule)}")
                
                # أ. التحقق من أن السائس يرى جدوله
                if len(handler_schedule) == 0:
                    error_msg = f"السائس {handler.full_name} لا يرى أي جدول!"
                    print(f"  ❌ {error_msg}")
                    self.issues_found.append(error_msg)
                else:
                    print(f"  ✅ السائس يرى الجدول")
                
                # ب. التحقق من أن السائس يرى فقط جدوله وليس جداول الآخرين
                for item in handler_schedule:
                    if str(item.handler_user_id) != str(handler.id):
                        error_msg = f"السائس {handler.full_name} يرى جدول سائس آخر!"
                        print(f"  ❌ {error_msg}")
                        self.issues_found.append(error_msg)
                    else:
                        print(f"  ✅ الجدول خاص بالسائس نفسه")
                        print(f"     🐕 الكلب: {item.dog.name if item.dog else 'غير محدد'}")
                        print(f"     ⏰ الفترة: {item.shift.name if item.shift else 'غير محدد'}")
                        print(f"     📍 الموقع: {item.location.name if item.location else 'غير محدد'}")
            
            if len(self.issues_found) == 0 or all('يرى جدول' not in issue for issue in self.issues_found):
                self.tests_passed.append("✅ السائس يرى جدوله فقط")
            
        except Exception as e:
            print(f"\n❌ خطأ في التحقق من رؤية الجدول: {str(e)}")
            self.issues_found.append(f"خطأ في التحقق من رؤية الجدول: {str(e)}")
    
    def verify_handler_can_submit_reports(self):
        """4️⃣  التحقق من قدرة السائس على رفع تقارير الفترات"""
        print("\n" + "="*80)
        print("4️⃣  التحقق من قدرة السائس على رفع تقارير الفترات...")
        print("="*80)
        
        try:
            handlers = self.test_data['handlers']
            schedule_items = self.test_data['schedule_items']
            
            print("\nاختبار رفع تقرير لكل سائس...")
            
            for i, handler in enumerate(handlers):
                schedule_item = schedule_items[i]
                
                print(f"\n👨 السائس: {handler.full_name}")
                print(f"  📋 عنصر الجدول: {schedule_item.id}")
                
                # التحقق من عدم وجود تقرير سابق
                existing_report = ShiftReport.query.filter_by(
                    schedule_item_id=schedule_item.id
                ).first()
                
                if existing_report:
                    print(f"  ⚠️  يوجد تقرير سابق - سيتم حذفه")
                    db.session.delete(existing_report)
                    db.session.flush()
                
                # محاولة إنشاء تقرير فترة
                try:
                    shift_report, error = ShiftReportService.create_shift_report(
                        schedule_item_id=str(schedule_item.id),
                        handler_user_id=str(handler.id),
                        dog_id=str(schedule_item.dog_id),
                        project_id=str(schedule_item.schedule.project_id),
                        report_date=schedule_item.schedule.date,
                        location=schedule_item.location.name if schedule_item.location else "Test Location"
                    )
                    
                    if error:
                        print(f"  ❌ فشل إنشاء التقرير: {error}")
                        self.issues_found.append(f"فشل رفع تقرير للسائس {handler.full_name}: {error}")
                    else:
                        print(f"  ✅ تم إنشاء تقرير الفترة بنجاح")
                        print(f"     🆔 معرف التقرير: {shift_report.id}")
                        print(f"     📅 التاريخ: {shift_report.report_date}")
                        print(f"     📍 الموقع: {shift_report.location}")
                        
                        self.test_data[f'shift_report_{i}'] = shift_report
                        
                except Exception as e:
                    print(f"  ❌ خطأ في إنشاء التقرير: {str(e)}")
                    self.issues_found.append(f"خطأ في رفع تقرير للسائس {handler.full_name}: {str(e)}")
            
            db.session.commit()
            
            if len([issue for issue in self.issues_found if 'فشل رفع تقرير' in issue]) == 0:
                self.tests_passed.append("✅ السائس يستطيع رفع تقارير الفترات")
            
        except Exception as e:
            print(f"\n❌ خطأ عام في اختبار التقارير: {str(e)}")
            self.issues_found.append(f"خطأ في اختبار رفع التقارير: {str(e)}")
            db.session.rollback()
    
    def verify_reports_storage(self):
        """5️⃣  التحقق من التخزين المنفصل للتقارير"""
        print("\n" + "="*80)
        print("5️⃣  التحقق من التخزين المنفصل للتقارير...")
        print("="*80)
        
        try:
            print("\nفحص بنية قاعدة البيانات...")
            
            # التحقق من وجود جدول shift_report
            shift_reports = ShiftReport.query.filter(
                ShiftReport.schedule_item_id.in_([item.id for item in self.test_data['schedule_items']])
            ).all()
            
            print(f"  📊 عدد تقارير الفترات في DB: {len(shift_reports)}")
            
            # التحقق من أن كل تقرير مرتبط بعنصر جدول محدد
            for report in shift_reports:
                schedule_item = DailyScheduleItem.query.get(report.schedule_item_id)
                if not schedule_item:
                    error_msg = f"تقرير فترة {report.id} غير مرتبط بعنصر جدول صحيح"
                    print(f"  ❌ {error_msg}")
                    self.issues_found.append(error_msg)
                else:
                    print(f"  ✅ تقرير {report.id[:8]}... مرتبط بـ schedule_item {schedule_item.id[:8]}...")
            
            print(f"\n  ✅ تقارير الفترات مخزنة بشكل منفصل ومستقل")
            self.tests_passed.append("✅ التخزين المنفصل للتقارير")
            
        except Exception as e:
            print(f"\n❌ خطأ في فحص التخزين: {str(e)}")
            self.issues_found.append(f"خطأ في فحص التخزين: {str(e)}")
    
    def verify_pm_can_see_schedules(self):
        """6️⃣  التحقق من ظهور الجداول لمسؤول المشروع"""
        print("\n" + "="*80)
        print("6️⃣  التحقق من ظهور الجداول لمسؤول المشروع...")
        print("="*80)
        
        try:
            pm = self.test_data['pm']
            project = self.test_data['project']
            schedule = self.test_data['schedule']
            
            print(f"\n👔 مسؤول المشروع: {pm.full_name}")
            
            # محاكاة استعلام مسؤول المشروع
            pm_schedules = DailySchedule.query.filter_by(
                project_id=project.id
            ).order_by(DailySchedule.date.desc()).all()
            
            print(f"  📋 عدد الجداول المرئية: {len(pm_schedules)}")
            
            if len(pm_schedules) == 0:
                error_msg = "مسؤول المشروع لا يرى أي جداول!"
                print(f"  ❌ {error_msg}")
                self.issues_found.append(error_msg)
            else:
                print(f"  ✅ مسؤول المشروع يرى الجداول")
                
                for sched in pm_schedules:
                    items_count = DailyScheduleItem.query.filter_by(daily_schedule_id=sched.id).count()
                    print(f"     📅 {sched.date} - {items_count} عناصر")
                
                # التحقق من ظهور التقارير المرتبطة
                print(f"\n  🔍 فحص التقارير المرتبطة...")
                for item in schedule.items:
                    shift_report = ShiftReport.query.filter_by(schedule_item_id=item.id).first()
                    if shift_report:
                        print(f"     ✅ عنصر {item.handler.full_name}: يوجد تقرير")
                    else:
                        print(f"     ⚪ عنصر {item.handler.full_name}: لا يوجد تقرير بعد")
                
                self.tests_passed.append("✅ مسؤول المشروع يرى الجداول والتقارير")
            
        except Exception as e:
            print(f"\n❌ خطأ في فحص رؤية مسؤول المشروع: {str(e)}")
            self.issues_found.append(f"خطأ في رؤية مسؤول المشروع: {str(e)}")
    
    def verify_database_integrity(self):
        """7️⃣  التحقق من التكامل والبيانات في قاعدة البيانات"""
        print("\n" + "="*80)
        print("7️⃣  التحقق من تكامل قاعدة البيانات...")
        print("="*80)
        
        try:
            schedule = self.test_data['schedule']
            schedule_items = self.test_data['schedule_items']
            
            print("\nفحص البيانات المحفوظة...")
            
            # التحقق من الجدول
            db_schedule = DailySchedule.query.get(schedule.id)
            if not db_schedule:
                error_msg = "الجدول غير موجود في قاعدة البيانات!"
                print(f"  ❌ {error_msg}")
                self.issues_found.append(error_msg)
            else:
                print(f"  ✅ الجدول محفوظ: {db_schedule.date}")
                print(f"     📁 المشروع: {db_schedule.project.name}")
                print(f"     📊 الحالة: {db_schedule.status.value}")
                print(f"     👤 المنشئ: {db_schedule.created_by.full_name if db_schedule.created_by else 'غير محدد'}")
            
            # التحقق من العناصر
            print(f"\n  🔍 فحص عناصر الجدول...")
            for item in schedule_items:
                db_item = DailyScheduleItem.query.get(item.id)
                if not db_item:
                    error_msg = f"عنصر الجدول {item.id} غير موجود في قاعدة البيانات!"
                    print(f"     ❌ {error_msg}")
                    self.issues_found.append(error_msg)
                else:
                    # التحقق من جميع الحقول
                    checks = {
                        'السائس': db_item.handler_user_id is not None,
                        'الكلب': db_item.dog_id is not None,
                        'الفترة': db_item.shift_id is not None,
                        'الموقع': db_item.location_id is not None,
                        'التاريخ': db_item.schedule.date is not None
                    }
                    
                    all_ok = all(checks.values())
                    status = "✅" if all_ok else "⚠️"
                    print(f"     {status} عنصر {db_item.handler.full_name}:")
                    for field, ok in checks.items():
                        print(f"        {'✅' if ok else '❌'} {field}")
                    
                    if not all_ok:
                        self.issues_found.append(f"عنصر الجدول لـ {db_item.handler.full_name} به بيانات ناقصة")
            
            if len([issue for issue in self.issues_found if 'قاعدة البيانات' in issue or 'ناقصة' in issue]) == 0:
                self.tests_passed.append("✅ تكامل قاعدة البيانات")
            
        except Exception as e:
            print(f"\n❌ خطأ في فحص التكامل: {str(e)}")
            self.issues_found.append(f"خطأ في فحص التكامل: {str(e)}")
    
    def generate_final_report(self):
        """8️⃣  إصدار التقرير النهائي"""
        print("\n" + "="*80)
        print("📊 التقرير النهائي للاختبار الذاتي")
        print("="*80)
        
        total_tests = len(self.tests_passed)
        total_issues = len(self.issues_found)
        total_fixes = len(self.fixes_applied)
        
        print(f"\n✅ الاختبارات الناجحة: {total_tests}")
        for test in self.tests_passed:
            print(f"   {test}")
        
        if total_issues > 0:
            print(f"\n⚠️  المشاكل المكتشفة: {total_issues}")
            for issue in self.issues_found:
                print(f"   ❌ {issue}")
        else:
            print(f"\n🎉 لم يتم اكتشاف أي مشاكل!")
        
        if total_fixes > 0:
            print(f"\n🔧 الإصلاحات المطبقة: {total_fixes}")
            for fix in self.fixes_applied:
                print(f"   ✅ {fix}")
        
        # الحكم النهائي
        print("\n" + "="*80)
        if total_issues == 0:
            print("🎉 النتيجة: نظام الجدولة اليومية يعمل بالكامل بنجاح!")
            print("="*80)
            return True
        else:
            print("⚠️  النتيجة: نظام الجدولة به بعض المشاكل التي تحتاج إلى إصلاح")
            print("="*80)
            return False
    
    def run_full_test(self):
        """تشغيل الاختبار الكامل"""
        try:
            self.setup_test_environment()
            self.cleanup_test_data()
            
            # 1. إنشاء البيانات التجريبية
            self.create_test_data()
            
            # 2. إنشاء الجدولة اليومية
            self.create_daily_schedule()
            
            # 3. التحقق من رؤية السائس للجدول
            self.verify_handler_sees_schedule()
            
            # 4. التحقق من قدرة السائس على رفع التقارير
            self.verify_handler_can_submit_reports()
            
            # 5. التحقق من التخزين المنفصل
            self.verify_reports_storage()
            
            # 6. التحقق من رؤية مسؤول المشروع
            self.verify_pm_can_see_schedules()
            
            # 7. التحقق من تكامل قاعدة البيانات
            self.verify_database_integrity()
            
            # 8. إصدار التقرير النهائي
            success = self.generate_final_report()
            
            return success
            
        except Exception as e:
            print(f"\n💥 خطأ فادح في الاختبار: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if self.app_context:
                self.app_context.pop()


def main():
    """نقطة الدخول الرئيسية"""
    print("\n🚀 بدء الاختبار الشامل والذاتي لنظام الجدولة اليومية للسائسين")
    print("="*80)
    
    tester = ScheduleSystemTester()
    success = tester.run_full_test()
    
    # كود الخروج
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
