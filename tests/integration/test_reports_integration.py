"""
Integration tests for reports system
Tests data flow between different modules and report generation
"""

import pytest
from datetime import date, datetime, time
from uuid import uuid4

from models import (
    User, Employee, Dog, Project, TrainingSession, VeterinaryVisit,
    UserRole, ProjectStatus, TrainingCategory, VisitType, EmployeeRole
)
from models_attendance_reporting import ProjectAttendanceReporting, AttendanceDayLeave
from attendance_reporting_services import get_daily_sheet
from trainer_daily_services import get_trainer_daily
from app.reports.veterinary.daily_services import get_vet_daily


class TestReportsIntegration:
    """Integration tests for complete report workflows"""

    def test_complete_daily_operations_workflow(self, db_session, sample_user, sample_project):
        """Test complete workflow: data entry → reports → consistency check"""
        target_date = date.today()
        
        # 1. Create employees and dogs
        trainer = Employee(
            name="محمد أحمد",
            employee_id="TRN001",
            role=EmployeeRole.TRAINER,
            phone="0501234567",
            hire_date=date(2023, 1, 1)
        )
        vet = Employee(
            name="د. فاطمة علي",
            employee_id="VET001", 
            role=EmployeeRole.VETERINARIAN,
            phone="0507654321",
            hire_date=date(2023, 1, 1)
        )
        dog = Dog(
            name="لابرادور",
            code="DOG002",
            breed="لابرادور",
            gender="MALE",
            birth_date=date(2021, 5, 15),
            microchip_id="98765432109876",
            current_status="ACTIVE"
        )
        
        db_session.add_all([trainer, vet, dog])
        db_session.commit()
        
        # 2. Create attendance record
        attendance = ProjectAttendanceReporting(
            project_id=sample_project.id,
            employee_id=trainer.id,
            dog_id=dog.id,
            date=target_date,
            group_no=1,
            seq_no=1,
            check_in_time=time(8, 0),
            check_out_time=time(16, 0)
        )
        db_session.add(attendance)
        
        # 3. Create training session
        training = TrainingSession(
            dog_id=dog.id,
            trainer_id=trainer.id,
            project_id=sample_project.id,
            category=TrainingCategory.DETECTION,
            subject="تدريب الكشف عن المتفجرات",
            session_date=datetime.combine(target_date, time(10, 0)),
            duration=90,
            success_rating=9,
            location="ميدان التدريب الرئيسي",
            notes="أداء ممتاز"
        )
        db_session.add(training)
        
        # 4. Create veterinary visit
        vet_visit = VeterinaryVisit(
            dog_id=dog.id,
            vet_id=vet.id,
            project_id=sample_project.id,
            visit_type=VisitType.ROUTINE,
            visit_date=datetime.combine(target_date, time(14, 0)),
            reason="فحص دوري شهري",
            diagnosis="حالة صحية ممتازة",
            temperature=38.2,
            heart_rate=110,
            weight=32.5,
            medications=[
                {"name": "فيتامين متعدد", "dose": "1 قرص", "frequency": "يومياً"}
            ]
        )
        db_session.add(vet_visit)
        db_session.commit()
        
        # 5. Generate all reports
        attendance_report = get_daily_sheet(str(sample_project.id), target_date, sample_user)
        trainer_report = get_trainer_daily(str(sample_project.id), target_date, None, None, None, sample_user)
        vet_report = get_vet_daily(str(sample_project.id), target_date, None, None, None, sample_user)
        
        # 6. Verify data consistency across reports
        assert attendance_report["project_name"] == sample_project.name
        assert trainer_report["project_name"] == sample_project.name
        assert vet_report["project_name"] == sample_project.name
        
        # Verify dog appears in all relevant reports
        assert len(attendance_report["group_1_rows"]) > 0
        assert attendance_report["group_1_rows"][0]["dog_name"] == "لابرادور"
        
        assert len(trainer_report["sessions"]) > 0
        assert trainer_report["sessions"][0]["dog_name"] == "لابرادور"
        assert trainer_report["sessions"][0]["trainer_name"] == "محمد أحمد"
        
        assert len(vet_report["visits"]) > 0
        assert vet_report["visits"][0]["dog_name"] == "لابرادور"
        assert vet_report["visits"][0]["vet_name"] == "د. فاطمة علي"
        
        # Verify timing consistency
        assert "08:00" in attendance_report["group_1_rows"][0]["check_in_time"]
        assert trainer_report["sessions"][0]["time"] == "10:00"
        assert vet_report["visits"][0]["time"] == "14:00"

    def test_reports_with_data_updates_reflect_immediately(self, db_session, sample_user, sample_project):
        """Test that changes in source data immediately reflect in reports"""
        target_date = date.today()
        
        # Create initial data
        dog = Dog(
            name="الأصلي",
            code="DOG003", 
            breed="جيرمن شيبرد",
            gender="FEMALE",
            birth_date=date(2020, 3, 10),
            microchip_id="11111111111111",
            current_status="ACTIVE"
        )
        trainer = Employee(
            name="سارة محمود",
            employee_id="TRN002",
            role=EmployeeRole.TRAINER,
            phone="0509876543"
        )
        db_session.add_all([dog, trainer])
        db_session.commit()
        
        # Create training session
        session = TrainingSession(
            dog_id=dog.id,
            trainer_id=trainer.id,
            project_id=sample_project.id,
            category=TrainingCategory.DETECTION,
            subject="تدريب أولي",
            session_date=datetime.combine(target_date, time(9, 0)),
            duration=60,
            success_rating=6
        )
        db_session.add(session)
        db_session.commit()
        
        # Get initial report
        initial_report = get_trainer_daily(str(sample_project.id), target_date, None, None, None, sample_user)
        assert len(initial_report["sessions"]) == 1
        assert initial_report["sessions"][0]["success_rating"] == 6
        assert initial_report["sessions"][0]["subject"] == "تدريب أولي"
        
        # Update the session
        session.success_rating = 9
        session.subject = "تدريب متقدم"
        session.notes = "تحسن ملحوظ"
        db_session.commit()
        
        # Get updated report
        updated_report = get_trainer_daily(str(sample_project.id), target_date, None, None, None, sample_user)
        assert updated_report["sessions"][0]["success_rating"] == 9
        assert updated_report["sessions"][0]["subject"] == "تدريب متقدم"
        assert updated_report["sessions"][0]["notes"] == "تحسن ملحوظ"
        
        # Verify KPIs are recalculated
        if updated_report["summary_by_dog"]:
            assert updated_report["summary_by_dog"][0]["avg_rating"] == 9.0

    def test_reports_cross_module_dependencies(self, db_session, sample_user, sample_project):
        """Test reports correctly handle data from multiple modules"""
        target_date = date.today()
        
        # Create shared entities
        dog = Dog(
            name="الكلب المشترك",
            code="DOG004",
            breed="بلجيكي مالينوا", 
            gender="MALE",
            birth_date=date(2019, 8, 20),
            microchip_id="22222222222222",
            current_status="ACTIVE"
        )
        trainer = Employee(
            name="خالد أحمد",
            employee_id="TRN003",
            role=EmployeeRole.TRAINER,
            phone="0508888888"
        )
        vet = Employee(
            name="د. أميرة سالم",
            employee_id="VET002",
            role=EmployeeRole.VETERINARIAN,
            phone="0507777777"
        )
        db_session.add_all([dog, trainer, vet])
        db_session.commit()
        
        # Create attendance (morning)
        attendance = ProjectAttendanceReporting(
            project_id=sample_project.id,
            employee_id=trainer.id,
            dog_id=dog.id,
            date=target_date,
            group_no=1,
            seq_no=1,
            check_in_time=time(7, 30),
            check_out_time=time(15, 30)
        )
        db_session.add(attendance)
        
        # Create training sessions (morning and afternoon)
        morning_session = TrainingSession(
            dog_id=dog.id,
            trainer_id=trainer.id,
            project_id=sample_project.id,
            category=TrainingCategory.DETECTION,
            subject="تدريب صباحي",
            session_date=datetime.combine(target_date, time(8, 30)),
            duration=120,
            success_rating=8
        )
        afternoon_session = TrainingSession(
            dog_id=dog.id,
            trainer_id=trainer.id,
            project_id=sample_project.id,
            category=TrainingCategory.PATROL,
            subject="تدريب دورية",
            session_date=datetime.combine(target_date, time(13, 0)),
            duration=90,
            success_rating=7
        )
        db_session.add_all([morning_session, afternoon_session])
        
        # Create vet visit (midday)
        vet_visit = VeterinaryVisit(
            dog_id=dog.id,
            vet_id=vet.id,
            project_id=sample_project.id,
            visit_type=VisitType.ROUTINE,
            visit_date=datetime.combine(target_date, time(11, 30)),
            reason="فحص بين التدريبات",
            diagnosis="جاهز للتدريب المسائي"
        )
        db_session.add(vet_visit)
        db_session.commit()
        
        # Generate all reports
        attendance_report = get_daily_sheet(str(sample_project.id), target_date, sample_user)
        trainer_report = get_trainer_daily(str(sample_project.id), target_date, None, None, None, sample_user)
        vet_report = get_vet_daily(str(sample_project.id), target_date, None, None, None, sample_user)
        
        # Verify cross-module data consistency
        # All should reference same dog
        assert attendance_report["group_1_rows"][0]["dog_name"] == "الكلب المشترك"
        
        # Training report should show both sessions
        assert len(trainer_report["sessions"]) == 2
        session_times = [s["time"] for s in trainer_report["sessions"]]
        assert "08:30" in session_times
        assert "13:00" in session_times
        
        # Summary should aggregate both sessions
        dog_summary = trainer_report["summary_by_dog"][0]
        assert dog_summary["sessions_count"] == 2
        assert dog_summary["total_duration_min"] == 210  # 120 + 90
        assert dog_summary["avg_rating"] == 7.5  # (8 + 7) / 2
        
        # Vet report should show visit between training sessions
        assert len(vet_report["visits"]) == 1
        assert vet_report["visits"][0]["time"] == "11:30"
        assert vet_report["visits"][0]["dog_name"] == "الكلب المشترك"

    def test_reports_performance_with_large_dataset(self, db_session, sample_user, sample_project):
        """Test reports performance with larger data sets"""
        target_date = date.today()
        
        # Create multiple dogs and employees
        dogs = []
        trainers = []
        vets = []
        
        for i in range(10):  # 10 dogs
            dog = Dog(
                name=f"كلب {i+1}",
                code=f"DOG{i+10:03d}",
                breed="جيرمن شيبرد",
                gender="MALE" if i % 2 == 0 else "FEMALE",
                birth_date=date(2020, 1, 1),
                microchip_id=f"{i+10:014d}",
                current_status="ACTIVE"
            )
            dogs.append(dog)
            
        for i in range(5):  # 5 trainers
            trainer = Employee(
                name=f"مدرب {i+1}",
                employee_id=f"TRN{i+10:03d}",
                role=EmployeeRole.TRAINER,
                phone=f"050{i+1}000000"
            )
            trainers.append(trainer)
            
        for i in range(3):  # 3 vets
            vet = Employee(
                name=f"د. طبيب {i+1}",
                employee_id=f"VET{i+10:03d}",
                role=EmployeeRole.VETERINARIAN,
                phone=f"055{i+1}000000"
            )
            vets.append(vet)
            
        db_session.add_all(dogs + trainers + vets)
        db_session.commit()
        
        # Create attendance records for all dogs
        for i, dog in enumerate(dogs):
            attendance = ProjectAttendanceReporting(
                project_id=sample_project.id,
                employee_id=trainers[i % len(trainers)].id,
                dog_id=dog.id,
                date=target_date,
                group_no=1,
                seq_no=i+1,
                check_in_time=time(8, 0),
                check_out_time=time(16, 0)
            )
            db_session.add(attendance)
        
        # Create multiple training sessions
        for i, dog in enumerate(dogs):
            for j in range(3):  # 3 sessions per dog
                session = TrainingSession(
                    dog_id=dog.id,
                    trainer_id=trainers[i % len(trainers)].id,
                    project_id=sample_project.id,
                    category=TrainingCategory.DETECTION,
                    subject=f"جلسة {j+1} للكلب {i+1}",
                    session_date=datetime.combine(target_date, time(9+j, 0)),
                    duration=60,
                    success_rating=7 + (j % 3)
                )
                db_session.add(session)
        
        # Create vet visits
        for i, dog in enumerate(dogs):
            visit = VeterinaryVisit(
                dog_id=dog.id,
                vet_id=vets[i % len(vets)].id,
                project_id=sample_project.id,
                visit_type=VisitType.ROUTINE,
                visit_date=datetime.combine(target_date, time(14, 0)),
                reason=f"فحص الكلب {i+1}"
            )
            db_session.add(visit)
            
        db_session.commit()
        
        # Test report generation performance
        import time as time_module
        
        start_time = time_module.time()
        attendance_report = get_daily_sheet(str(sample_project.id), target_date, sample_user)
        attendance_time = time_module.time() - start_time
        
        start_time = time_module.time()
        trainer_report = get_trainer_daily(str(sample_project.id), target_date, None, None, None, sample_user)
        trainer_time = time_module.time() - start_time
        
        start_time = time_module.time()
        vet_report = get_vet_daily(str(sample_project.id), target_date, None, None, None, sample_user)
        vet_time = time_module.time() - start_time
        
        # Verify data volumes
        assert len(attendance_report["group_1_rows"]) == 10
        assert len(trainer_report["sessions"]) == 30  # 10 dogs × 3 sessions
        assert len(vet_report["visits"]) == 10
        
        # Verify performance (should complete within reasonable time)
        assert attendance_time < 2.0  # 2 seconds max
        assert trainer_time < 2.0
        assert vet_time < 2.0
        
        # Verify data integrity with large dataset
        assert len(trainer_report["summary_by_dog"]) == 10
        for dog_summary in trainer_report["summary_by_dog"]:
            assert dog_summary["sessions_count"] == 3
            assert dog_summary["total_duration_min"] == 180

    def test_reports_permission_enforcement_across_modules(self, db_session, sample_project):
        """Test consistent permission enforcement across all report modules"""
        # Create PM user
        pm_user = User(
            username="pm_reports",
            email="pm.reports@test.com",
            role=UserRole.PROJECT_MANAGER
        )
        pm_user.set_password("password")
        db_session.add(pm_user)
        db_session.commit()
        
        target_date = date.today()
        project_id = str(sample_project.id)
        
        # Test unauthorized access to all reports
        with pytest.raises(PermissionError):
            get_daily_sheet(project_id, target_date, pm_user)
            
        with pytest.raises(ValueError):
            get_trainer_daily(None, target_date, None, None, None, pm_user)
            
        with pytest.raises(ValueError):
            get_vet_daily(project_id, target_date, None, None, None, pm_user)

    def test_reports_data_validation_and_error_handling(self, db_session, sample_user):
        """Test error handling and data validation across reports"""
        target_date = date.today()
        fake_id = str(uuid4())
        
        # Test invalid project IDs
        with pytest.raises(ValueError):
            get_daily_sheet(fake_id, target_date, sample_user)
            
        with pytest.raises(ValueError):
            get_trainer_daily(fake_id, target_date, None, None, None, sample_user)
            
        with pytest.raises(ValueError):
            get_vet_daily(fake_id, target_date, None, None, None, sample_user)
        
        # Test invalid date formats
        with pytest.raises(ValueError):
            get_daily_sheet("invalid-id", "invalid-date", sample_user)
            
        # Test malformed UUIDs
        with pytest.raises(ValueError):
            get_trainer_daily("not-a-uuid", target_date, None, None, None, sample_user)