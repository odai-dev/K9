import pytest
from datetime import date


@pytest.mark.unit
class TestUnifiedBreedingReportsRoutes:
    """Test suite for unified breeding reports route rendering"""

    def test_unified_feeding_route_renders(self, authenticated_client, test_project):
        """Test that unified feeding report route renders successfully"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/unified',
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
        
    def test_unified_checkup_route_renders(self, authenticated_client, test_project):
        """Test that unified checkup report route renders successfully"""
        response = authenticated_client.get(
            '/breeding/checkup-reports/unified',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily'
            }
        )
        
        assert response.status_code == 200
        assert b'<html' in response.data
        assert 'text/html' in response.headers.get('Content-Type', '')

    def test_unified_feeding_with_different_ranges(self, authenticated_client, test_project):
        """Test unified feeding route with different range types"""
        range_types = ['daily', 'weekly', 'monthly', 'custom']
        
        for range_type in range_types:
            response = authenticated_client.get(
                '/breeding/feeding-reports/unified',
                query_string={
                    'project_id': test_project.id,
                    'range_type': range_type
                }
            )
            
            assert response.status_code == 200
            assert b'<html' in response.data

    def test_unified_checkup_with_different_ranges(self, authenticated_client, test_project):
        """Test unified checkup route with different range types"""
        range_types = ['daily', 'weekly', 'monthly', 'custom']
        
        for range_type in range_types:
            response = authenticated_client.get(
                '/breeding/checkup-reports/unified',
                query_string={
                    'project_id': test_project.id,
                    'range_type': range_type
                }
            )
            
            assert response.status_code == 200
            assert b'<html' in response.data

    def test_unified_routes_require_authentication(self, client, test_project):
        """Test that unified routes require authentication"""
        # Test feeding route
        response = client.get(
            '/breeding/feeding-reports/unified',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily'
            }
        )
        
        # Should redirect to login or return 401
        assert response.status_code in [302, 401]
        
        # Test checkup route
        response = client.get(
            '/breeding/checkup-reports/unified',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily'
            }
        )
        
        assert response.status_code in [302, 401]

    def test_unified_routes_with_missing_project_id(self, authenticated_client):
        """Test unified routes behavior with missing project_id"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/unified',
            query_string={'range_type': 'daily'}
        )
        
        # Should handle missing project_id gracefully
        # Either redirect to project selection or show error
        assert response.status_code in [200, 302, 400]

    def test_unified_routes_with_invalid_range_type(self, authenticated_client, test_project):
        """Test unified routes with invalid range_type parameter"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/unified',
            query_string={
                'project_id': test_project.id,
                'range_type': 'invalid_range'
            }
        )
        
        # Should handle invalid range type gracefully
        assert response.status_code in [200, 400]
        
    def test_unified_routes_preserve_query_parameters(self, authenticated_client, test_project, test_dogs):
        """Test that unified routes preserve query parameters"""
        test_dog = test_dogs[0]
        
        response = authenticated_client.get(
            '/breeding/feeding-reports/unified',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'dog_id': test_dog.id,
                'date_from': '2023-01-01',
                'date_to': '2023-01-31'
            }
        )
        
        assert response.status_code == 200
        
        # Check that parameters are available in the response
        response_text = response.data.decode('utf-8')
        assert str(test_project.id) in response_text
        assert str(test_dog.id) in response_text

    def test_unified_feeding_route_includes_javascript(self, authenticated_client, test_project):
        """Test that unified feeding route includes required JavaScript"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/unified',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily'
            }
        )
        
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        
        # Should include JavaScript for unified functionality
        assert 'loadUnifiedFeedingData' in response_text or 'unified' in response_text.lower()

    def test_unified_checkup_route_includes_javascript(self, authenticated_client, test_project):
        """Test that unified checkup route includes required JavaScript"""
        response = authenticated_client.get(
            '/breeding/checkup-reports/unified',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily'
            }
        )
        
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        
        # Should include JavaScript for unified functionality
        assert 'loadUnifiedCheckupData' in response_text or 'unified' in response_text.lower()

    def test_unified_routes_rtl_layout(self, authenticated_client, test_project):
        """Test that unified routes use proper RTL layout"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/unified',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily'
            }
        )
        
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        
        # Should include RTL styling
        assert 'dir="rtl"' in response_text or 'rtl' in response_text.lower()
        
        # Should include Arabic text
        assert 'تقرير' in response_text or 'البيانات' in response_text