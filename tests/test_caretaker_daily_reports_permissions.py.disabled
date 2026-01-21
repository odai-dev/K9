import pytest
import json
from datetime import date
from flask import url_for
from unittest.mock import patch
from k9.models.models import SubPermission, PermissionType, UserRole


@pytest.mark.unit
class TestCaretakerDailyReportsPermissions:
    """Test suite for caretaker daily reports permission system"""

    def test_project_manager_has_view_access(self, authenticated_client, test_project):
        """Test that PROJECT_MANAGER users can view caretaker daily reports"""
        response = authenticated_client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        # PROJECT_MANAGER should have explicit access
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_project_manager_has_export_access(self, authenticated_client, test_project):
        """Test that PROJECT_MANAGER users can export caretaker daily reports to PDF"""
        with patch('k9.api.caretaker_daily_report_api._generate_caretaker_daily_pdf') as mock_pdf:
            mock_pdf.return_value = b'fake-pdf-content'
            
            response = authenticated_client.get(
                '/api/reports/breeding/caretaker-daily/unified/export.pdf',
                query_string={
                    'range_type': 'daily',
                    'project_id': test_project.id,
                    'date': date.today().strftime('%Y-%m-%d')
                }
            )
            assert response.status_code == 200
            assert response.content_type == 'application/pdf'

    def test_general_admin_has_access(self, client, admin_user, test_project):
        """Test that GENERAL_ADMIN users can access caretaker daily reports"""
        # Authenticate as admin
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        # Test view access
        response = client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        assert response.status_code != 403

        # Test export access
        with patch('k9.api.caretaker_daily_report_api._generate_caretaker_daily_pdf') as mock_pdf:
            mock_pdf.return_value = b'fake-pdf-content'
            
            response = client.get(
                '/api/reports/breeding/caretaker-daily/unified/export.pdf',
                query_string={
                    'range_type': 'daily',
                    'project_id': test_project.id,
                    'date': date.today().strftime('%Y-%m-%d')
                }
            )
            assert response.status_code != 403

    def test_unauthenticated_user_denied(self, client, test_project):
        """Test that unauthenticated users are denied access"""
        # Test view access
        response = client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 401

        # Test export access
        response = client.get(
            '/api/reports/breeding/caretaker-daily/unified/export.pdf',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 401

    def test_user_without_permission_denied(self, client, unauthorized_user, test_project, db_session):
        """Test that users without caretaker daily report permissions are denied"""
        # Authenticate as user without permissions
        with client.session_transaction() as sess:
            sess['_user_id'] = str(unauthorized_user.id)
            sess['_fresh'] = True

        # Create explicit denial SubPermission for view access
        denial_permission = SubPermission(
            user_id=unauthorized_user.id,
            section='Reports',
            subsection='Caretaker Daily',
            permission_type=PermissionType.VIEW,
            project_id=test_project.id,
            is_granted=False
        )
        db_session.add(denial_permission)
        db_session.commit()

        # Test view access denied
        response = client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 403

        # Test export access denied
        response = client.get(
            '/api/reports/breeding/caretaker-daily/unified/export.pdf',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 403

    def test_specific_export_permission_required(self, client, unauthorized_user, test_project, db_session):
        """Test that export requires specific export permission"""
        # Authenticate as user
        with client.session_transaction() as sess:
            sess['_user_id'] = str(unauthorized_user.id)
            sess['_fresh'] = True

        # Grant VIEW permission but not EXPORT
        view_permission = SubPermission(
            user_id=unauthorized_user.id,
            section='Reports',
            subsection='Caretaker Daily',
            permission_type=PermissionType.VIEW,
            project_id=test_project.id,
            is_granted=True
        )
        
        # Explicitly deny EXPORT permission
        export_denial = SubPermission(
            user_id=unauthorized_user.id,
            section='Reports',
            subsection='Caretaker Daily',
            permission_type=PermissionType.EXPORT,
            project_id=test_project.id,
            is_granted=False
        )
        
        db_session.add(view_permission)
        db_session.add(export_denial)
        db_session.commit()

        # View should work
        response = client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 200

        # Export should be denied
        response = client.get(
            '/api/reports/breeding/caretaker-daily/unified/export.pdf',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 403

    def test_project_access_validation(self, authenticated_client):
        """Test that users can only access projects they have permission for"""
        fake_project_id = 'fake-project-12345'
        
        response = authenticated_client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'daily',
                'project_id': fake_project_id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
        # Should contain Arabic error message
        assert any(arabic_char in data['error'] for arabic_char in 'صلاحية')

    def test_permission_decorator_functionality(self, client, unauthorized_user, test_project, db_session):
        """Test that permission decorators work correctly for caretaker reports"""
        # Authenticate as user without permissions
        with client.session_transaction() as sess:
            sess['_user_id'] = str(unauthorized_user.id)
            sess['_fresh'] = True

        # Create explicit denial SubPermission
        denial_permission = SubPermission(
            user_id=unauthorized_user.id,
            section='Reports',
            subsection='Caretaker Daily',
            permission_type=PermissionType.VIEW,
            project_id=test_project.id,
            is_granted=False
        )
        db_session.add(denial_permission)
        db_session.commit()

        # Test access should be denied
        response = client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 403

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

        response = client.get('/reports/breeding/caretaker-daily/')
        assert response.status_code != 403

        # Test GENERAL_ADMIN access
        with client.session_transaction() as sess:
            sess['_user_id'] = str(general_admin.id)
            sess['_fresh'] = True

        response = client.get('/reports/breeding/caretaker-daily/')
        assert response.status_code != 403

    def test_route_permission_consistency(self, authenticated_client, test_project):
        """Test that caretaker report routes have consistent permission requirements"""
        routes_to_test = [
            '/reports/breeding/caretaker-daily/'
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
            '/api/reports/breeding/caretaker-daily/unified'
        ]
        
        for route in api_routes:
            response = authenticated_client.get(
                route,
                query_string={
                    'range_type': 'daily',
                    'project_id': test_project.id,
                    'date': date.today().strftime('%Y-%m-%d')
                }
            )
            # Should not get permission denied
            assert response.status_code != 403

    def test_permission_error_messages_in_arabic(self, client, unauthorized_user, test_project, db_session):
        """Test that permission error messages are in Arabic"""
        # Create explicit denial
        denial = SubPermission(
            user_id=unauthorized_user.id,
            section='Reports',
            subsection='Caretaker Daily',
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
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        
        if response.status_code == 403:
            data = json.loads(response.data)
            # Error message should be in Arabic
            assert any(arabic_char in data.get('error', '') for arabic_char in 'صلاحية')

    def test_backwards_compatibility_permissions(self, authenticated_client, test_project):
        """Test that permissions work with backwards compatibility mode"""
        # The has_permission function should handle "reports.breeding.caretaker_daily.view" permission string
        response = authenticated_client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        
        # Should not fail due to permission mapping issues
        assert response.status_code != 500  # No internal server error
        assert response.status_code != 403  # No permission denied for valid PROJECT_MANAGER

    def test_permission_check_with_has_permission_function(self, authenticated_client, test_project):
        """Test that the has_permission function works correctly for caretaker daily reports"""
        # This tests the permission string: "reports.breeding.caretaker_daily.view"
        response = authenticated_client.get(
            '/reports/breeding/caretaker-daily/',
            query_string={'project_id': test_project.id}
        )
        
        # PROJECT_MANAGER should have access
        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data

    def test_export_permission_check_with_has_permission_function(self, authenticated_client, test_project):
        """Test that the has_permission function works correctly for caretaker daily export"""
        # This tests the permission string: "reports.breeding.caretaker_daily.export"
        with patch('k9.api.caretaker_daily_report_api._generate_caretaker_daily_pdf') as mock_pdf:
            mock_pdf.return_value = b'fake-pdf-content'
            
            response = authenticated_client.get(
                '/api/reports/breeding/caretaker-daily/unified/export.pdf',
                query_string={
                    'range_type': 'daily',
                    'project_id': test_project.id,
                    'date': date.today().strftime('%Y-%m-%d')
                }
            )
            
            # PROJECT_MANAGER should have export access
            assert response.status_code == 200
            assert response.content_type == 'application/pdf'