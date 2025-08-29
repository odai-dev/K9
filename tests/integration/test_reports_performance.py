"""
Performance tests for reports system
Tests system performance with large datasets and concurrent access
"""

import pytest
import time
import threading
from datetime import date, datetime, time as time_obj
from concurrent.futures import ThreadPoolExecutor, as_completed

from models import (
    User, Employee, Dog, Project, TrainingSession, VeterinaryVisit,
    UserRole, ProjectStatus, TrainingCategory, VisitType, EmployeeRole
)
from models_attendance_reporting import ProjectAttendanceReporting
from attendance_reporting_services import get_daily_sheet
from trainer_daily_services import get_trainer_daily
from app.reports.veterinary.daily_services import get_vet_daily


@pytest.mark.slow
@pytest.mark.performance
class TestReportsPerformance:
    """Performance testing for reports with large datasets"""

    def setup_large_dataset(self, db_session, project, num_dogs=50, num_trainers=10, num_vets=5):
        """Set up large dataset for performance testing"""
        dogs = []
        trainers = []
        vets = []
        
        # Create dogs
        for i in range(num_dogs):
            dog = Dog(
                name=f"كلب {i+1}",
                code=f"PERF{i+1:03d}",
                breed="جيرمن شيبرد" if i % 2 == 0 else "لابرادور",
                gender="MALE" if i % 2 == 0 else "FEMALE",
                birth_date=date(2020, 1, 1),
                microchip_id=f"{i+1000:014d}",
                current_status="ACTIVE",
                weight=25.0 + (i % 20),
                height=50.0 + (i % 30)
            )
            dogs.append(dog)
        
        # Create trainers
        for i in range(num_trainers):
            trainer = Employee(
                name=f"مدرب {i+1}",
                employee_id=f"PTRNR{i+1:03d}",
                role=EmployeeRole.TRAINER,
                phone=f"0501{i+1:06d}",
                hire_date=date(2023, 1, 1)
            )
            trainers.append(trainer)
        
        # Create vets
        for i in range(num_vets):
            vet = Employee(
                name=f"د. طبيب {i+1}",
                employee_id=f"PVET{i+1:03d}",
                role=EmployeeRole.VETERINARIAN,
                phone=f"0507{i+1:06d}",
                hire_date=date(2023, 1, 1)
            )
            vets.append(vet)
        
        db_session.add_all(dogs + trainers + vets)
        db_session.commit()
        
        return dogs, trainers, vets

    def test_attendance_report_performance_large_dataset(self, db_session, sample_user):
        """Test attendance report performance with large dataset"""
        # Create project
        project = Project(
            name="مشروع الأداء الكبير",
            description="اختبار الأداء",
            status=ProjectStatus.ACTIVE,
            start_date=date.today(),
            manager_id=sample_user.id
        )
        db_session.add(project)
        db_session.commit()
        
        # Set up large dataset
        dogs, trainers, vets = self.setup_large_dataset(db_session, project, 100, 20, 10)
        
        # Create attendance records
        target_date = date.today()
        for i, dog in enumerate(dogs):
            attendance = ProjectAttendanceReporting(
                project_id=project.id,
                employee_id=trainers[i % len(trainers)].id,
                dog_id=dog.id,
                date=target_date,
                group_no=1 if i < 50 else 2,
                seq_no=i+1,
                check_in_time=time_obj(8, 0),
                check_out_time=time_obj(16, 0)
            )
            db_session.add(attendance)
        
        db_session.commit()
        
        # Test performance
        start_time = time.time()
        report = get_daily_sheet(str(project.id), target_date, sample_user)
        execution_time = time.time() - start_time
        
        # Verify performance
        assert execution_time < 3.0  # Should complete within 3 seconds
        assert len(report["group_1_rows"]) == 50
        assert len(report["group_2_rows"]) == 50
        
        # Verify data integrity
        assert report["project_name"] == "مشروع الأداء الكبير"
        assert all(row["dog_name"].startswith("كلب") for row in report["group_1_rows"])

    def test_training_report_performance_large_dataset(self, db_session, sample_user):
        """Test training report performance with large dataset"""
        # Create project
        project = Project(
            name="مشروع التدريب الضخم",
            description="اختبار أداء التدريب",
            status=ProjectStatus.ACTIVE,
            start_date=date.today(),
            manager_id=sample_user.id
        )
        db_session.add(project)
        db_session.commit()
        
        # Set up dataset
        dogs, trainers, vets = self.setup_large_dataset(db_session, project, 30, 10, 5)
        
        # Create training sessions (3 sessions per dog)
        target_date = date.today()
        for i, dog in enumerate(dogs):
            for session_num in range(3):
                session = TrainingSession(
                    dog_id=dog.id,
                    trainer_id=trainers[i % len(trainers)].id,
                    project_id=project.id,
                    category=TrainingCategory.DETECTION,
                    subject=f"جلسة {session_num+1} للكلب {i+1}",
                    session_date=datetime.combine(target_date, time_obj(9+session_num, 0)),
                    duration=60,
                    success_rating=7 + (session_num % 3),
                    location="ميدان التدريب",
                    notes=f"ملاحظات الجلسة {session_num+1}"
                )
                db_session.add(session)
        
        db_session.commit()
        
        # Test performance
        start_time = time.time()
        report = get_trainer_daily(str(project.id), target_date, None, None, None, sample_user)
        execution_time = time.time() - start_time
        
        # Verify performance
        assert execution_time < 3.0  # Should complete within 3 seconds
        assert len(report["sessions"]) == 90  # 30 dogs × 3 sessions
        assert len(report["summary_by_dog"]) == 30
        
        # Verify calculations
        for dog_summary in report["summary_by_dog"]:
            assert dog_summary["sessions_count"] == 3
            assert dog_summary["total_duration_min"] == 180

    def test_veterinary_report_performance_large_dataset(self, db_session, sample_user):
        """Test veterinary report performance with large dataset"""
        # Create project
        project = Project(
            name="مشروع بيطري ضخم",
            description="اختبار أداء بيطري",
            status=ProjectStatus.ACTIVE,
            start_date=date.today(),
            manager_id=sample_user.id
        )
        db_session.add(project)
        db_session.commit()
        
        # Set up dataset
        dogs, trainers, vets = self.setup_large_dataset(db_session, project, 50, 5, 8)
        
        # Create veterinary visits
        target_date = date.today()
        for i, dog in enumerate(dogs):
            visit = VeterinaryVisit(
                dog_id=dog.id,
                vet_id=vets[i % len(vets)].id,
                project_id=project.id,
                visit_type=VisitType.ROUTINE if i % 2 == 0 else VisitType.TREATMENT,
                visit_date=datetime.combine(target_date, time_obj(10 + i//10, i%6*10)),
                reason=f"فحص الكلب {i+1}",
                diagnosis=f"تشخيص الكلب {i+1}",
                temperature=38.0 + (i % 5) * 0.2,
                heart_rate=110 + (i % 20),
                medications=[
                    {"name": f"دواء {i+1}", "dose": "50mg", "frequency": "يومياً"}
                ]
            )
            db_session.add(visit)
        
        db_session.commit()
        
        # Test performance
        start_time = time.time()
        report = get_vet_daily(str(project.id), target_date, None, None, None, sample_user)
        execution_time = time.time() - start_time
        
        # Verify performance
        assert execution_time < 3.0  # Should complete within 3 seconds
        assert len(report["visits"]) == 50
        
        # Verify summary calculations
        summary = report["summary"]
        assert summary["total_visits"] == 50
        assert summary["routine_visits"] == 25
        assert summary["treatment_visits"] == 25

    def test_concurrent_report_generation(self, db_session, sample_user):
        """Test concurrent report generation"""
        # Create project with data
        project = Project(
            name="مشروع متزامن",
            description="اختبار التزامن",
            status=ProjectStatus.ACTIVE,
            start_date=date.today(),
            manager_id=sample_user.id
        )
        db_session.add(project)
        db_session.commit()
        
        # Set up minimal dataset
        dogs, trainers, vets = self.setup_large_dataset(db_session, project, 10, 3, 2)
        
        # Create some data for each report type
        target_date = date.today()
        
        # Attendance
        for i, dog in enumerate(dogs):
            attendance = ProjectAttendanceReporting(
                project_id=project.id,
                employee_id=trainers[i % len(trainers)].id,
                dog_id=dog.id,
                date=target_date,
                group_no=1,
                seq_no=i+1,
                check_in_time=time_obj(8, 0),
                check_out_time=time_obj(16, 0)
            )
            db_session.add(attendance)
        
        # Training
        for i, dog in enumerate(dogs):
            session = TrainingSession(
                dog_id=dog.id,
                trainer_id=trainers[i % len(trainers)].id,
                project_id=project.id,
                category=TrainingCategory.DETECTION,
                subject=f"تدريب متزامن {i+1}",
                session_date=datetime.combine(target_date, time_obj(10, 0)),
                duration=60,
                success_rating=8
            )
            db_session.add(session)
        
        # Veterinary
        for i, dog in enumerate(dogs):
            visit = VeterinaryVisit(
                dog_id=dog.id,
                vet_id=vets[i % len(vets)].id,
                project_id=project.id,
                visit_type=VisitType.ROUTINE,
                visit_date=datetime.combine(target_date, time_obj(14, 0)),
                reason=f"فحص متزامن {i+1}"
            )
            db_session.add(visit)
        
        db_session.commit()
        
        # Test concurrent execution
        results = []
        errors = []
        
        def generate_attendance_report():
            try:
                start = time.time()
                report = get_daily_sheet(str(project.id), target_date, sample_user)
                end = time.time()
                results.append(("attendance", end - start, len(report["group_1_rows"])))
            except Exception as e:
                errors.append(("attendance", str(e)))
        
        def generate_training_report():
            try:
                start = time.time()
                report = get_trainer_daily(str(project.id), target_date, None, None, None, sample_user)
                end = time.time()
                results.append(("training", end - start, len(report["sessions"])))
            except Exception as e:
                errors.append(("training", str(e)))
        
        def generate_vet_report():
            try:
                start = time.time()
                report = get_vet_daily(str(project.id), target_date, None, None, None, sample_user)
                end = time.time()
                results.append(("veterinary", end - start, len(report["visits"])))
            except Exception as e:
                errors.append(("veterinary", str(e)))
        
        # Run concurrent threads
        threads = [
            threading.Thread(target=generate_attendance_report),
            threading.Thread(target=generate_training_report),
            threading.Thread(target=generate_vet_report)
        ]
        
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3
        assert total_time < 5.0  # All should complete within 5 seconds
        
        # Verify each report type completed
        report_types = [result[0] for result in results]
        assert "attendance" in report_types
        assert "training" in report_types
        assert "veterinary" in report_types

    def test_memory_usage_large_dataset(self, db_session, sample_user):
        """Test memory usage with large datasets"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create project with large dataset
        project = Project(
            name="مشروع الذاكرة",
            description="اختبار استخدام الذاكرة",
            status=ProjectStatus.ACTIVE,
            start_date=date.today(),
            manager_id=sample_user.id
        )
        db_session.add(project)
        db_session.commit()
        
        # Create large dataset
        dogs, trainers, vets = self.setup_large_dataset(db_session, project, 200, 30, 15)
        
        target_date = date.today()
        
        # Create extensive data
        for i, dog in enumerate(dogs):
            # Attendance
            attendance = ProjectAttendanceReporting(
                project_id=project.id,
                employee_id=trainers[i % len(trainers)].id,
                dog_id=dog.id,
                date=target_date,
                group_no=1,
                seq_no=i+1,
                check_in_time=time_obj(8, 0),
                check_out_time=time_obj(16, 0)
            )
            db_session.add(attendance)
            
            # Training sessions
            for j in range(2):  # 2 sessions per dog
                session = TrainingSession(
                    dog_id=dog.id,
                    trainer_id=trainers[i % len(trainers)].id,
                    project_id=project.id,
                    category=TrainingCategory.DETECTION,
                    subject=f"تدريب ذاكرة {i+1}-{j+1}",
                    session_date=datetime.combine(target_date, time_obj(9+j, 0)),
                    duration=90,
                    success_rating=8,
                    notes=f"ملاحظات طويلة للجلسة {i+1}-{j+1} " * 10  # Long notes
                )
                db_session.add(session)
            
            # Veterinary visit
            visit = VeterinaryVisit(
                dog_id=dog.id,
                vet_id=vets[i % len(vets)].id,
                project_id=project.id,
                visit_type=VisitType.ROUTINE,
                visit_date=datetime.combine(target_date, time_obj(13, 0)),
                reason=f"فحص ذاكرة مفصل للكلب {i+1}",
                diagnosis=f"تشخيص مفصل وطويل للكلب {i+1} يحتوي على تفاصيل كثيرة",
                notes=f"ملاحظات طبية مفصلة للكلب {i+1} " * 15,  # Long notes
                medications=[
                    {"name": f"دواء {j+1}", "dose": "100mg", "frequency": "مرتين يومياً"}
                    for j in range(3)  # Multiple medications
                ]
            )
            db_session.add(visit)
        
        db_session.commit()
        
        # Check memory after data creation
        after_data_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate reports
        attendance_report = get_daily_sheet(str(project.id), target_date, sample_user)
        training_report = get_trainer_daily(str(project.id), target_date, None, None, None, sample_user)
        vet_report = get_vet_daily(str(project.id), target_date, None, None, None, sample_user)
        
        # Check final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Verify reports were generated correctly
        assert len(attendance_report["group_1_rows"]) == 200
        assert len(training_report["sessions"]) == 400  # 200 dogs × 2 sessions
        assert len(vet_report["visits"]) == 200
        
        # Memory usage should be reasonable (less than 500MB increase)
        memory_increase = final_memory - initial_memory
        assert memory_increase < 500, f"Memory usage increased by {memory_increase}MB"
        
        # Clean up references to help garbage collection
        del attendance_report, training_report, vet_report
        
    @pytest.mark.parametrize("num_dogs,num_sessions", [
        (10, 1),
        (50, 2),
        (100, 3),
        (200, 2)
    ])
    def test_scalability_different_sizes(self, db_session, sample_user, num_dogs, num_sessions):
        """Test scalability with different dataset sizes"""
        # Create project
        project = Project(
            name=f"مشروع قابلية التوسع {num_dogs}",
            description="اختبار قابلية التوسع",
            status=ProjectStatus.ACTIVE,
            start_date=date.today(),
            manager_id=sample_user.id
        )
        db_session.add(project)
        db_session.commit()
        
        # Set up dataset
        num_trainers = max(5, num_dogs // 10)
        dogs, trainers, vets = self.setup_large_dataset(db_session, project, num_dogs, num_trainers, 5)
        
        # Create training sessions
        target_date = date.today()
        for i, dog in enumerate(dogs):
            for j in range(num_sessions):
                session = TrainingSession(
                    dog_id=dog.id,
                    trainer_id=trainers[i % len(trainers)].id,
                    project_id=project.id,
                    category=TrainingCategory.DETECTION,
                    subject=f"قابلية توسع {i+1}-{j+1}",
                    session_date=datetime.combine(target_date, time_obj(9+j, 0)),
                    duration=60,
                    success_rating=8
                )
                db_session.add(session)
        
        db_session.commit()
        
        # Test performance scales reasonably
        start_time = time.time()
        report = get_trainer_daily(str(project.id), target_date, None, None, None, sample_user)
        execution_time = time.time() - start_time
        
        # Performance should scale reasonably (not exponentially)
        expected_sessions = num_dogs * num_sessions
        max_expected_time = 0.05 * num_dogs / 10  # Linear scaling expectation
        
        assert len(report["sessions"]) == expected_sessions
        assert execution_time < max_expected_time, f"Execution time {execution_time}s exceeds expected {max_expected_time}s for {num_dogs} dogs"