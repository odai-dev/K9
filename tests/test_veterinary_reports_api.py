"""
Tests for veterinary reports API endpoints
Tests the unified veterinary reports with range selectors and API functionality
"""
import json
import pytest
from datetime import date, timedelta
from k9.models.models import VeterinaryVisit, VisitType


class TestVeterinaryReportsAPI:
    """Test suite for veterinary reports API endpoints"""

    def test_unified_veterinary_daily_range(self, authenticated_client, test_veterinary_visits, test_project):
        """Test unified veterinary report with daily range"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
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

    def test_unified_veterinary_weekly_range(self, authenticated_client, test_veterinary_visits, test_project):
        """Test unified veterinary report with weekly range"""
        target_date = date.today()
        week_start = target_date - timedelta(days=target_date.weekday())
        week_end = week_start + timedelta(days=6)
        
        response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
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

    def test_unified_veterinary_monthly_range(self, authenticated_client, test_veterinary_visits, test_project):
        """Test unified veterinary report with monthly range"""
        target_date = date.today()
        month_start = target_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
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

    def test_unified_veterinary_custom_range(self, authenticated_client, test_veterinary_visits, test_project):
        """Test unified veterinary report with custom range"""
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
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

    def test_veterinary_report_with_dog_filter(self, authenticated_client, test_veterinary_visits, test_project, test_dogs):
        """Test veterinary report filtered by specific dog"""
        target_date = date.today()
        test_dog = test_dogs[0]
        
        response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
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
        
        # All rows should be for the specified dog
        for row in data['rows']:
            assert row['dog_id'] == str(test_dog.id)

    def test_veterinary_report_kpis_calculation(self, authenticated_client, test_veterinary_visits, test_project):
        """Test veterinary report KPIs calculation"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d'),
                'show_kpis': '1'
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check KPIs structure
        kpis = data['kpis']
        expected_kpi_keys = ['total_visits', 'total_dogs', 'total_vets', 'total_cost',
                           'total_medications', 'by_visit_type', 'avg_duration']
        for key in expected_kpi_keys:
            assert key in kpis

    def test_veterinary_report_without_kpis(self, authenticated_client, test_veterinary_visits, test_project):
        """Test veterinary report without KPIs to improve performance"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d'),
                'show_kpis': '0'
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # KPIs should be None when disabled
        assert data['kpis'] is None

    def test_veterinary_report_pagination(self, authenticated_client, test_veterinary_visits, test_project):
        """Test veterinary report with pagination parameters"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d'),
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

    def test_veterinary_report_invalid_date_range(self, authenticated_client, test_project):
        """Test veterinary report with invalid date range"""
        response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'custom',
                'date_from': '2023-12-31',
                'date_to': '2023-01-01'  # End before start
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'errors' in data

    def test_veterinary_pdf_export(self, authenticated_client, test_veterinary_visits, test_project):
        """Test veterinary report PDF export"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/reports/breeding/veterinary/export',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d'),
                'format': 'pdf'
            }
        )
        
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/pdf'
        assert 'attachment' in response.headers['Content-Disposition']

    def test_veterinary_report_cache_headers(self, authenticated_client, test_veterinary_visits, test_project):
        """Test that veterinary reports include proper cache control headers"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        # Check for cache control headers to prevent stale data
        assert 'Cache-Control' in response.headers
        assert 'no-cache' in response.headers['Cache-Control']

    def test_veterinary_report_error_handling(self, authenticated_client):
        """Test veterinary report error handling for missing project"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': '00000000-0000-0000-0000-000000000000',  # Non-existent project
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
        assert 'صلاحية' in data['error']  # Arabic error message