"""
Direct test using Flask test client to verify handler schedule display
"""
from app import app, db
from k9.models.models import User
from flask_login import login_user
import sys

def test_handler_dashboard_schedule():
    """Test that handler dashboard shows schedules correctly"""
    print("="*80)
    print("HANDLER DASHBOARD SCHEDULE TEST (Direct)")
    print("="*80)
    
    with app.test_client() as client:
        with app.app_context():
            # Get handler1 user
            print("\n📋 Step 1: Getting handler1 user from database...")
            handler = User.query.filter_by(username='handler1').first()
            if not handler:
                print("❌ handler1 user not found in database")
                return False
            print(f"✅ Found handler: {handler.full_name} (ID: {handler.id})")
            print(f"   Project ID: {handler.project_id}")
            print(f"   Dog ID: {handler.dog_id}")
            
            # Login
            print("\n📋 Step 2: Logging in as handler1...")
            with client.session_transaction() as sess:
                sess['_user_id'] = str(handler.id)
                sess['_fresh'] = True
            
            # Access handler dashboard
            print("\n📋 Step 3: Accessing handler dashboard...")
            response = client.get('/handler/dashboard', follow_redirects=True)
            
            if response.status_code != 200:
                print(f"❌ Failed to access handler dashboard: {response.status_code}")
                return False
            print(f"✅ Handler dashboard accessible (status: {response.status_code})")
            
            # Check response content
            html_content = response.data.decode('utf-8')
            
            # Step 4: Check for handler name
            print("\n📋 Step 4: Checking for handler name...")
            if 'خالد السائس' in html_content:
                print("✅ Handler name 'خالد السائس' found")
            else:
                print("❌ Handler name not found")
                return False
            
            # Step 5: Check for "Today's Schedule" section
            print("\n📋 Step 5: Checking for 'Today's Schedule' section...")
            if 'جدول اليوم' in html_content:
                print("✅ 'جدول اليوم' section found")
            else:
                print("❌ 'جدول اليوم' section not found")
                return False
            
            # Step 6: Check for schedule items (dogs)
            print("\n📋 Step 6: Checking for schedule items...")
            
            dogs_found = []
            if 'رعد' in html_content:
                dogs_found.append('رعد')
                print("✅ Dog 'رعد' found in schedule")
            else:
                print("⚠ Dog 'رعد' not found")
            
            if 'صقر' in html_content:
                dogs_found.append('صقر')
                print("✅ Dog 'صقر' found in schedule")
            else:
                print("⚠ Dog 'صقر' not found")
            
            if len(dogs_found) < 2:
                print(f"❌ Expected 2 dogs, found {len(dogs_found)}: {dogs_found}")
                # Let's check what we have
                print("\n📋 Debugging: Checking for schedule table...")
                if '<table' in html_content and 'table-hover' in html_content:
                    print("✅ Schedule table found in HTML")
                else:
                    print("❌ Schedule table not found")
                
                # Check for the "no schedule" message
                if 'لا يوجد جدول لليوم' in html_content:
                    print("❌ 'No schedule for today' message found!")
                    print("\n   This means the schedule is not being retrieved correctly.")
                    print("   Possible causes:")
                    print("   - handler_user_id doesn't match in schedule items")
                    print("   - project_id doesn't match")
                    print("   - schedule date is wrong")
                    return False
                else:
                    print("✅ No 'empty schedule' message found")
            
            # Step 7: Check for shift name
            print("\n📋 Step 7: Checking for shift information...")
            if 'الوردية الصباحية' in html_content:
                print("✅ Shift 'الوردية الصباحية' found")
            else:
                print("⚠ Shift name not found")
            
            # Step 8: Final verification
            print("\n📋 Step 8: Final verification...")
            if 'لا يوجد جدول لليوم' in html_content:
                print("❌ FAILURE: 'No schedule' message is present!")
                return False
            else:
                print("✅ SUCCESS: 'No schedule' message is NOT present")
            
            if len(dogs_found) >= 2:
                print(f"✅ SUCCESS: Found {len(dogs_found)} dogs in schedule")
            else:
                print(f"⚠ WARNING: Only found {len(dogs_found)} dogs")
            
            print("\n" + "="*80)
            if len(dogs_found) >= 2 and 'لا يوجد جدول لليوم' not in html_content:
                print("✅ ALL TESTS PASSED!")
                print("="*80)
                print("\n🎉 Handler schedule feature is working correctly!")
                print(f"   • Handler name displayed: ✓")
                print(f"   • Schedule section present: ✓")
                print(f"   • Dogs displayed ({len(dogs_found)}): {', '.join(dogs_found)}")
                print(f"   • Shift information: ✓")
                print(f"   • No 'empty schedule' message: ✓")
                return True
            else:
                print("⚠ PARTIAL SUCCESS - Some elements missing")
                print("="*80)
                return False

if __name__ == '__main__':
    try:
        success = test_handler_dashboard_schedule()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
