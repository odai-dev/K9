#!/usr/bin/env python3
"""
Test trainer daily report functionality
"""

import os
from datetime import date, timedelta
from app import app, db
from models import User, TrainingSession
from trainer_daily_services import get_trainer_daily

def test_trainer_daily_report():
    """Test the trainer daily report with sample data"""
    
    with app.app_context():
        print("🧪 Testing Trainer Daily Report...")
        
        # Get admin user
        admin_user = db.session.query(User).filter_by(username='admin').first()
        if not admin_user:
            print("❌ Admin user not found")
            return
            
        print(f"✅ Testing with user: {admin_user.username}")
        
        # Test date (today)
        test_date = date.today()
        print(f"📅 Testing date: {test_date}")
        
        # Check if we have training sessions
        sessions_count = db.session.query(TrainingSession).count()
        print(f"📊 Total training sessions in database: {sessions_count}")
        
        # Test the trainer daily service
        try:
            report_data = get_trainer_daily(
                project_id=None,  # All projects for admin
                date_filter=test_date,
                trainer_id=None,  # All trainers
                dog_id=None,     # All dogs
                category=None,   # All categories
                user=admin_user
            )
            
            print("✅ Report generation successful!")
            print(f"📈 Report summary:")
            print(f"   - Sessions found: {len(report_data['sessions'])}")
            print(f"   - Dogs in summary: {len(report_data['summary_by_dog'])}")
            print(f"   - Total sessions: {report_data['kpis']['total_sessions']}")
            print(f"   - Unique dogs: {report_data['kpis']['unique_dogs']}")
            print(f"   - Unique trainers: {report_data['kpis']['unique_trainers']}")
            
            # Show sample session data
            if report_data['sessions']:
                print(f"\n📝 Sample session:")
                session = report_data['sessions'][0]
                print(f"   - Time: {session['time']}")
                print(f"   - Trainer: {session['trainer_name']}")
                print(f"   - Dog: {session['dog_name']}")
                print(f"   - Category: {session['category_ar']}")
                print(f"   - Subject: {session['subject']}")
                
            # Show dog summary
            if report_data['summary_by_dog']:
                print(f"\n🐕 Sample dog summary:")
                dog_summary = report_data['summary_by_dog'][0]
                print(f"   - Dog: {dog_summary['dog_name']}")
                print(f"   - Sessions: {dog_summary['sessions_count']}")
                print(f"   - Total duration: {dog_summary['total_duration_min']} min")
                print(f"   - Average rating: {dog_summary['avg_success_rating']:.1f}")
                
            return True
            
        except Exception as e:
            print(f"❌ Report generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_trainer_daily_report()
    if success:
        print("\n🎉 Trainer Daily Report is working correctly!")
    else:
        print("\n💥 Trainer Daily Report has issues!")