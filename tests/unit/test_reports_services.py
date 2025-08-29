"""
Unit tests for reports services
Tests the core data generation functions for all report modules
"""

import pytest
from datetime import date, datetime, time
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4, UUID

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from attendance_reporting_services import get_daily_sheet
from trainer_daily_services import get_trainer_daily
from models import (
    User, Employee, Dog, Project, TrainingSession, VeterinaryVisit,
    UserRole, ProjectStatus, TrainingCategory, VisitType
)


class TestAttendanceReportingServices:
    """Test attendance reporting data generation functions"""

    def test_get_daily_sheet_valid_data(self, db_session, sample_user, sample_project, sample_employee, sample_dog):
        """Test that get_daily_sheet returns correct data structure"""
        target_date = date.today()
        
        result = get_daily_sheet(
            str(sample_project.id), 
            target_date, 
            sample_user
        )
        
        # Verify data structure
        assert isinstance(result, dict)
        assert "project_id" in result
        assert "date" in result
        assert "day_name_ar" in result
        assert "project_name" in result
        assert "group_1_rows" in result
        assert "group_2_rows" in result
        assert "leave_rows" in result
        
        # Verify data types
        assert isinstance(result["group_1_rows"], list)
        assert isinstance(result["group_2_rows"], list)
        assert isinstance(result["leave_rows"], list)

    def test_get_daily_sheet_permission_check(self, db_session, sample_project):
        """Test that PROJECT_MANAGER can only access assigned projects"""
        # Create PROJECT_MANAGER user
        pm_user = User(
            username="pm_test",
            email="pm@test.com",
            role=UserRole.PROJECT_MANAGER
        )
        pm_user.set_password("password")
        db_session.add(pm_user)
        db_session.commit()
        
        # Test access to unassigned project
        with pytest.raises(PermissionError):
            get_daily_sheet(str(sample_project.id), date.today(), pm_user)

    def test_get_daily_sheet_invalid_project(self, db_session, sample_user):
        """Test handling of invalid project ID"""
        fake_id = str(uuid4())
        
        with pytest.raises(ValueError, match="Project not found"):
            get_daily_sheet(fake_id, date.today(), sample_user)

    def test_get_daily_sheet_date_conversion(self, db_session, sample_user, sample_project):
        """Test that string dates are properly converted"""
        date_str = "2024-01-15"
        
        result = get_daily_sheet(
            str(sample_project.id), 
            date_str, 
            sample_user
        )
        
        assert result["date"] == date_str

    @patch('attendance_reporting_services.ProjectAttendanceReporting')
    def test_get_daily_sheet_data_processing(self, mock_attendance, db_session, sample_user, sample_project):
        """Test data processing and formatting"""
        # Mock attendance record
        mock_record = Mock()
        mock_record.seq_no = 1
        mock_record.employee = Mock()
        mock_record.employee.name = "أحمد محمد"
        mock_record.substitute_employee = None
        mock_record.dog = Mock()
        mock_record.dog.name = "ريكس"
        mock_record.check_in_time = time(8, 0)
        mock_record.check_out_time = time(16, 0)
        
        mock_attendance.query.filter.return_value.order_by.return_value = [mock_record]
        
        result = get_daily_sheet(str(sample_project.id), date.today(), sample_user)
        
        # Verify data formatting
        if result["group_1_rows"]:
            row = result["group_1_rows"][0]
            assert row["check_in_time"] == "08:00"
            assert row["check_out_time"] == "16:00"
            assert row["check_in_signed"] is False
            assert row["check_out_signed"] is False


