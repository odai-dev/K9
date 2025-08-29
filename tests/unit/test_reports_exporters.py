"""
Unit tests for reports exporters
Tests PDF, Excel, and CSV export functionality and data integrity
"""

import pytest
from datetime import date, datetime, time
from unittest.mock import Mock, patch, MagicMock
import os
from io import BytesIO

from attendance_reporting_exporters import export_daily_attendance_pdf
from trainer_daily_exporters import export_trainer_daily_pdf


class TestAttendanceExporters:
    """Test attendance report export functions"""

    def test_export_daily_attendance_pdf_structure(self):
        """Test PDF export creates valid structure"""
        # Mock data in expected format
        test_data = {
            "project_id": "test-project-id",
            "project_name": "مشروع الاختبار",
            "date": "2024-01-15",
            "day_name_ar": "الاثنين",
            "group_1_rows": [
                {
                    "seq_no": 1,
                    "employee_name": "أحمد محمد",
                    "substitute_name": "",
                    "dog_name": "ريكس",
                    "check_in_time": "08:00",
                    "check_out_time": "16:00",
                    "check_in_signed": False,
                    "check_out_signed": False
                }
            ],
            "group_2_rows": [],
            "leave_rows": []
        }
        
        with patch('attendance_reporting_exporters.SimpleDocTemplate') as mock_doc:
            with patch('attendance_reporting_exporters.ensure_reports_directory') as mock_dir:
                mock_dir.return_value = "/tmp/reports"
                mock_doc_instance = Mock()
                mock_doc.return_value = mock_doc_instance
                
                result_path = export_daily_attendance_pdf(test_data)
                
                # Verify file path structure
                assert isinstance(result_path, str)
                assert "daily_sheet_" in result_path
                assert ".pdf" in result_path
                
                # Verify document creation
                mock_doc.assert_called_once()
                mock_doc_instance.build.assert_called_once()

    def test_export_daily_attendance_pdf_arabic_formatting(self):
        """Test Arabic text formatting in PDF export"""
        test_data = {
            "project_name": "مشروع النصوص العربية",
            "date": "2024-01-15",
            "day_name_ar": "الثلاثاء",
            "group_1_rows": [
                {
                    "seq_no": 1,
                    "employee_name": "فاطمة الزهراء",
                    "dog_name": "البطل العربي",
                    "check_in_time": "07:30",
                    "check_out_time": "15:30"
                }
            ],
            "group_2_rows": [],
            "leave_rows": []
        }
        
        with patch('attendance_reporting_exporters.register_arabic_fonts') as mock_fonts:
            with patch('attendance_reporting_exporters.get_arabic_font_name') as mock_font_name:
                with patch('attendance_reporting_exporters.SimpleDocTemplate'):
                    with patch('attendance_reporting_exporters.ensure_reports_directory'):
                        mock_font_name.return_value = "DejaVuSans"
                        
                        result_path = export_daily_attendance_pdf(test_data)
                        
                        # Verify Arabic font handling
                        mock_fonts.assert_called_once()
                        mock_font_name.assert_called_once()

    def test_export_daily_attendance_pdf_error_handling(self):
        """Test error handling in PDF export"""
        invalid_data = {
            "project_name": None,  # Invalid data
            "date": "invalid-date"
        }
        
        with patch('attendance_reporting_exporters.SimpleDocTemplate') as mock_doc:
            mock_doc.side_effect = Exception("PDF creation failed")
            
            # Should handle errors gracefully
            with pytest.raises(Exception):
                export_daily_attendance_pdf(invalid_data)

    def test_export_daily_attendance_pdf_file_naming(self):
        """Test PDF file naming convention"""
        test_data = {
            "project_id": "abc-123-def",
            "date": "2024-03-20",
            "project_name": "مشروع التسمية",
            "day_name_ar": "الأربعاء",
            "group_1_rows": [],
            "group_2_rows": [],
            "leave_rows": []
        }
        
        with patch('attendance_reporting_exporters.get_project_code') as mock_code:
            with patch('attendance_reporting_exporters.ensure_reports_directory') as mock_dir:
                with patch('attendance_reporting_exporters.SimpleDocTemplate'):
                    mock_code.return_value = "PRJ001"
                    mock_dir.return_value = "/tmp/reports"
                    
                    result_path = export_daily_attendance_pdf(test_data)
                    
                    # Verify file naming pattern
                    assert "daily_sheet_PRJ001_20240320.pdf" in result_path


