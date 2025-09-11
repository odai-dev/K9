import pytest
import json
from datetime import date, timedelta
from flask import url_for

from k9.models.models import User, FeedingLog, BodyConditionScale, PrepMethod


@pytest.mark.unit
class TestFeedingReportsAPI:
    """Test suite for feeding reports API endpoints"""

    def test_daily_feeding_report_success(self, authenticated_client, test_feeding_logs, test_project):
        """Test successful daily feeding report retrieval"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check response structure based on actual API contract
        assert data['success'] is True
        assert 'pagination' in data
        assert 'filters' in data
        assert 'kpis' in data
        assert 'rows' in data
        assert 'date' in data
        assert 'project_name' in data
        
        # Check pagination metadata
        pagination = data['pagination']
        assert 'page' in pagination
        assert 'per_page' in pagination
        assert 'total' in pagination
        assert 'pages' in pagination
        assert 'has_next' in pagination
        assert 'has_prev' in pagination
        
        # Check KPIs structure
        kpis = data['kpis']
        expected_kpi_keys = ['total_meals', 'total_dogs', 'total_grams', 'total_water_ml', 
                           'fresh_meals', 'dry_meals', 'poor_conditions', 'avg_quantity', 
                           'by_meal_type', 'bcs_dist']
        for key in expected_kpi_keys:
            assert key in kpis

    def test_daily_feeding_report_with_pagination(self, authenticated_client, test_feeding_logs, test_project):
        """Test daily feeding report with pagination parameters"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d'),
                'page': 1,
                'per_page': 2
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        pagination = data['pagination']
        assert pagination['page'] == 1
        assert pagination['per_page'] == 2
        assert len(data['rows']) <= 2

    def test_daily_feeding_report_with_dog_filter(self, authenticated_client, test_feeding_logs, test_project, test_dogs):
        """Test daily feeding report filtered by specific dog"""
        target_date = date.today()
        test_dog = test_dogs[0]
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d'),
                'dog_id': test_dog.id
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # All rows should be for the specified dog
        for row in data['rows']:
            assert row['dog_id'] == str(test_dog.id)

    def test_daily_feeding_report_missing_params(self, authenticated_client):
        """Test daily feeding report with missing required parameters"""
        # Missing both project_id and date
        response = authenticated_client.get('/api/breeding/feeding-reports/daily')
        assert response.status_code == 400
        
        # Missing date
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={'project_id': 'test-id'}
        )
        assert response.status_code == 400
        
        # Missing project_id
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={'date': '2023-01-01'}
        )
        assert response.status_code == 400

    def test_daily_feeding_report_invalid_date_format(self, authenticated_client, test_project):
        """Test daily feeding report with invalid date format"""
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': 'invalid-date'
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_weekly_feeding_report_success(self, authenticated_client, test_feeding_logs, test_project):
        """Test successful weekly feeding report retrieval"""
        week_start = date.today() - timedelta(days=6)
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/weekly',
            query_string={
                'project_id': test_project.id,
                'week_start': week_start.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check response structure (should have dogs and summary data)
        assert 'dogs' in data or 'rows' in data
        assert 'week_start' in data
        assert 'week_end' in data

    def test_weekly_feeding_report_with_pagination(self, authenticated_client, test_feeding_logs, test_project):
        """Test weekly feeding report with pagination"""
        week_start = date.today() - timedelta(days=6)
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/weekly',
            query_string={
                'project_id': test_project.id,
                'week_start': week_start.strftime('%Y-%m-%d'),
                'page': 1,
                'per_page': 50
            }
        )
        
        assert response.status_code == 200

    def test_unauthenticated_access_denied(self, client, test_project):
        """Test that unauthenticated users cannot access feeding reports"""
        response = client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 401

    def test_project_access_denied(self, authenticated_client, test_project):
        """Test access denied for unauthorized project"""
        # Using a different project ID that user doesn't have access to
        fake_project_id = 'fake-project-id'
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': fake_project_id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data

    def test_daily_report_performance_optimization(self, authenticated_client, test_feeding_logs, test_project):
        """Test that API handles pagination limits correctly"""
        target_date = date.today()
        
        # Test maximum per_page limit
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d'),
                'per_page': 500  # Should be capped at 100
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['pagination']['per_page'] <= 100

    def test_daily_report_kpi_calculations(self, authenticated_client, test_feeding_logs, test_project):
        """Test that KPI calculations are accurate"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        kpis = data['kpis']
        
        # Basic sanity checks on KPI calculations
        assert kpis['total_meals'] >= 0
        assert kpis['total_dogs'] >= 0
        assert kpis['total_grams'] >= 0
        assert kpis['total_water_ml'] >= 0
        assert kpis['fresh_meals'] >= 0
        assert kpis['dry_meals'] >= 0
        
        # Meal type totals should make sense
        assert isinstance(kpis['by_meal_type'], dict)
        assert 'طازج' in kpis['by_meal_type']
        assert 'مجفف' in kpis['by_meal_type']
        assert 'مختلط' in kpis['by_meal_type']

    def test_response_format_compatibility(self, authenticated_client, test_feeding_logs, test_project):
        """Test that response format maintains backward compatibility"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check that legacy KPI keys are still present
        kpis = data['kpis']
        legacy_keys = ['total_grams', 'by_meal_type', 'bcs_dist']
        for key in legacy_keys:
            assert key in kpis, f"Legacy KPI key '{key}' missing from response"

    def test_arabic_content_handling(self, authenticated_client, test_feeding_logs, test_project):
        """Test that Arabic content is properly handled in responses"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check Arabic field names in rows
        if data['rows']:
            row = data['rows'][0]
            arabic_fields = ['نوع_الوجبة', 'اسم_الوجبة', 'كمية_الوجبة_غرام', 
                           'ماء_الشرب_مل', 'طريقة_التحضير', 'كتلة_الجسد_BCS', 'ملاحظات']
            for field in arabic_fields:
                assert field in row

        # Check Arabic meal types in KPIs
        by_meal_type = data['kpis']['by_meal_type']
        arabic_meal_types = ['طازج', 'مجفف', 'مختلط']
        for meal_type in arabic_meal_types:
            assert meal_type in by_meal_type