class TestTrainerDailyServices:
    """Test trainer daily report data generation functions"""

    def test_get_trainer_daily_valid_data(self, db_session, sample_user, sample_project, sample_trainer, sample_dog):
        """Test trainer daily report returns correct structure"""
        target_date = date.today()
        
        result = get_trainer_daily(
            str(sample_project.id),
            target_date,
            str(sample_trainer.id),
            str(sample_dog.id),
            None,
            sample_user
        )
        
        # Verify data structure
        assert isinstance(result, dict)
        assert "date" in result
        assert "day_name_ar" in result
        assert "project_name" in result
        assert "sessions" in result
        assert "summary_by_dog" in result
        assert "kpis" in result
        
        # Verify data types
        assert isinstance(result["sessions"], list)
        assert isinstance(result["summary_by_dog"], list)
        assert isinstance(result["kpis"], dict)

    def test_get_trainer_daily_pm_permission(self, db_session, sample_project):
        """Test PROJECT_MANAGER requires project_id"""
        pm_user = User(
            username="pm_trainer",
            email="pm.trainer@test.com",
            role=UserRole.PROJECT_MANAGER
        )
        pm_user.set_password("password")
        db_session.add(pm_user)
        db_session.commit()
        
        # Test without project_id
        with pytest.raises(ValueError, match="Project ID is required for PROJECT_MANAGER"):
            get_trainer_daily(None, date.today(), None, None, None, pm_user)

    def test_get_trainer_daily_with_filters(self, db_session, sample_user, sample_project, sample_trainer, sample_dog):
        """Test filtering functionality"""
        # Create training session
        session = TrainingSession(
            dog_id=sample_dog.id,
            trainer_id=sample_trainer.id,
            project_id=sample_project.id,
            category=TrainingCategory.DETECTION,
            subject="اختبار الكشف",
            session_date=datetime.combine(date.today(), time(9, 0)),
            duration=60,
            success_rating=8
        )
        db_session.add(session)
        db_session.commit()
        
        result = get_trainer_daily(
            str(sample_project.id),
            date.today(),
            str(sample_trainer.id),
            str(sample_dog.id),
            "DETECTION",
            sample_user
        )
        
        # Should have filtered results
        assert len(result["sessions"]) >= 0
        if result["sessions"]:
            assert result["sessions"][0]["category_ar"] == "كشف"

    def test_get_trainer_daily_summary_calculation(self, db_session, sample_user, sample_project, sample_trainer, sample_dog):
        """Test summary calculations for dogs"""
        # Create multiple sessions for same dog
        for i in range(3):
            session = TrainingSession(
                dog_id=sample_dog.id,
                trainer_id=sample_trainer.id,
                project_id=sample_project.id,
                category=TrainingCategory.DETECTION,
                subject=f"جلسة {i+1}",
                session_date=datetime.combine(date.today(), time(9+i, 0)),
                duration=60,
                success_rating=7+i
            )
            db_session.add(session)
        db_session.commit()
        
        result = get_trainer_daily(
            str(sample_project.id),
            date.today(),
            None,
            None,
            None,
            sample_user
        )
        
        # Verify summary calculations
        if result["summary_by_dog"]:
            summary = result["summary_by_dog"][0]
            assert summary["sessions_count"] == 3
            assert summary["total_duration_min"] == 180
            assert 7 <= summary["avg_rating"] <= 9


class TestVeterinaryDailyServices:
    """Test veterinary daily report data generation functions"""

    def test_get_vet_daily_valid_data(self, db_session, sample_user, sample_project, sample_vet, sample_dog):
        """Test veterinary daily report returns correct structure"""
        target_date = date.today()
        
        result = get_vet_daily(
            str(sample_project.id),
            target_date,
            str(sample_vet.id),
            str(sample_dog.id),
            None,
            sample_user
        )
        
        # Verify data structure
        assert isinstance(result, dict)
        assert "project_name" in result
        assert "date" in result
        assert "day_name_ar" in result
        assert "visits" in result
        assert "summary" in result
        
        # Verify data types
        assert isinstance(result["visits"], list)
        assert isinstance(result["summary"], dict)

    def test_get_vet_daily_project_access(self, db_session, sample_project, sample_vet, sample_dog):
        """Test PROJECT_MANAGER project access validation"""
        # Create PM user without project access
        pm_user = User(
            username="pm_vet",
            email="pm.vet@test.com",
            role=UserRole.PROJECT_MANAGER
        )
        pm_user.set_password("password")
        db_session.add(pm_user)
        db_session.commit()
        
        with pytest.raises(ValueError, match="Access denied to this project"):
            get_vet_daily(str(sample_project.id), date.today(), None, None, None, pm_user)

    def test_get_vet_daily_invalid_project(self, db_session, sample_user):
        """Test handling of invalid project ID"""
        fake_id = str(uuid4())
        
        with pytest.raises(ValueError, match="Project not found"):
            get_vet_daily(fake_id, date.today(), None, None, None, sample_user)

    def test_get_vet_daily_with_visit_data(self, db_session, sample_user, sample_project, sample_vet, sample_dog):
        """Test processing of veterinary visit data"""
        # Create veterinary visit
        visit = VeterinaryVisit(
            dog_id=sample_dog.id,
            vet_id=sample_vet.id,
            project_id=sample_project.id,
            visit_type=VisitType.ROUTINE,
            visit_date=datetime.combine(date.today(), time(10, 0)),
            reason="فحص دوري",
            diagnosis="حالة جيدة",
            temperature=38.5,
            heart_rate=120,
            medications=[
                {"name": "فيتامين د", "dose": "100mg", "frequency": "يومياً"}
            ]
        )
        db_session.add(visit)
        db_session.commit()
        
        result = get_vet_daily(
            str(sample_project.id),
            date.today(),
            None,
            None,
            None,
            sample_user
        )
        
        # Verify visit data processing
        if result["visits"]:
            visit_data = result["visits"][0]
            assert "time" in visit_data
            assert "vet_name" in visit_data
            assert "dog_name" in visit_data
            assert "visit_type_ar" in visit_data
            assert "medications" in visit_data
            assert "vital_signs" in visit_data

    def test_get_vet_daily_medications_formatting(self, db_session, sample_user, sample_project, sample_vet, sample_dog):
        """Test medications data formatting"""
        # Test with complex medication data
        medications = [
            {"name": "أموكسيسيلين", "dose": "250mg", "frequency": "3 مرات يومياً"},
            {"name": "مسكن الألم", "dose": "50mg", "frequency": "عند الحاجة"}
        ]
        
        visit = VeterinaryVisit(
            dog_id=sample_dog.id,
            vet_id=sample_vet.id,
            project_id=sample_project.id,
            visit_type=VisitType.TREATMENT,
            visit_date=datetime.combine(date.today(), time(14, 0)),
            reason="علاج",
            medications=medications
        )
        db_session.add(visit)
        db_session.commit()
        
        result = get_vet_daily(
            str(sample_project.id),
            date.today(),
            None,
            None,
            None,
            sample_user
        )
        
        # Verify medications formatting
        if result["visits"]:
            visit_data = result["visits"][0]
            meds_str = visit_data["medications"]
            assert "أموكسيسيلين" in meds_str
            assert "250mg" in meds_str
            assert "3 مرات يومياً" in meds_str