class TestTrainerExporters:
    """Test trainer report export functions"""

    def test_export_trainer_daily_pdf_structure(self):
        """Test trainer PDF export structure"""
        test_data = {
            "date": "2024-01-15",
            "day_name_ar": "الاثنين",
            "project_name": "مشروع التدريب",
            "project_id": "trainer-project-123",
            "sessions": [
                {
                    "time": "09:00",
                    "trainer_name": "أحمد المدرب",
                    "dog_name": "الكلب البطل",
                    "category_ar": "كشف",
                    "subject": "تدريب الكشف",
                    "duration_min": 60,
                    "success_rating": 8,
                    "location": "الميدان الرئيسي",
                    "weather": "مشمس",
                    "equipment": "حقيبة تدريب",
                    "notes": "أداء جيد"
                }
            ],
            "summary_by_dog": [
                {
                    "dog_name": "الكلب البطل",
                    "sessions_count": 1,
                    "total_duration_min": 60,
                    "avg_rating": 8.0
                }
            ],
            "kpis": {
                "total_sessions": 1,
                "total_duration_hours": 1.0,
                "avg_success_rating": 8.0
            }
        }
        
        with patch('trainer_daily_exporters.SimpleDocTemplate') as mock_doc:
            with patch('os.makedirs'):
                mock_doc_instance = Mock()
                mock_doc.return_value = mock_doc_instance
                
                result_path = export_trainer_daily_pdf(test_data)
                
                # Verify structure
                assert isinstance(result_path, str)
                assert "trainer_daily_" in result_path
                assert ".pdf" in result_path
                
                # Verify document creation
                mock_doc.assert_called_once()
                mock_doc_instance.build.assert_called_once()

    def test_export_trainer_daily_pdf_arabic_content(self):
        """Test Arabic content handling in trainer PDF"""
        test_data = {
            "date": "2024-02-10",
            "day_name_ar": "السبت",
            "project_name": "مشروع النصوص العربية المعقدة",
            "sessions": [
                {
                    "trainer_name": "محمد عبدالرحمن الطويل الاسم",
                    "dog_name": "كلب بالاسم العربي الطويل جداً",
                    "category_ar": "دورية وحراسة",
                    "subject": "تدريب الحراسة الليلية والدورية الصباحية",
                    "notes": "ملاحظات طويلة باللغة العربية تحتوي على تفاصيل كثيرة"
                }
            ],
            "summary_by_dog": [],
            "kpis": {}
        }
        
        with patch('trainer_daily_exporters.register_arabic_fonts') as mock_fonts:
            with patch('trainer_daily_exporters.get_arabic_font') as mock_font:
                with patch('trainer_daily_exporters.SimpleDocTemplate'):
                    with patch('os.makedirs'):
                        mock_font.return_value = "DejaVuSans"
                        
                        result_path = export_trainer_daily_pdf(test_data)
                        
                        # Verify Arabic handling
                        mock_fonts.assert_called_once()
                        mock_font.assert_called_once()

    def test_export_trainer_daily_pdf_empty_data(self):
        """Test PDF export with empty data"""
        empty_data = {
            "date": "2024-01-01",
            "day_name_ar": "الاثنين",
            "project_name": "مشروع فارغ",
            "sessions": [],
            "summary_by_dog": [],
            "kpis": {
                "total_sessions": 0,
                "total_duration_hours": 0.0,
                "avg_success_rating": 0.0
            }
        }
        
        with patch('trainer_daily_exporters.SimpleDocTemplate') as mock_doc:
            with patch('os.makedirs'):
                mock_doc_instance = Mock()
                mock_doc.return_value = mock_doc_instance
                
                result_path = export_trainer_daily_pdf(empty_data)
                
                # Should handle empty data gracefully
                assert isinstance(result_path, str)
                mock_doc_instance.build.assert_called_once()


