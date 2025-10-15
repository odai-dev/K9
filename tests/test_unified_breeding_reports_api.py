import pytest
import json
from datetime import date, timedelta
from flask import url_for

from k9.models.models import User, FeedingLog, BodyConditionScale, PrepMethod


@pytest.mark.unit
class TestUnifiedBreedingReportsAPI:
    """Test suite for unified breeding reports API endpoints"""

    def test_unified_feeding_daily_range(self, authenticated_client, test_feeding_logs, test_project):
        """Test unified feeding report with daily range"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check unified response structure
        assert data['success'] is True
        assert 'pagination' in data
        assert 'filters' in data
        assert 'kpis' in data
        assert 'rows' in data
        assert 'range_info' in data
        
        # Check range_info contains proper metadata
        range_info = data['range_info']
        assert range_info['range_type'] == 'daily'
        assert range_info['date_from'] == target_date.strftime('%Y-%m-%d')
        assert range_info['date_to'] == target_date.strftime('%Y-%m-%d')

    def test_unified_feeding_weekly_range(self, authenticated_client, test_feeding_logs, test_project):
        """Test unified feeding report with weekly range"""
        target_date = date.today()
        week_start = target_date - timedelta(days=target_date.weekday())
        week_end = week_start + timedelta(days=6)
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'weekly',
                'date_from': week_start.strftime('%Y-%m-%d'),
                'date_to': week_end.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['range_info']['range_type'] == 'weekly'

    def test_unified_feeding_monthly_range(self, authenticated_client, test_feeding_logs, test_project):
        """Test unified feeding report with monthly range"""
        target_date = date.today()
        month_start = target_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'monthly',
                'date_from': month_start.strftime('%Y-%m-%d'),
                'date_to': month_end.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['range_info']['range_type'] == 'monthly'

    def test_unified_feeding_custom_range_short(self, authenticated_client, test_feeding_logs, test_project):
        """Test unified feeding report with custom range <= 31 days"""
        end_date = date.today()
        start_date = end_date - timedelta(days=10)  # 11 days total
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'custom',
                'date_from': start_date.strftime('%Y-%m-%d'),
                'date_to': end_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['range_info']['range_type'] == 'custom'
        # For short ranges, should show daily data
        assert data['range_info']['aggregation_level'] == 'daily'

    def test_unified_feeding_custom_range_long(self, authenticated_client, test_feeding_logs, test_project):
        """Test unified feeding report with custom range > 31 days"""
        end_date = date.today()
        start_date = end_date - timedelta(days=45)  # 46 days total
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'custom',
                'date_from': start_date.strftime('%Y-%m-%d'),
                'date_to': end_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        # For long ranges, should aggregate weekly
        assert data['range_info']['aggregation_level'] == 'weekly'

    def test_unified_checkup_daily_range(self, authenticated_client, test_project, test_dogs, db_session):
        """Test unified checkup report with daily range"""
        # Create test checkup data
        from k9.models.models import BreedingCheckup
        from datetime import datetime
        
        target_date = date.today()
        checkup = BreedingCheckup(
            project_id=test_project.id,
            dog_id=test_dogs[0].id,
            date=target_date,
            time=datetime.now().time(),
            eyes='صافيتان',
            ears='نظيفتان',
            nose='رطبة',
            front_legs='سليمتان',
            hind_legs='سليمتان',
            coat='صحية',
            tail='طبيعي',
            severity='طبيعي',
            notes='فحص روتيني'
        )
        db_session.add(checkup)
        db_session.commit()
        
        response = authenticated_client.get(
            '/api/breeding/checkup-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['range_info']['range_type'] == 'daily'

    def test_unified_feeding_caching_headers(self, authenticated_client, test_feeding_logs, test_project):
        """Test that unified feeding API returns proper caching headers"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        
        # Check caching headers
        cache_control = response.headers.get('Cache-Control')
        assert cache_control is not None
        assert 'private' in cache_control
        assert 'max-age=60' in cache_control
        
        # Check Vary header for security
        vary_header = response.headers.get('Vary')
        assert vary_header is not None
        assert 'Cookie' in vary_header
        assert 'Authorization' in vary_header

    def test_unified_checkup_caching_headers(self, authenticated_client, test_project):
        """Test that unified checkup API returns proper caching headers"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/breeding/checkup-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        
        # Check caching headers
        cache_control = response.headers.get('Cache-Control')
        assert cache_control is not None
        assert 'private' in cache_control
        assert 'max-age=60' in cache_control

    def test_unified_feeding_pdf_export(self, authenticated_client, test_feeding_logs, test_project):
        """Test unified feeding PDF export functionality"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/unified/export-pdf',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'file' in data
        assert 'filename' in data
        
        # Check filename format
        filename = data['filename']
        assert 'breeding_feeding_' in filename
        assert '.pdf' in filename
        assert target_date.strftime('%Y-%m-%d') in filename

    def test_unified_checkup_pdf_export(self, authenticated_client, test_project):
        """Test unified checkup PDF export functionality"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/breeding/checkup-reports/unified/export-pdf',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'file' in data
        assert 'filename' in data
        
        # Check filename format
        filename = data['filename']
        assert 'breeding_checkup_' in filename
        assert '.pdf' in filename

    def test_unified_feeding_pdf_export_caching(self, authenticated_client, test_feeding_logs, test_project):
        """Test that unified feeding PDF export returns proper caching headers"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/unified/export-pdf',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        
        # Check caching headers on PDF export
        cache_control = response.headers.get('Cache-Control')
        assert cache_control is not None
        assert 'private' in cache_control
        assert 'max-age=60' in cache_control

    def test_unified_feeding_invalid_range_type(self, authenticated_client, test_project):
        """Test unified feeding with invalid range_type parameter"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'invalid_range',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_unified_feeding_missing_dates(self, authenticated_client, test_project):
        """Test unified feeding with missing date parameters"""
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily'
                # Missing date_from and date_to
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_unified_feeding_arabic_content(self, authenticated_client, test_feeding_logs, test_project):
        """Test that unified feeding API handles Arabic content correctly"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check Arabic content in KPIs
        if 'by_meal_type' in data['kpis']:
            meal_types = data['kpis']['by_meal_type']
            arabic_types = ['طازج', 'مجفف', 'مختلط']
            for meal_type in arabic_types:
                assert meal_type in meal_types

    def test_unified_feeding_dog_filter(self, authenticated_client, test_feeding_logs, test_project, test_dogs):
        """Test unified feeding with dog_id filter"""
        target_date = date.today()
        test_dog = test_dogs[0]
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d'),
                'dog_id': test_dog.id
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # All returned rows should be for the specified dog
        for row in data['rows']:
            assert row['dog_id'] == str(test_dog.id)