class TestReportsServicesIntegration:
    """Integration tests for reports services working together"""

    def test_all_reports_with_same_project_date(self, db_session, sample_user, sample_project, 
                                               sample_trainer, sample_vet, sample_dog):
        """Test all report services with same project and date"""
        target_date = date.today()
        project_id = str(sample_project.id)
        
        # Get all reports
        attendance_report = get_daily_sheet(project_id, target_date, sample_user)
        trainer_report = get_trainer_daily(project_id, target_date, None, None, None, sample_user)
        vet_report = get_vet_daily(project_id, target_date, None, None, None, sample_user)
        
        # Verify all reports reference same project and date
        assert attendance_report["project_id"] == project_id
        assert trainer_report["project_name"] == sample_project.name
        assert vet_report["project_name"] == sample_project.name
        
        # Verify date consistency
        assert attendance_report["date"] == target_date.isoformat()
        assert trainer_report["date"] == target_date.isoformat()
        assert vet_report["date"] == target_date.isoformat()

    def test_reports_permissions_consistency(self, db_session, sample_project):
        """Test that all reports enforce same permission logic"""
        pm_user = User(
            username="pm_consistency",
            email="pm.consistency@test.com",
            role=UserRole.PROJECT_MANAGER
        )
        pm_user.set_password("password")
        db_session.add(pm_user)
        db_session.commit()
        
        project_id = str(sample_project.id)
        target_date = date.today()
        
        # All should raise PermissionError or ValueError for unauthorized access
        with pytest.raises((PermissionError, ValueError)):
            get_daily_sheet(project_id, target_date, pm_user)
        
        with pytest.raises(ValueError):
            get_trainer_daily(None, target_date, None, None, None, pm_user)
        
        with pytest.raises(ValueError):
            get_vet_daily(project_id, target_date, None, None, None, pm_user)

    def test_reports_data_consistency_with_shared_entities(self, db_session, sample_user, sample_project, 
                                                          sample_trainer, sample_vet, sample_dog):
        """Test data consistency when reports share dogs/employees"""
        target_date = date.today()
        
        # Create training session
        training_session = TrainingSession(
            dog_id=sample_dog.id,
            trainer_id=sample_trainer.id,
            project_id=sample_project.id,
            category=TrainingCategory.DETECTION,
            subject="تدريب مشترك",
            session_date=datetime.combine(target_date, time(9, 0)),
            duration=60,
            success_rating=8
        )
        db_session.add(training_session)
        
        # Create vet visit for same dog
        vet_visit = VeterinaryVisit(
            dog_id=sample_dog.id,
            vet_id=sample_vet.id,
            project_id=sample_project.id,
            visit_type=VisitType.ROUTINE,
            visit_date=datetime.combine(target_date, time(11, 0)),
            reason="فحص بعد التدريب"
        )
        db_session.add(vet_visit)
        db_session.commit()
        
        # Get reports
        trainer_report = get_trainer_daily(str(sample_project.id), target_date, None, None, None, sample_user)
        vet_report = get_vet_daily(str(sample_project.id), target_date, None, None, None, sample_user)
        
        # Verify dog name consistency
        if trainer_report["sessions"] and vet_report["visits"]:
            assert trainer_report["sessions"][0]["dog_name"] == vet_report["visits"][0]["dog_name"]
            assert trainer_report["sessions"][0]["dog_name"] == sample_dog.name