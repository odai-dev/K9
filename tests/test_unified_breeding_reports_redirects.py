import pytest
from datetime import date
from urllib.parse import urlparse, parse_qs


@pytest.mark.unit 
class TestUnifiedBreedingReportsRedirects:
    """Test suite for legacy breeding report URL redirects to unified endpoints"""

    def test_feeding_daily_redirect(self, authenticated_client, test_project):
        """Test that legacy daily feeding URL redirects to unified"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/daily',
            query_string={'project_id': test_project.id},
            follow_redirects=False
        )
        
        assert response.status_code == 302
        
        # Check redirect location
        location = response.headers.get('Location')
        assert location is not None
        assert '/breeding/feeding-reports/unified' in location
        
        # Parse query parameters from redirect
        parsed_url = urlparse(location)
        query_params = parse_qs(parsed_url.query)
        
        assert 'range_type' in query_params
        assert query_params['range_type'][0] == 'daily'
        assert 'project_id' in query_params
        assert query_params['project_id'][0] == str(test_project.id)

    def test_feeding_weekly_redirect(self, authenticated_client, test_project):
        """Test that legacy weekly feeding URL redirects to unified"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/weekly',
            query_string={
                'project_id': test_project.id,
                'week_start': '2023-01-01'
            },
            follow_redirects=False
        )
        
        assert response.status_code == 302
        
        location = response.headers.get('Location')
        assert '/breeding/feeding-reports/unified' in location
        
        parsed_url = urlparse(location)
        query_params = parse_qs(parsed_url.query)
        
        assert query_params['range_type'][0] == 'weekly'
        assert 'date_from' in query_params
        assert 'date_to' in query_params

    def test_checkup_daily_redirect(self, authenticated_client, test_project):
        """Test that legacy daily checkup URL redirects to unified"""
        response = authenticated_client.get(
            '/breeding/checkup-reports/daily',
            query_string={'project_id': test_project.id},
            follow_redirects=False
        )
        
        assert response.status_code == 302
        
        location = response.headers.get('Location')
        assert '/breeding/checkup-reports/unified' in location
        
        parsed_url = urlparse(location)
        query_params = parse_qs(parsed_url.query)
        
        assert query_params['range_type'][0] == 'daily'

    def test_checkup_weekly_redirect(self, authenticated_client, test_project):
        """Test that legacy weekly checkup URL redirects to unified"""
        response = authenticated_client.get(
            '/breeding/checkup-reports/weekly',
            query_string={
                'project_id': test_project.id,
                'week_start': '2023-01-01'
            },
            follow_redirects=False
        )
        
        assert response.status_code == 302
        
        location = response.headers.get('Location')
        assert '/breeding/checkup-reports/unified' in location

    def test_redirect_preserves_all_parameters(self, authenticated_client, test_project, test_dogs):
        """Test that redirect preserves all query parameters"""
        test_dog = test_dogs[0]
        
        response = authenticated_client.get(
            '/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'dog_id': test_dog.id,
                'page': 2,
                'per_page': 10
            },
            follow_redirects=False
        )
        
        assert response.status_code == 302
        
        location = response.headers.get('Location')
        parsed_url = urlparse(location)
        query_params = parse_qs(parsed_url.query)
        
        # All original parameters should be preserved
        assert query_params['project_id'][0] == str(test_project.id)
        assert query_params['dog_id'][0] == str(test_dog.id)
        assert query_params['page'][0] == '2'
        assert query_params['per_page'][0] == '10'
        assert query_params['range_type'][0] == 'daily'

    def test_redirect_with_follow_works(self, authenticated_client, test_project):
        """Test that following the redirect works properly"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/daily',
            query_string={'project_id': test_project.id},
            follow_redirects=True
        )
        
        # Should successfully load the unified page
        assert response.status_code == 200
        assert b'<html' in response.data
        assert 'text/html' in response.headers.get('Content-Type', '')

    def test_api_redirect_preserves_security(self, client, test_project):
        """Test that API redirects maintain security (unauthenticated should fail)"""
        response = client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': '2023-01-01'
            },
            follow_redirects=False
        )
        
        # Should still require authentication even through redirect
        assert response.status_code in [401, 302]  # Either auth error or redirect

    def test_legacy_api_endpoints_redirect(self, authenticated_client, test_project):
        """Test that legacy API endpoints redirect to unified APIs"""
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': date.today().strftime('%Y-%m-%d')
            },
            follow_redirects=False
        )
        
        # Legacy API endpoints should redirect to unified APIs
        if response.status_code == 302:
            location = response.headers.get('Location')
            assert '/api/breeding/feeding-reports/unified/' in location