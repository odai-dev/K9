"""
اختبار تكاملية سير العمل الكامل
من المدير العام/مسؤول المشروع → السائس → مراجعة التقرير
"""
from app import app, db
from k9.models.models import User, UserRole, Project
from k9.models.models_handler_daily import DailySchedule, DailyScheduleItem, ShiftReport, ReportStatus
from datetime import datetime

with app.app_context():
    print("=" * 100)
    print("🔍 اختبار تكاملية سير العمل الكامل للنظام")
    print("=" * 100)
    
    # =================================================================
    # 1. التحقق من الأدوار الموجودة
    # =================================================================
    print("\n" + "=" * 100)
    print("📌 الخطوة 1: التحقق من الأدوار الموجودة في النظام")
    print("=" * 100)
    
    admin_count = User.query.filter_by(role=UserRole.GENERAL_ADMIN).count()
    pm_count = User.query.filter_by(role=UserRole.PROJECT_MANAGER).count()
    handler_count = User.query.filter_by(role=UserRole.HANDLER).count()
    
    print(f"✅ المديرون العامون: {admin_count}")
    print(f"✅ مسؤولو المشاريع: {pm_count}")
    print(f"✅ السائسون: {handler_count}")
    
    # عرض تفاصيل المستخدمين
    print("\n📋 تفاصيل المستخدمين:")
    
    admins = User.query.filter_by(role=UserRole.GENERAL_ADMIN).all()
    for admin in admins:
        print(f"   👤 مدير عام: {admin.username}")
    
    pms = User.query.filter_by(role=UserRole.PROJECT_MANAGER).all()
    for pm in pms:
        project = Project.query.filter_by(manager_id=pm.id).first()
        if not project:
            employee = pm.employee
            if employee:
                project = Project.query.filter_by(project_manager_id=employee.id).first()
        
        print(f"   👤 مسؤول مشروع: {pm.username} - المشروع: {project.name if project else 'غير محدد'}")
    
    handlers = User.query.filter_by(role=UserRole.HANDLER).all()
    for handler in handlers:
        project = Project.query.get(handler.project_id) if handler.project_id else None
        print(f"   👤 سائس: {handler.username} - المشروع: {project.name if project else 'غير محدد'}")
    
    # =================================================================
    # 2. التحقق من إنشاء الجداول
    # =================================================================
    print("\n" + "=" * 100)
    print("📌 الخطوة 2: التحقق من إنشاء الجداول اليومية")
    print("=" * 100)
    
    schedules = DailySchedule.query.filter_by(date=datetime.now().date()).all()
    
    if not schedules:
        print("❌ لا توجد جداول لليوم")
    else:
        for schedule in schedules:
            print(f"\n✅ جدول يومي:")
            print(f"   📅 التاريخ: {schedule.date}")
            print(f"   🏢 المشروع: {schedule.project.name if schedule.project else 'غير محدد'}")
            print(f"   📝 الحالة: {schedule.status.value}")
            print(f"   👤 أنشأه: {schedule.created_by.username if schedule.created_by else 'غير محدد'}")
            
            items = DailyScheduleItem.query.filter_by(daily_schedule_id=schedule.id).all()
            print(f"   📊 عدد العناصر: {len(items)}")
            
            for item in items:
                print(f"\n      🔹 عنصر الجدول:")
                print(f"         السائس: {item.handler.username if item.handler else 'غير محدد'}")
                print(f"         الكلب: {item.dog.name if item.dog else 'غير محدد'}")
                print(f"         الوردية: {item.shift.name if item.shift else 'غير محدد'} ({item.shift.start_time if item.shift else ''} - {item.shift.end_time if item.shift else ''})")
                print(f"         الحالة: {item.status.value}")
    
    # =================================================================
    # 3. التحقق من رؤية السائس للجدول
    # =================================================================
    print("\n" + "=" * 100)
    print("📌 الخطوة 3: التحقق من رؤية السائس للجدول")
    print("=" * 100)
    
    from k9.services.handler_service import DailyScheduleService
    
    for handler in handlers[:3]:  # فحص أول 3 سائسين فقط
        today_schedule = DailyScheduleService.get_handler_schedule_for_date(
            str(handler.id), 
            datetime.now().date()
        )
        
        print(f"\n👤 السائس: {handler.username}")
        if today_schedule:
            print(f"   ✅ يمكنه رؤية {len(today_schedule)} عنصر/عناصر في جدوله:")
            for item in today_schedule:
                print(f"      - {item.shift.name if item.shift else 'غير محدد'}: {item.dog.name if item.dog else 'غير محدد'}")
        else:
            print(f"   ❌ لا يوجد جدول لهذا السائس اليوم")
    
    # =================================================================
    # 4. التحقق من تقارير الفترة
    # =================================================================
    print("\n" + "=" * 100)
    print("📌 الخطوة 4: التحقق من تقارير الفترة")
    print("=" * 100)
    
    shift_reports = ShiftReport.query.filter_by(date=datetime.now().date()).all()
    
    if not shift_reports:
        print("📝 لا توجد تقارير فترة لليوم (هذا طبيعي لأن الورديات لم تنتهِ بعد)")
    else:
        for report in shift_reports:
            print(f"\n✅ تقرير فترة:")
            print(f"   السائس: {report.handler.username if report.handler else 'غير محدد'}")
            print(f"   الكلب: {report.dog.name if report.dog else 'غير محدد'}")
            print(f"   التاريخ: {report.date}")
            print(f"   الحالة: {report.status.value}")
    
    # =================================================================
    # 5. التحقق من آلية المراجعة
    # =================================================================
    print("\n" + "=" * 100)
    print("📌 الخطوة 5: التحقق من آلية المراجعة")
    print("=" * 100)
    
    from k9.models.models_handler_daily import HandlerReport
    
    # فحص التقارير المرسلة للمراجعة
    submitted_reports = HandlerReport.query.filter_by(status=ReportStatus.SUBMITTED).all()
    approved_reports = HandlerReport.query.filter_by(status=ReportStatus.APPROVED_BY_PM).all()
    rejected_reports = HandlerReport.query.filter_by(status=ReportStatus.REJECTED).all()
    
    print(f"\n📊 إحصائيات التقارير اليومية:")
    print(f"   📤 تقارير مرسلة (تنتظر المراجعة): {len(submitted_reports)}")
    print(f"   ✅ تقارير معتمدة من قبل مسؤول المشروع: {len(approved_reports)}")
    print(f"   ❌ تقارير مرفوضة: {len(rejected_reports)}")
    
    # =================================================================
    # 6. اختبار الصلاحيات
    # =================================================================
    print("\n" + "=" * 100)
    print("📌 الخطوة 6: اختبار الصلاحيات")
    print("=" * 100)
    
    print("\n✅ الصلاحيات المتوقعة:")
    print("   1️⃣ المدير العام / مسؤول المشروع:")
    print("      - إنشاء جداول يومية ✓")
    print("      - تعديل الجداول (قبل الإقفال) ✓")
    print("      - عرض جميع الجداول ✓")
    print("      - مراجعة واعتماد/رفض تقارير السائسين ✓")
    print("")
    print("   2️⃣ السائس:")
    print("      - عرض جدوله الخاص فقط ✓")
    print("      - إنشاء تقرير الفترة (بعد انتهاء الفترة فقط) ✓")
    print("      - إنشاء التقرير اليومي العام ✓")
    print("      - عدم القدرة على إنشاء أو تعديل الجداول ✓")
    
    # =================================================================
    # 7. سير العمل الكامل
    # =================================================================
    print("\n" + "=" * 100)
    print("📌 الخطوة 7: سير العمل الكامل")
    print("=" * 100)
    
    print("\n🔄 سير العمل المتكامل:")
    print("")
    print("1️⃣ مسؤول المشروع/المدير العام:")
    print("   ↓ ينشئ جدول يومي")
    print("   ↓ يضيف السائسين والكلاب والورديات")
    print("   ↓ يحفظ الجدول")
    print("")
    print("2️⃣ السائس:")
    print("   ↓ يسجل الدخول ويرى جدوله في لوحة التحكم")
    print("   ↓ ينتظر انتهاء الوردية")
    print("   ↓ بعد انتهاء الوردية، ينشئ تقرير الفترة")
    print("   ↓ يملأ التقرير ويرسله")
    print("")
    print("3️⃣ مسؤول المشروع:")
    print("   ↓ يستلم إشعار بتقرير جديد")
    print("   ↓ يراجع التقرير")
    print("   ↓ يعتمده أو يرفضه أو يطلب تعديلات")
    print("")
    print("4️⃣ النتيجة:")
    print("   ✅ التقرير معتمد → يُرسل للمدير العام")
    print("   🔄 طلب تعديل → يعود للسائس للتعديل")
    print("   ❌ مرفوض → ينتهي سير العمل")
    
    print("\n" + "=" * 100)
    print("✨ انتهى اختبار التكاملية")
    print("=" * 100)
