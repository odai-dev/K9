"""
Tests for veterinary reports permissions
Tests that only authorized users can access veterinary reports
"""
import json
import pytest
from datetime import date


class TestVeterinaryReportsPermissions:
    """Test suite for veterinary reports permission enforcement"""

    def test_project_manager_has_access(self, authenticated_client, test_project):
        """Test that PROJECT_MANAGER users can access veterinary reports"""
        # Test unified report access
        response = authenticated_client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': date.today().strftime('%Y-%m-%d'),
                'date_to': date.today().strftime('%Y-%m-%d')
            }
        )
        # PROJECT_MANAGER should have explicit access
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Test PDF export access
        response = authenticated_client.get(
            '/api/reports/breeding/veterinary/export',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': date.today().strftime('%Y-%m-%d'),
                'date_to': date.today().strftime('%Y-%m-%d'),
                'format': 'pdf'
            }
        )
        assert response.status_code == 200

    def test_general_admin_has_access(self, client, admin_user, test_project):
        """Test that GENERAL_ADMIN users can access veterinary reports"""
        # Authenticate as admin
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        # Test unified report access
        response = client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': date.today().strftime('%Y-%m-%d'),
                'date_to': date.today().strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 200

        # Test PDF export access
        response = client.get(
            '/api/reports/breeding/veterinary/export',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': date.today().strftime('%Y-%m-%d'),
                'date_to': date.today().strftime('%Y-%m-%d'),
                'format': 'pdf'
            }
        )
        assert response.status_code == 200

    def test_unauthenticated_user_denied(self, client, test_project):
        """Test that unauthenticated users are denied access"""
        # Test unified report
        response = client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': date.today().strftime('%Y-%m-%d'),
                'date_to': date.today().strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 401

        # Test PDF export
        response = client.get(
            '/api/reports/breeding/veterinary/export',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': date.today().strftime('%Y-%m-%d'),
                'date_to': date.today().strftime('%Y-%m-%d'),
                'format': 'pdf'
            }
        )
        assert response.status_code == 401

    def test_project_manager_restricted_to_own_projects(self, client, test_user, test_project, test_other_project):
        """Test that PROJECT_MANAGER users can only access their own projects"""
        # Authenticate as project manager
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True

        # Access to assigned project should work
        response = client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': date.today().strftime('%Y-%m-%d'),
                'date_to': date.today().strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 200

        # Access to other project should be denied
        response = client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_other_project.id,
                'range_type': 'daily',
                'date_from': date.today().strftime('%Y-%m-%d'),
                'date_to': date.today().strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
        assert 'صلاحية' in data['error']  # Arabic error message

    def test_route_permissions(self, authenticated_client, test_project):
        """Test that veterinary report routes require proper permissions"""
        # Test unified veterinary report route
        response = authenticated_client.get(
            '/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily'
            }
        )
        assert response.status_code == 200
        assert b'<html' in response.data

    def test_legacy_route_redirects(self, authenticated_client, test_project):
        """Test that legacy veterinary routes redirect properly"""
        # Test daily legacy route
        response = authenticated_client.get(
            '/reports/veterinary/daily',
            query_string={'project_id': test_project.id}
        )
        assert response.status_code == 302
        assert '/reports/breeding/veterinary/' in response.location

        # Test weekly legacy route
        response = authenticated_client.get(
            '/reports/veterinary/weekly',
            query_string={'project_id': test_project.id}
        )
        assert response.status_code == 302
        assert '/reports/breeding/veterinary/' in response.location

    def test_permission_denied_error_message_in_arabic(self, client, test_user_without_permissions, test_project):
        """Test that permission denied errors are in Arabic"""
        # Authenticate as user without veterinary permissions
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user_without_permissions.id)
            sess['_fresh'] = True

        response = client.get(
            '/api/reports/breeding/veterinary/',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': date.today().strftime('%Y-%m-%d'),
                'date_to': date.today().strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
        assert 'صلاحية' in data['error']  # Arabic error message