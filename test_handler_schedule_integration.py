"""
Integration test to verify handler schedule display functionality
"""
import requests
from bs4 import BeautifulSoup
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_handler_login_and_schedule():
    """Test that a handler can login and see their schedule"""
    print("="*80)
    print("HANDLER SCHEDULE INTEGRATION TEST")
    print("="*80)
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Get login page
    print("\n📋 Step 1: Accessing login page...")
    response = session.get(f"{BASE_URL}/auth/login")
    if response.status_code != 200:
        print(f"❌ Failed to access login page: {response.status_code}")
        return False
    print("✅ Login page accessible")
    
    # Extract CSRF token
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})
    if not csrf_token:
        print("❌ Could not find CSRF token")
        return False
    csrf_token_value = csrf_token.get('value')
    print(f"✅ CSRF token found")
    
    # Step 2: Login as handler1
    print("\n📋 Step 2: Logging in as handler1...")
    login_data = {
        'username': 'handler1',
        'password': 'test123',
        'csrf_token': csrf_token_value
    }
    response = session.post(f"{BASE_URL}/auth/login", data=login_data, allow_redirects=True)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return False
    
    # Check if we're redirected to dashboard
    if '/handler/dashboard' not in response.url:
        print(f"❌ Not redirected to handler dashboard. Current URL: {response.url}")
        return False
    print("✅ Successfully logged in as handler1")
    
    # Step 3: Check handler dashboard
    print("\n📋 Step 3: Checking handler dashboard content...")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check for welcome message
    welcome_text = soup.find(text=lambda text: text and 'خالد السائس' in text)
    if not welcome_text:
        print("❌ Handler name not found on dashboard")
        return False
    print("✅ Handler name 'خالد السائس' found on dashboard")
    
    # Step 4: Check for "Today's Schedule" section
    print("\n📋 Step 4: Checking 'Today's Schedule' section...")
    schedule_header = soup.find(text=lambda text: text and 'جدول اليوم' in text)
    if not schedule_header:
        print("❌ 'جدول اليوم' (Today's Schedule) section not found")
        return False
    print("✅ 'جدول اليوم' section found")
    
    # Step 5: Check for schedule items
    print("\n📋 Step 5: Checking for schedule items...")
    
    # Look for dog names رعد and صقر (handler1 has 2 dogs)
    page_text = response.text
    
    dogs_found = []
    if 'رعد' in page_text:
        dogs_found.append('رعد')
        print("✅ Dog 'رعد' found in schedule")
    
    if 'صقر' in page_text:
        dogs_found.append('صقر')
        print("✅ Dog 'صقر' found in schedule")
    
    if len(dogs_found) < 2:
        print(f"❌ Expected 2 dogs for handler1, found {len(dogs_found)}: {dogs_found}")
        return False
    
    # Check for shift name
    if 'الوردية الصباحية' in page_text:
        print("✅ Shift 'الوردية الصباحية' found in schedule")
    else:
        print("❌ Shift name not found in schedule")
        return False
    
    # Step 6: Check for "No schedule" message (should NOT be present)
    print("\n📋 Step 6: Verifying 'No schedule' message is NOT present...")
    if 'لا يوجد جدول لليوم' in page_text:
        print("❌ 'No schedule' message found - schedules are not displaying!")
        return False
    print("✅ 'No schedule' message NOT found - schedules are displaying correctly")
    
    # Step 7: Logout
    print("\n📋 Step 7: Logging out...")
    response = session.get(f"{BASE_URL}/auth/logout", allow_redirects=True)
    print("✅ Logged out successfully")
    
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED!")
    print("="*80)
    print("\nSummary:")
    print("  ✓ Handler login successful")
    print("  ✓ Handler dashboard accessible")
    print("  ✓ Handler name displayed correctly")
    print("  ✓ 'Today's Schedule' section present")
    print("  ✓ Both dogs (رعد, صقر) displayed in schedule")
    print("  ✓ Shift name displayed correctly")
    print("  ✓ No 'empty schedule' message")
    print("\n🎉 Handler schedule feature is working correctly!")
    return True

if __name__ == '__main__':
    try:
        success = test_handler_login_and_schedule()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
