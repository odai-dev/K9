import pytest
import json
from datetime import date

from k9.models.models import User, SubPermission, PermissionType


@pytest.mark.unit
class TestUnifiedBreedingReportsPermissions:
    """Test suite for unified breeding reports permissions"""

    def test_feeding_unified_view_permission(self, authenticated_client, test_project, test_feeding_logs):
        """Test that feeding:view permission works for unified endpoints"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        # Should work with proper permissions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_feeding_unified_export_permission(self, authenticated_client, test_project, test_feeding_logs):
        """Test that feeding:export permission works for unified PDF export"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/unified/export-pdf',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        # Should work with proper permissions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_checkup_unified_view_permission(self, authenticated_client, test_project):
        """Test that checkup:view permission works for unified endpoints"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/breeding/checkup-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        # Should work with proper permissions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_checkup_unified_export_permission(self, authenticated_client, test_project):
        """Test that checkup:export permission works for unified PDF export"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/breeding/checkup-reports/unified/export-pdf',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        # Should work with proper permissions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_unauthenticated_access_denied(self, client, test_project):
        """Test that unauthenticated users cannot access unified endpoints"""
        target_date = date.today()
        
        # Test feeding data endpoint
        response = client.get(
            '/api/breeding/feeding-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 401
        
        # Test feeding PDF export
        response = client.get(
            '/api/breeding/feeding-reports/unified/export-pdf',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 401
        
        # Test checkup data endpoint
        response = client.get(
            '/api/breeding/checkup-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 401
        
        # Test checkup PDF export
        response = client.get(
            '/api/breeding/checkup-reports/unified/export-pdf',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 401

    def test_unauthorized_user_access_denied(self, client, unauthorized_user, test_project, db_session):
        """Test that users without proper permissions are denied access"""
        # Authenticate as user without permissions
        with client.session_transaction() as sess:
            sess['_user_id'] = str(unauthorized_user.id)
            sess['_fresh'] = True

        target_date = date.today()
        
        # Test feeding endpoint - should be denied without proper permission
        response = client.get(
            '/api/breeding/feeding-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        # Should be denied access
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data

    def test_project_manager_access_own_project(self, client, project_manager_user, test_project, db_session):
        """Test that PROJECT_MANAGER can access unified reports for their assigned project"""
        # Authenticate as project manager
        with client.session_transaction() as sess:
            sess['_user_id'] = str(project_manager_user.id)
            sess['_fresh'] = True

        # Grant feeding view permission for this project
        feeding_permission = SubPermission(
            user_id=project_manager_user.id,
            section='Reports',
            subsection='Feeding',
            permission_type=PermissionType.VIEW,
            project_id=test_project.id,
            is_granted=True
        )
        db_session.add(feeding_permission)
        
        # Grant checkup view permission for this project
        checkup_permission = SubPermission(
            user_id=project_manager_user.id,
            section='Reports',
            subsection='Checkup',
            permission_type=PermissionType.VIEW,
            project_id=test_project.id,
            is_granted=True
        )
        db_session.add(checkup_permission)
        db_session.commit()

        target_date = date.today()
        
        # Test feeding access
        response = client.get(
            '/api/breeding/feeding-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Test checkup access
        response = client.get(
            '/api/breeding/checkup-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_project_manager_denied_other_project(self, client, project_manager_user, test_project, db_session):
        """Test that PROJECT_MANAGER cannot access reports for projects they're not assigned to"""
        # Create another project
        from k9.models.models import Project, ProjectStatus
        
        other_project = Project(
            name='Other Test Project',
            code='OTHER',
            status=ProjectStatus.ACTIVE,
            description='Other project for testing'
        )
        db_session.add(other_project)
        db_session.commit()
        
        # Authenticate as project manager
        with client.session_transaction() as sess:
            sess['_user_id'] = str(project_manager_user.id)
            sess['_fresh'] = True

        target_date = date.today()
        
        # Try to access other project's reports - should be denied
        response = client.get(
            '/api/breeding/feeding-reports/unified/data',
            query_string={
                'project_id': other_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 403

    def test_general_admin_access_all_projects(self, authenticated_client, test_project):
        """Test that GENERAL_ADMIN can access unified reports for any project"""
        target_date = date.today()
        
        # GENERAL_ADMIN should have access to all reports
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/unified/data',
            query_string={
                'project_id': test_project.id,
                'range_type': 'daily',
                'date_from': target_date.strftime('%Y-%m-%d'),
                'date_to': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True