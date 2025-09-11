"""
Integration tests for veterinary reports
Tests the complete workflow from UI to API to data
"""
import json
import pytest
from datetime import date, timedelta


class TestVeterinaryReportsIntegration:
    """Test suite for veterinary reports integration workflow"""

    def test_complete_unified_report_workflow(self, authenticated_client, test_veterinary_visits, test_project, test_dogs):
        """Test complete workflow from route to API to data display"""
        target_date = date.today()
        
        # Step 1: Access the unified veterinary report page
        page_response = authenticated_client.get(
            '/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily'
            }
        )
        assert page_response.status_code == 200
        assert b'<html' in page_response.data
        
        # Step 2: Fetch data via API
        api_response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        assert api_response.status_code == 200
        
        # Step 3: Verify data consistency
        data = json.loads(api_response.data)
        assert data['success'] is True
        
        # Step 4: Test with dog filter
        if test_dogs:
            test_dog = test_dogs[0]
            filtered_response = authenticated_client.get(
                '/api/reports/breeding/veterinary/',
                query_string={
                    'project_id': test_project.id,
                    'range_type': 'daily',
                    'date_from': target_date.strftime('%Y-%m-%d'),
                    'date_to': target_date.strftime('%Y-%m-%d'),
                    'dog_id': test_dog.id
                }
            )
            assert filtered_response.status_code == 200
            filtered_data = json.loads(filtered_response.data)
            
            # All rows should be for the specified dog
            for row in filtered_data['rows']:
                assert row['dog_id'] == str(test_dog.id)

    def test_legacy_route_workflow(self, authenticated_client, test_project):
        """Test that legacy routes redirect properly and maintain functionality"""
        # Test daily legacy route redirect
        response = authenticated_client.get(
            '/reports/veterinary/daily',
            query_string={'project_id': test_project.id}
        )
        assert response.status_code == 302
        
        # Follow redirect
        redirect_url = response.location
        redirect_response = authenticated_client.get(redirect_url)
        assert redirect_response.status_code == 200
        assert b'<html' in redirect_response.data
        
        # Test weekly legacy route redirect
        response = authenticated_client.get(
            '/reports/veterinary/weekly',
            query_string={'project_id': test_project.id}
        )
        assert response.status_code == 302
        
        # Follow redirect
        redirect_url = response.location
        redirect_response = authenticated_client.get(redirect_url)
        assert redirect_response.status_code == 200

    def test_pdf_export_workflow(self, authenticated_client, test_veterinary_visits, test_project):
        """Test complete PDF export workflow"""
        target_date = date.today()
        
        # Step 1: Get report data
        data_response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        assert data_response.status_code == 200
        
        # Step 2: Export to PDF
        pdf_response = authenticated_client.get(
            '/api/reports/breeding/veterinary/export',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d'),
                'format': 'pdf'
            }
        )
        assert pdf_response.status_code == 200
        assert pdf_response.headers['Content-Type'] == 'application/pdf'
        assert 'attachment' in pdf_response.headers['Content-Disposition']

    def test_range_selector_workflow(self, authenticated_client, test_veterinary_visits, test_project):
        """Test all range selector options work correctly"""
        today = date.today()
        
        # Test daily range
        daily_response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': today.strftime('%Y-%m-%d'),
                'date_to': today.strftime('%Y-%m-%d')
            }
        )
        assert daily_response.status_code == 200
        daily_data = json.loads(daily_response.data)
        assert daily_data['range_info']['range_type'] == 'daily'
        
        # Test weekly range
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        weekly_response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'weekly',
                'date_from': week_start.strftime('%Y-%m-%d'),
                'date_to': week_end.strftime('%Y-%m-%d')
            }
        )
        assert weekly_response.status_code == 200
        weekly_data = json.loads(weekly_response.data)
        assert weekly_data['range_info']['range_type'] == 'weekly'
        
        # Test monthly range
        month_start = today.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        monthly_response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'monthly',
                'date_from': month_start.strftime('%Y-%m-%d'),
                'date_to': month_end.strftime('%Y-%m-%d')
            }
        )
        assert monthly_response.status_code == 200
        monthly_data = json.loads(monthly_response.data)
        assert monthly_data['range_info']['range_type'] == 'monthly'
        
        # Test custom range
        start_date = today - timedelta(days=10)
        end_date = today - timedelta(days=1)
        custom_response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'custom',
                'date_from': start_date.strftime('%Y-%m-%d'),
                'date_to': end_date.strftime('%Y-%m-%d')
            }
        )
        assert custom_response.status_code == 200
        custom_data = json.loads(custom_response.data)
        assert custom_data['range_info']['range_type'] == 'custom'

    def test_kpis_toggle_workflow(self, authenticated_client, test_veterinary_visits, test_project):
        """Test KPIs toggle functionality"""
        target_date = date.today()
        
        # Test with KPIs enabled
        with_kpis_response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d'),
                'show_kpis': '1'
            }
        )
        assert with_kpis_response.status_code == 200
        with_kpis_data = json.loads(with_kpis_response.data)
        assert with_kpis_data['kpis'] is not None
        
        # Test with KPIs disabled
        without_kpis_response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d'),
                'show_kpis': '0'
            }
        )
        assert without_kpis_response.status_code == 200
        without_kpis_data = json.loads(without_kpis_response.data)
        assert without_kpis_data['kpis'] is None

    def test_pagination_workflow(self, authenticated_client, test_veterinary_visits, test_project):
        """Test pagination functionality across multiple pages"""
        target_date = date.today()
        
        # Get first page
        first_page_response = authenticated_client.get(
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
        assert first_page_response.status_code == 200
        first_page_data = json.loads(first_page_response.data)
        
        # Check pagination structure
        pagination = first_page_data['pagination']
        assert pagination['page'] == 1
        assert pagination['per_page'] == 2
        
        # If there are more pages, test second page
        if pagination['has_next']:
            second_page_response = authenticated_client.get(
                '/api/reports/breeding/veterinary/',
                query_string={
                    'project_id': test_project.id,
                    'range_type': 'daily',
                    'date_from': target_date.strftime('%Y-%m-%d'),
                    'date_to': target_date.strftime('%Y-%m-%d'),
                    'page': 2,
                    'per_page': 2
                }
            )
            assert second_page_response.status_code == 200
            second_page_data = json.loads(second_page_response.data)
            assert second_page_data['pagination']['page'] == 2

    def test_error_handling_workflow(self, authenticated_client):
        """Test error handling across the entire workflow"""
        target_date = date.today()
        
        # Test invalid project ID
        invalid_project_response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': '00000000-0000-0000-0000-000000000000',
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        assert invalid_project_response.status_code == 403
        
        # Test invalid date range
        invalid_date_response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': '11111111-1111-1111-1111-111111111111',
                'range_type': 'custom',
                'date_from': '2023-12-31',
                'date_to': '2023-01-01'  # End before start
            }
        )
        assert invalid_date_response.status_code == 400

    def test_performance_workflow(self, authenticated_client, test_veterinary_visits, test_project):
        """Test that the workflow performs within acceptable limits"""
        import time
        target_date = date.today()
        
        # Test response time for data retrieval
        start_time = time.time()
        response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        # Response should be fast (under 2 seconds for most cases)
        assert response_time < 2.0
        
        # Test caching headers are present
        assert 'Cache-Control' in response.headers