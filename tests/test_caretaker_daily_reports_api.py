import pytest
import json
from datetime import date, timedelta
from flask import url_for
from unittest.mock import patch, MagicMock

from k9.models.models import User, CaretakerDailyLog, UserRole


@pytest.mark.unit
class TestCaretakerDailyReportsAPI:
    """Test suite for caretaker daily reports API endpoints"""

    def test_unified_caretaker_daily_report_success(self, authenticated_client, test_caretaker_logs, test_project):
        """Test successful unified caretaker daily report retrieval"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check response structure
        assert data['success'] is True
        assert 'pagination' in data
        assert 'filters' in data
        assert 'kpis' in data
        assert 'rows' in data
        assert 'range_display' in data
        
        # Check pagination metadata
        pagination = data['pagination']
        required_pagination_keys = ['page', 'per_page', 'total', 'pages', 'has_next', 'has_prev']
        for key in required_pagination_keys:
            assert key in pagination
        
        # Check KPIs structure for caretaker activities
        kpis = data['kpis']
        expected_kpi_keys = [
            'total_entries', 'unique_dogs', 'unique_dates',
            'house_tasks', 'dog_tasks'
        ]
        for key in expected_kpi_keys:
            assert key in kpis
            
        # Check house tasks KPIs
        house_tasks = kpis['house_tasks']
        expected_house_keys = [
            'house_clean', 'house_vacuum', 'house_tap_clean', 'house_drain_clean',
            'full_house_clean', 'house_clean_pct', 'house_vacuum_pct'
        ]
        for key in expected_house_keys:
            assert key in house_tasks
            
        # Check dog tasks KPIs  
        dog_tasks = kpis['dog_tasks']
        expected_dog_keys = [
            'dog_clean', 'dog_washed', 'dog_brushed', 'bowls_bucket_clean',
            'full_dog_grooming', 'dog_clean_pct', 'dog_washed_pct'
        ]
        for key in expected_dog_keys:
            assert key in dog_tasks

    def test_unified_caretaker_daily_report_weekly(self, authenticated_client, test_caretaker_logs, test_project):
        """Test unified caretaker daily report with weekly range"""
        week_start = date.today() - timedelta(days=7)
        
        response = authenticated_client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'weekly',
                'project_id': test_project.id,
                'week_start': week_start.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'weekly' in data['range_display'].lower() or 'أسبوع' in data['range_display']

    def test_unified_caretaker_daily_report_monthly(self, authenticated_client, test_caretaker_logs, test_project):
        """Test unified caretaker daily report with monthly range"""
        year_month = date.today().strftime('%Y-%m')
        
        response = authenticated_client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'monthly',
                'project_id': test_project.id,
                'year_month': year_month
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'شهر' in data['range_display'] or 'monthly' in data['range_display'].lower()

    def test_unified_caretaker_daily_report_custom_range(self, authenticated_client, test_caretaker_logs, test_project):
        """Test unified caretaker daily report with custom date range"""
        date_from = date.today() - timedelta(days=10)
        date_to = date.today()
        
        response = authenticated_client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'custom',
                'project_id': test_project.id,
                'date_from': date_from.strftime('%Y-%m-%d'),
                'date_to': date_to.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'مخصص' in data['range_display'] or 'custom' in data['range_display'].lower()

    def test_unified_caretaker_daily_report_with_pagination(self, authenticated_client, test_caretaker_logs, test_project):
        """Test unified caretaker daily report with pagination parameters"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d'),
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

    def test_unified_caretaker_daily_report_with_dog_filter(self, authenticated_client, test_caretaker_logs, test_project, test_dogs):
        """Test unified caretaker daily report filtered by specific dog"""
        target_date = date.today()
        test_dog = test_dogs[0]
        
        response = authenticated_client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d'),
                'dog_id': test_dog.id
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # All rows should be for the specified dog if dog filter is applied
        if data['rows'] and test_dog.id:
            for row in data['rows']:
                assert row['dog_id'] == str(test_dog.id)

    def test_unified_caretaker_daily_report_missing_params(self, authenticated_client):
        """Test unified caretaker daily report with missing required parameters"""
        # Missing range_type
        response = authenticated_client.get('/api/reports/breeding/caretaker-daily/unified')
        assert response.status_code == 400
        
        # Missing date for daily range
        response = authenticated_client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={'range_type': 'daily'}
        )
        assert response.status_code == 400
        
        # Missing week_start for weekly range
        response = authenticated_client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={'range_type': 'weekly'}
        )
        assert response.status_code == 400

    def test_unified_caretaker_daily_report_invalid_date_format(self, authenticated_client, test_project):
        """Test unified caretaker daily report with invalid date format"""
        response = authenticated_client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': 'invalid-date'
            }
        )
        assert response.status_code == 400

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

    def test_arabic_field_names_in_response(self, authenticated_client, test_caretaker_logs, test_project):
        """Test that API returns proper Arabic field names for RTL frontend"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        if data['rows']:  # If there are rows
            row = data['rows'][0]
            
            # Check Arabic field names for caretaker activities
            expected_arabic_fields = [
                'التاريخ',           # Date
                'اسم_الكلب',         # Dog name  
                'رمز_الكلب',         # Dog code
                'رقم_البيت',         # House number
                'القائم_بالرعاية',    # Caretaker name
                'تنظيف_البيت',       # House cleaning
                'شفط_البيت',         # House vacuuming
                'تنظيف_الصنبور',     # Tap cleaning
                'تنظيف_البالوعة',    # Drain cleaning
                'تنظيف_الكلب',       # Dog cleaning
                'استحمام_الكلب',     # Dog washing
                'تمشيط_الكلب',       # Dog brushing
                'تنظيف_الأواني',     # Bowl/bucket cleaning
                'ملاحظات',          # Notes
                'وقت_التسجيل'        # Recording time
            ]
            
            for field in expected_arabic_fields:
                assert field in row, f"Missing Arabic field: {field}"

    def test_cleaning_status_display_values(self, authenticated_client, test_caretaker_logs, test_project):
        """Test that cleaning status is properly displayed in Arabic"""
        target_date = date.today()
        
        response = authenticated_client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'daily', 
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        if data['rows']:
            row = data['rows'][0]
            
            # Check cleaning status values are in Arabic (نعم/لا)
            cleaning_fields = [
                'تنظيف_البيت', 'شفط_البيت', 'تنظيف_الصنبور', 'تنظيف_البالوعة',
                'تنظيف_الكلب', 'استحمام_الكلب', 'تمشيط_الكلب', 'تنظيف_الأواني'
            ]
            
            for field in cleaning_fields:
                if row.get(field):
                    assert row[field] in ['نعم', 'لا'], f"Invalid cleaning status for {field}: {row[field]}"

    @patch('k9.api.caretaker_daily_report_api._generate_caretaker_daily_pdf')
    def test_unified_caretaker_daily_pdf_export_success(self, mock_pdf_gen, authenticated_client, test_project):
        """Test successful PDF export for caretaker daily reports"""
        mock_pdf_gen.return_value = b'fake-pdf-content'
        
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
        assert 'attachment; filename=' in response.headers.get('Content-Disposition', '')
        assert 'caretaker-daily-report' in response.headers.get('Content-Disposition', '')
        mock_pdf_gen.assert_called_once()

    @patch('k9.api.caretaker_daily_report_api._generate_caretaker_daily_pdf')  
    def test_pdf_export_with_arabic_filename(self, mock_pdf_gen, authenticated_client, test_project):
        """Test PDF export generates proper Arabic filename"""
        mock_pdf_gen.return_value = b'fake-pdf-content'
        
        response = authenticated_client.get(
            '/api/reports/breeding/caretaker-daily/unified/export.pdf',
            query_string={
                'range_type': 'weekly',
                'project_id': test_project.id,
                'week_start': date.today().strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 200
        content_disposition = response.headers.get('Content-Disposition', '')
        assert 'filename=' in content_disposition
        # Should contain Arabic or project-related identifier
        assert any(identifier in content_disposition for identifier in ['caretaker', 'رعاية', test_project.id])

    def test_unauthenticated_access_denied(self, client, test_project):
        """Test that unauthenticated users cannot access caretaker daily reports"""
        response = client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 401

        # Test PDF export also denied
        response = client.get(
            '/api/reports/breeding/caretaker-daily/unified/export.pdf',
            query_string={
                'range_type': 'daily',
                'project_id': test_project.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        assert response.status_code == 401

    def test_invalid_range_type_handling(self, authenticated_client, test_project):
        """Test handling of invalid range_type parameter"""
        response = authenticated_client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'invalid_range',
                'project_id': test_project.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_large_dataset_pagination(self, authenticated_client, test_project):
        """Test pagination behavior with large datasets"""
        response = authenticated_client.get(
            '/api/reports/breeding/caretaker-daily/unified',
            query_string={
                'range_type': 'custom',
                'project_id': test_project.id,
                'date_from': (date.today() - timedelta(days=365)).strftime('%Y-%m-%d'),
                'date_to': date.today().strftime('%Y-%m-%d'),
                'per_page': 5
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check pagination is properly implemented
        pagination = data['pagination']
        assert pagination['per_page'] == 5
        assert len(data['rows']) <= 5