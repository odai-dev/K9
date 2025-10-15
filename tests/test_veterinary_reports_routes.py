"""
Tests for veterinary reports UI routes
Tests that the unified veterinary reports routes render correctly
"""
import pytest
from datetime import date


class TestVeterinaryReportsRoutes:
    """Test suite for veterinary reports route rendering and functionality"""

    def test_unified_veterinary_route_renders(self, authenticated_client, test_project):
        """Test that unified veterinary report route renders successfully"""
        response = authenticated_client.get(
            '/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily'
            }
        )
        
        assert response.status_code == 200
        assert b'<html' in response.data
        assert 'text/html' in response.headers.get('Content-Type', '')
        
        # Check for unified report elements
        assert b'range-selector' in response.data or 'تحديد النطاق'.encode('utf-8') in response.data

    def test_unified_veterinary_with_different_ranges(self, authenticated_client, test_project):
        """Test unified veterinary route with different range types"""
        range_types = ['daily', 'weekly', 'monthly', 'custom']
        
        for range_type in range_types:
            response = authenticated_client.get(
                '/reports/breeding/veterinary/',
                query_string={
                    'project_id': test_project.id,
                    'range_type': range_type
                }
            )
            
            assert response.status_code == 200
            assert b'<html' in response.data

    def test_veterinary_route_with_filters(self, authenticated_client, test_project, test_dogs):
        """Test veterinary route with various filter parameters"""
        if test_dogs:
            test_dog = test_dogs[0]
            
            response = authenticated_client.get(
                '/reports/breeding/veterinary/',
                query_string={
                    'project_id': test_project.id,
                    'range_type': 'daily',
                    'dog_id': test_dog.id
                }
            )
            
            assert response.status_code == 200
            assert b'<html' in response.data

    def test_veterinary_route_requires_authentication(self, client, test_project):
        """Test that veterinary route requires authentication"""
        response = client.get(
            '/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily'
            }
        )
        
        # Should redirect to login
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_veterinary_route_with_custom_dates(self, authenticated_client, test_project):
        """Test veterinary route with custom date range"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'custom',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        assert b'<html' in response.data

    def test_veterinary_route_arabic_rtl_support(self, authenticated_client, test_project):
        """Test that veterinary route includes proper Arabic RTL support"""
        response = authenticated_client.get(
            '/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily'
            }
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for RTL support
        assert 'dir="rtl"' in content
        assert 'lang="ar"' in content
        
        # Check for Arabic text
        assert 'التقرير البيطري' in content or 'البيطرية' in content

    def test_veterinary_route_includes_necessary_assets(self, authenticated_client, test_project):
        """Test that veterinary route includes necessary CSS and JS assets"""
        response = authenticated_client.get(
            '/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily'
            }
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for Bootstrap CSS (RTL version)
        assert 'bootstrap' in content
        
        # Check for JavaScript files
        assert 'reports_veterinary_unified.js' in content

    def test_veterinary_route_form_elements(self, authenticated_client, test_project):
        """Test that veterinary route includes proper form elements"""
        response = authenticated_client.get(
            '/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily'
            }
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for form elements
        assert 'form' in content
        assert 'select' in content or 'dropdown' in content
        
        # Check for filters
        assert 'project_id' in content
        assert 'range_type' in content

    def test_veterinary_route_pagination_controls(self, authenticated_client, test_project):
        """Test that veterinary route includes pagination controls"""
        response = authenticated_client.get(
            '/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily'
            }
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for pagination elements
        assert 'pagination' in content or 'page' in content

    def test_veterinary_route_export_controls(self, authenticated_client, test_project):
        """Test that veterinary route includes export controls"""
        response = authenticated_client.get(
            '/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily'
            }
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for export functionality
        assert 'export' in content or 'تصدير' in content
        assert 'pdf' in content or 'PDF' in content

    def test_veterinary_route_kpis_toggle(self, authenticated_client, test_project):
        """Test that veterinary route includes KPIs toggle"""
        response = authenticated_client.get(
            '/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily'
            }
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for KPIs toggle
        assert 'kpis' in content or 'KPI' in content or 'مؤشرات' in content

    def test_veterinary_route_error_handling(self, authenticated_client):
        """Test veterinary route error handling for invalid parameters"""
        # Test with missing project_id
        response = authenticated_client.get('/reports/breeding/veterinary/')
        
        # Should handle gracefully (either show error or default behavior)
        assert response.status_code in [200, 400, 403]
        
        # Test with invalid project_id
        response = authenticated_client.get(
            '/reports/breeding/veterinary/',
            query_string={
                'project_id': 'invalid-id',
                'range_type': 'daily'
            }
        )
        
        assert response.status_code in [200, 400, 403]