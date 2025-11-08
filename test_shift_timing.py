"""
اختبار آلية منع إنشاء تقرير الفترة قبل انتهائها
"""
from app import app, db
from k9.services.handler_service import ShiftReportService
from k9.models.models_handler_daily import DailyScheduleItem
from datetime import datetime

with app.app_context():
    print("=" * 80)
    print("اختبار آلية التحقق من وقت إنشاء تقرير الفترة")
    print("=" * 80)
    print(f"\n⏰ الوقت الحالي: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # جلب جميع عناصر الجدول لليوم
    from k9.models.models_handler_daily import DailySchedule
    
    today = datetime.now().date()
    items = DailyScheduleItem.query.join(
        DailySchedule
    ).filter(
        DailySchedule.date == today
    ).all()
    
    if not items:
        print("❌ لا توجد عناصر جدول لليوم")
    else:
        for item in items:
            print(f"\n📋 عنصر الجدول: {item.id}")
            print(f"   السائس: {item.handler.username if item.handler else 'غير محدد'}")
            print(f"   الكلب: {item.dog.name if item.dog else 'غير محدد'}")
            print(f"   الوردية: {item.shift.name if item.shift else 'غير محدد'}")
            
            if item.shift:
                print(f"   وقت البداية: {item.shift.start_time}")
                print(f"   وقت النهاية: {item.shift.end_time}")
                
                # حساب وقت انتهاء الوردية
                shift_end = datetime.combine(item.schedule.date, item.shift.end_time)
                now = datetime.now()
                
                if now < shift_end:
                    time_left = shift_end - now
                    hours = int(time_left.total_seconds() // 3600)
                    minutes = int((time_left.total_seconds() % 3600) // 60)
                    print(f"   ⏳ الوقت المتبقي لانتهاء الوردية: {hours} ساعة و {minutes} دقيقة")
                else:
                    print(f"   ✅ الوردية انتهت")
            
            # اختبار إمكانية إنشاء التقرير
            print(f"\n   🔍 اختبار إمكانية إنشاء تقرير الفترة:")
            can_create, error = ShiftReportService.can_create_shift_report(str(item.id))
            
            if can_create:
                print(f"   ✅ يمكن إنشاء التقرير")
            else:
                print(f"   ❌ لا يمكن إنشاء التقرير")
                print(f"   📝 السبب: {error}")
            
            print("-" * 80)
    
    print("\n✨ انتهى الاختبار")
