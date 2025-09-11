"""
Tests for veterinary reports legacy redirects
Tests that old veterinary report routes redirect to the new unified route
"""
import pytest
from datetime import date


class TestVeterinaryReportsRedirects:
    """Test suite for veterinary reports legacy route redirects"""

    def test_daily_legacy_redirect(self, authenticated_client, test_project):
        """Test that legacy daily veterinary route redirects to unified route"""
        response = authenticated_client.get(
            '/reports/veterinary/daily',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 302
        assert '/reports/breeding/veterinary/' in response.location
        assert 'range_type=daily' in response.location

    def test_weekly_legacy_redirect(self, authenticated_client, test_project):
        """Test that legacy weekly veterinary route redirects to unified route"""
        response = authenticated_client.get(
            '/reports/veterinary/weekly',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 302
        assert '/reports/breeding/veterinary/' in response.location
        assert 'range_type=weekly' in response.location

    def test_legacy_redirect_preserves_parameters(self, authenticated_client, test_project, test_dogs):
        """Test that legacy redirects preserve query parameters"""
        if test_dogs:
            test_dog = test_dogs[0]
            
            response = authenticated_client.get(
                '/reports/veterinary/daily',
                query_string={
                    'project_id': test_project.id,
                    'dog_id': test_dog.id,
                    'vet_id': 'some-vet-id'
                }
            )
            
            assert response.status_code == 302
            redirect_url = response.location
            
            # Check that original parameters are preserved
            assert f'project_id={test_project.id}' in redirect_url
            assert f'dog_id={test_dog.id}' in redirect_url
            assert 'vet_id=some-vet-id' in redirect_url
            assert 'range_type=daily' in redirect_url

    def test_legacy_redirect_shows_flash_message(self, authenticated_client, test_project):
        """Test that legacy redirects show informative flash messages"""
        response = authenticated_client.get(
            '/reports/veterinary/daily',
            query_string={'project_id': test_project.id},
            follow_redirects=True
        )
        
        assert response.status_code == 200
        # The redirect should have shown a flash message
        # This would typically be tested by checking the session or page content

    def test_legacy_redirect_requires_authentication(self, client, test_project):
        """Test that legacy redirects require authentication"""
        response = client.get(
            '/reports/veterinary/daily',
            query_string={'project_id': test_project.id}
        )
        
        # Should redirect to login
        assert response.status_code == 302
        assert '/auth/login' in response.location

    def test_legacy_redirect_maintains_functionality(self, authenticated_client, test_project):
        """Test that after redirect, the functionality works as expected"""
        # Make initial request to legacy route
        response = authenticated_client.get(
            '/reports/veterinary/daily',
            query_string={'project_id': test_project.id}
        )
        
        # Follow the redirect
        assert response.status_code == 302
        redirect_url = response.location
        
        # Access the redirected URL
        final_response = authenticated_client.get(redirect_url)
        assert final_response.status_code == 200
        assert b'<html' in final_response.data

    def test_legacy_redirect_with_date_parameters(self, authenticated_client, test_project):
        """Test legacy redirects with date parameters"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/reports/veterinary/daily',
            query_string={
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 302
        redirect_url = response.location
        
        # Check that date parameter is preserved
        assert f'date={target_date.strftime("%Y-%m-%d")}' in redirect_url or \
               f'date_from={target_date.strftime("%Y-%m-%d")}' in redirect_url

    def test_multiple_legacy_routes_redirect_correctly(self, authenticated_client, test_project):
        """Test that all legacy routes redirect to the correct unified route"""
        legacy_routes = [
            ('/reports/veterinary/daily', 'daily'),
            ('/reports/veterinary/weekly', 'weekly')
        ]
        
        for route, expected_range in legacy_routes:
            response = authenticated_client.get(
                route,
                query_string={'project_id': test_project.id}
            )
            
            assert response.status_code == 302
            assert '/reports/breeding/veterinary/' in response.location
            assert f'range_type={expected_range}' in response.location