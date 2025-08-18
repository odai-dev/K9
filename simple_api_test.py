#!/usr/bin/env python3
"""
Simple test script for Unified Matrix API endpoints
"""

import requests
import json
from datetime import date, timedelta

# Base configuration
BASE_URL = 'http://localhost:5000'
API_BASE = f'{BASE_URL}/api/reports/attendance'

def test_api_endpoints():
    """Test basic API functionality"""
    
    # Calculate test date range (last 7 days)
    end_date = date.today()
    start_date = end_date - timedelta(days=6)
    
    # Test data
    test_payload = {
        'date_from': start_date.strftime('%Y-%m-%d'),
        'date_to': end_date.strftime('%Y-%m-%d'),
        'per_page': 25,
        'include_dogs': False,
        'status_in': ['PRESENT', 'ABSENT', 'LATE', 'SICK']
    }
    
    print(f"Testing Unified Matrix API with date range: {start_date} to {end_date}")
    print("-" * 60)
    
    # Test 1: Run unified matrix
    print("1. Testing /run/unified endpoint...")
    
    try:
        response = requests.post(
            f'{API_BASE}/run/unified',
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Success!")
            print(f"   - Days in range: {len(data.get('days', []))}")
            print(f"   - Employee rows: {len(data.get('rows', []))}")
            print(f"   - Current page: {data.get('pagination', {}).get('page', 'N/A')}")
            print(f"   - Total pages: {data.get('pagination', {}).get('pages', 'N/A')}")
            
            # Show sample row data if available
            if data.get('rows'):
                sample_row = data['rows'][0]
                print(f"   - Sample employee: {sample_row.get('employee_name', 'N/A')}")
                print(f"   - Sample has {len(sample_row.get('cells', []))} day cells")
        else:
            print(f"   ✗ Failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text[:200]}")
    
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Request failed: {e}")
    
    print()
    
    # Test 2: Test export endpoint (PDF)
    print("2. Testing /export/pdf/unified endpoint...")
    
    try:
        response = requests.post(
            f'{API_BASE}/export/pdf/unified',
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('path'):
                print(f"   ✓ PDF export successful!")
                print(f"   - File path: {data['path']}")
            else:
                print(f"   ? Response: {data}")
        else:
            print(f"   ✗ Failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text[:200]}")
    
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Request failed: {e}")
    
    print()
    
    # Test 3: Test UI route
    print("3. Testing /unified UI route...")
    
    try:
        response = requests.get(f'{BASE_URL}/reports/attendance/unified')
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✓ UI route accessible!")
            print(f"   - Response length: {len(response.text)} characters")
        elif response.status_code == 302:
            print(f"   → Redirected (likely authentication required)")
        else:
            print(f"   ✗ Failed with status {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Request failed: {e}")
    
    print()
    print("API Test Complete!")
    print("-" * 60)

if __name__ == '__main__':
    test_api_endpoints()