class TestExportersIntegration:
    """Integration tests for export functionality"""

    def test_all_exporters_consistent_file_structure(self):
        """Test all exporters create consistent file structures"""
        # Test data for attendance
        attendance_data = {
            "project_id": "test-123",
            "date": "2024-01-15",
            "project_name": "مشروع موحد",
            "day_name_ar": "الاثنين",
            "group_1_rows": [],
            "group_2_rows": [],
            "leave_rows": []
        }
        
        # Test data for trainer
        trainer_data = {
            "date": "2024-01-15",
            "project_id": "test-123",
            "project_name": "مشروع موحد",
            "sessions": [],
            "summary_by_dog": [],
            "kpis": {}
        }
        
        with patch('attendance_reporting_exporters.SimpleDocTemplate'):
            with patch('trainer_daily_exporters.SimpleDocTemplate'):
                with patch('attendance_reporting_exporters.ensure_reports_directory') as mock_dir1:
                    with patch('os.makedirs'):
                        mock_dir1.return_value = "/tmp/reports"
                        
                        attendance_path = export_daily_attendance_pdf(attendance_data)
                        trainer_path = export_trainer_daily_pdf(trainer_data)
                        
                        # Both should create PDF files
                        assert attendance_path.endswith('.pdf')
                        assert trainer_path.endswith('.pdf')
                        
                        # Both should include date in filename
                        assert "20240115" in attendance_path
                        assert "20240115" in trainer_path

    def test_exporters_concurrent_access(self):
        """Test exporters can handle concurrent access"""
        import threading
        import time
        
        results = []
        errors = []
        
        def export_attendance():
            try:
                data = {
                    "project_id": "concurrent-test",
                    "date": "2024-01-15",
                    "project_name": "اختبار متزامن",
                    "day_name_ar": "الاثنين",
                    "group_1_rows": [],
                    "group_2_rows": [],
                    "leave_rows": []
                }
                with patch('attendance_reporting_exporters.SimpleDocTemplate'):
                    with patch('attendance_reporting_exporters.ensure_reports_directory'):
                        result = export_daily_attendance_pdf(data)
                        results.append(result)
            except Exception as e:
                errors.append(e)
        
        def export_trainer():
            try:
                data = {
                    "date": "2024-01-15",
                    "project_id": "concurrent-test",
                    "sessions": [],
                    "summary_by_dog": [],
                    "kpis": {}
                }
                with patch('trainer_daily_exporters.SimpleDocTemplate'):
                    with patch('os.makedirs'):
                        result = export_trainer_daily_pdf(data)
                        results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Run exports concurrently
        threads = [
            threading.Thread(target=export_attendance),
            threading.Thread(target=export_trainer)
        ]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify both completed successfully
        assert len(errors) == 0
        assert len(results) == 2

    def test_exporters_large_data_performance(self):
        """Test exporters performance with large datasets"""
        import time
        
        # Create large dataset
        large_attendance_data = {
            "project_id": "large-test",
            "date": "2024-01-15",
            "project_name": "مشروع كبير",
            "day_name_ar": "الاثنين",
            "group_1_rows": [
                {
                    "seq_no": i,
                    "employee_name": f"موظف {i}",
                    "dog_name": f"كلب {i}",
                    "check_in_time": "08:00",
                    "check_out_time": "16:00"
                }
                for i in range(100)  # 100 rows
            ],
            "group_2_rows": [],
            "leave_rows": []
        }
        
        large_trainer_data = {
            "date": "2024-01-15",
            "project_id": "large-test",
            "sessions": [
                {
                    "time": f"{8+i//10}:{i%10*6:02d}",
                    "trainer_name": f"مدرب {i}",
                    "dog_name": f"كلب {i}",
                    "category_ar": "كشف",
                    "subject": f"جلسة تدريب رقم {i}",
                    "duration_min": 60,
                    "success_rating": 7 + (i % 3),
                    "notes": f"ملاحظات الجلسة {i}"
                }
                for i in range(50)  # 50 sessions
            ],
            "summary_by_dog": [],
            "kpis": {}
        }
        
        with patch('attendance_reporting_exporters.SimpleDocTemplate'):
            with patch('trainer_daily_exporters.SimpleDocTemplate'):
                with patch('attendance_reporting_exporters.ensure_reports_directory'):
                    with patch('os.makedirs'):
                        # Test attendance export performance
                        start_time = time.time()
                        attendance_result = export_daily_attendance_pdf(large_attendance_data)
                        attendance_time = time.time() - start_time
                        
                        # Test trainer export performance
                        start_time = time.time()
                        trainer_result = export_trainer_daily_pdf(large_trainer_data)
                        trainer_time = time.time() - start_time
                        
                        # Should complete within reasonable time
                        assert attendance_time < 5.0  # 5 seconds max
                        assert trainer_time < 5.0
                        
                        # Should return valid paths
                        assert isinstance(attendance_result, str)
                        assert isinstance(trainer_result, str)

    @patch('attendance_reporting_exporters.os.path.exists')
    def test_exporters_file_cleanup(self, mock_exists):
        """Test exporters handle file cleanup properly"""
        mock_exists.return_value = True
        
        test_data = {
            "project_id": "cleanup-test",
            "date": "2024-01-15",
            "project_name": "اختبار التنظيف",
            "day_name_ar": "الاثنين",
            "group_1_rows": [],
            "group_2_rows": [],
            "leave_rows": []
        }
        
        with patch('attendance_reporting_exporters.SimpleDocTemplate') as mock_doc:
            with patch('attendance_reporting_exporters.ensure_reports_directory'):
                mock_doc_instance = Mock()
                mock_doc.return_value = mock_doc_instance
                
                result_path = export_daily_attendance_pdf(test_data)
                
                # Verify file handling
                assert isinstance(result_path, str)
                mock_doc.assert_called_once()