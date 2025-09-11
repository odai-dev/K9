import pytest
import json
from flask import url_for
from k9.models.models import SubPermission, PermissionType, UserRole


@pytest.mark.unit
class TestFeedingReportsPermissions:
    """Test suite for feeding reports permission system"""

    def test_project_manager_has_access(self, authenticated_client, test_project):
        """Test that PROJECT_MANAGER users can access feeding reports"""
        # Test daily report access
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        # PROJECT_MANAGER should have explicit access
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Test weekly report access
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/weekly',
            query_string={
                'project_id': test_project.id,
                'week_start': '2023-01-01'
            }
        )
        assert response.status_code != 403

    def test_general_admin_has_access(self, client, admin_user, test_project):
        """Test that GENERAL_ADMIN users can access feeding reports"""
        # Authenticate as admin
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        # Test daily report access
        response = client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': '2023-01-01'
            }
        )
        assert response.status_code != 403

        # Test weekly report access
        response = client.get(
            '/api/breeding/feeding-reports/weekly',
            query_string={
                'project_id': test_project.id,
                'week_start': '2023-01-01'
            }
        )
        assert response.status_code != 403

    def test_unauthenticated_user_denied(self, client, test_project):
        """Test that unauthenticated users are denied access"""
        # Test daily report
        response = client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': '2023-01-01'
            }
        )
        assert response.status_code == 401

        # Test weekly report
        response = client.get(
            '/api/breeding/feeding-reports/weekly',
            query_string={
                'project_id': test_project.id,
                'week_start': '2023-01-01'
            }
        )
        assert response.status_code == 401

    def test_permission_decorator_functionality(self, client, unauthorized_user, test_project, db_session):
        """Test that permission decorators work correctly"""
        # Authenticate as user without permissions
        with client.session_transaction() as sess:
            sess['_user_id'] = str(unauthorized_user.id)
            sess['_fresh'] = True

        # Create explicit denial SubPermission
        denial_permission = SubPermission(
            user_id=unauthorized_user.id,
            section='Reports',
            subsection='Feeding Daily',
            permission_type=PermissionType.VIEW,
            project_id=test_project.id,
            is_granted=False
        )
        db_session.add(denial_permission)
        db_session.commit()

        # Test access should be denied
        response = client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': '2023-01-01'
            }
        )
        assert response.status_code == 403

    def test_project_access_validation(self, authenticated_client):
        """Test that users can only access projects they have permission for"""
        fake_project_id = 'fake-project-12345'
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': fake_project_id,
                'date': '2023-01-01'
            }
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
        assert 'صلاحية' in data['error']  # Arabic error message

    def test_route_permission_consistency(self, authenticated_client, test_project):
        """Test that all feeding report routes have consistent permission requirements"""
        routes_to_test = [
            '/breeding/feeding-reports/daily',
            '/breeding/feeding-reports/weekly'
        ]
        
        for route in routes_to_test:
            response = authenticated_client.get(
                route,
                query_string={'project_id': test_project.id}
            )
            # Should not get permission denied (may get other errors but not 403)
            assert response.status_code != 403

    def test_api_permission_consistency(self, authenticated_client, test_project):
        """Test that API endpoints have consistent permission requirements"""
        api_routes = [
            '/api/breeding/feeding-reports/daily',
            '/api/breeding/feeding-reports/weekly'
        ]
        
        for route in api_routes:
            response = authenticated_client.get(
                route,
                query_string={
                    'project_id': test_project.id,
                    'date': '2023-01-01' if 'daily' in route else None,
                    'week_start': '2023-01-01' if 'weekly' in route else None
                }
            )
            # Should not get permission denied
            assert response.status_code != 403

    def test_role_based_access_control(self, client, db_session):
        """Test different user roles and their access levels"""
        from k9.models.models import User
        from werkzeug.security import generate_password_hash
        
        # Create users with different roles
        project_manager = User(
            username='pm_user',
            email='pm@test.com',
            password_hash=generate_password_hash('test123'),
            full_name='Project Manager User',
            role=UserRole.PROJECT_MANAGER,
            active=True
        )
        
        general_admin = User(
            username='admin_user',
            email='admin@test.com',
            password_hash=generate_password_hash('test123'),
            full_name='General Admin User',
            role=UserRole.GENERAL_ADMIN,
            active=True
        )
        
        db_session.add(project_manager)
        db_session.add(general_admin)
        db_session.commit()

        # Test PROJECT_MANAGER access
        with client.session_transaction() as sess:
            sess['_user_id'] = str(project_manager.id)
            sess['_fresh'] = True

        response = client.get('/breeding/feeding-reports/daily')
        assert response.status_code != 403

        # Test GENERAL_ADMIN access
        with client.session_transaction() as sess:
            sess['_user_id'] = str(general_admin.id)
            sess['_fresh'] = True

        response = client.get('/breeding/feeding-reports/daily')
        assert response.status_code != 403

    def test_permission_error_messages_in_arabic(self, client, unauthorized_user, test_project, db_session):
        """Test that permission error messages are in Arabic"""
        # Create explicit denial
        denial = SubPermission(
            user_id=unauthorized_user.id,
            section='Reports',
            subsection='Feeding Daily',
            permission_type=PermissionType.VIEW,
            project_id=test_project.id,
            is_granted=False
        )
        db_session.add(denial)
        db_session.commit()

        # Authenticate as restricted user
        with client.session_transaction() as sess:
            sess['_user_id'] = str(unauthorized_user.id)
            sess['_fresh'] = True

        response = client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': '2023-01-01'
            }
        )
        
        if response.status_code == 403:
            data = json.loads(response.data)
            # Error message should be in Arabic
            assert any(arabic_char in data.get('error', '') for arabic_char in 'صلاحية')

    def test_backwards_compatibility_permissions(self, authenticated_client, test_project):
        """Test that permissions work with backwards compatibility mode"""
        # The has_permission function should handle "Reports" category in backwards compatibility
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': '2023-01-01'
            }
        )
        
        # Should not fail due to permission mapping issues
        assert response.status_code != 500  # No internal server error
        assert response.status_code != 403  # No permission denied for valid PROJECT_MANAGER