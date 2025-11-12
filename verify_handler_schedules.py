from app import app, db
from k9.services.handler_service import DailyScheduleService
from k9.models.models import User, UserRole
from datetime import date

with app.app_context():
    print("="*80)
    print("HANDLER SCHEDULE VERIFICATION")
    print("="*80)
    
    handlers = User.query.filter_by(role=UserRole.HANDLER).all()
    
    for handler in handlers:
        print(f"\n👤 Handler: {handler.full_name} (username: {handler.username})")
        print(f"   User ID: {handler.id}")
        print(f"   Project ID: {handler.project_id}")
        
        schedule_items, schedule_date = DailyScheduleService.get_active_handler_schedule(str(handler.id))
        
        if schedule_items:
            print(f"   ✅ Schedule found for: {schedule_date}")
            print(f"   📋 Schedule items ({len(schedule_items)}):")
            for item in schedule_items:
                shift_name = item.shift.name if item.shift else "No shift"
                dog_name = item.dog.name if item.dog else "No dog"
                location_name = item.location.name if item.location else "No location"
                print(f"      • {shift_name}: {dog_name} @ {location_name} ({item.status.value})")
        else:
            print(f"   ❌ No schedule found")
    
    print("\n" + "="*80)
    print("VERIFICATION COMPLETE")
    print("="*80)
