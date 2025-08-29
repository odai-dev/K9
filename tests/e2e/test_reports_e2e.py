"""
End-to-End tests for reports system
Tests complete user workflows from data entry to report export
"""

import pytest
from datetime import date, datetime, time
import json
import os
from unittest.mock import patch, Mock

from flask import url_for
from models import (
    User, Employee, Dog, Project, TrainingSession, VeterinaryVisit,
    UserRole, ProjectStatus, TrainingCategory, VisitType, EmployeeRole
)
from models_attendance_reporting import ProjectAttendanceReporting


class TestReportsE2E:
    """End-to-End tests for complete report workflows"""

    def test_complete_attendance_report_workflow(self, client, db_session, login_admin):
        """Test complete attendance report workflow: data entry → navigation → display → export"""
        # 1. Set up data
        project = Project(
            name="مشروع الاختبار الشامل",
            description="مشروع للاختبار",
            status=ProjectStatus.ACTIVE,
            start_date=date.today(),
            manager_id=login_admin.id
        )
        
        trainer = Employee(
            name="أحمد المدرب",
            employee_id="TRN100",
            role=EmployeeRole.TRAINER,
            phone="0501111111"
        )
        
        dog = Dog(
            name="الكلب التجريبي",
            code="TEST001",
            breed="جيرمن شيبرد",
            gender="MALE",
            birth_date=date(2020, 1, 1),
            microchip_id="12345678901234",
            current_status="ACTIVE"
        )
        
        db_session.add_all([project, trainer, dog])
        db_session.commit()
        
        # 2. Create attendance data through form submission
        attendance_data = {
            'project_id': str(project.id),
            'employee_id': str(trainer.id),
            'dog_id': str(dog.id),
            'date': date.today().isoformat(),
            'group_no': '1',
            'seq_no': '1',
            'check_in_time': '08:00',
            'check_out_time': '16:00'
        }
        
        # Simulate attendance entry
        attendance = ProjectAttendanceReporting(
            project_id=project.id,
            employee_id=trainer.id,
            dog_id=dog.id,
            date=date.today(),
            group_no=1,
            seq_no=1,
            check_in_time=time(8, 0),
            check_out_time=time(16, 0)
        )
        db_session.add(attendance)
        db_session.commit()
        
        # 3. Navigate to reports index
        response = client.get('/reports/')
        assert response.status_code == 200
        assert 'تقارير النظام' in response.get_data(as_text=True)
        assert 'تقرير الحضور اليومي' in response.get_data(as_text=True)
        
        # 4. Access attendance report page
        response = client.get(f'/reports/attendance/daily-sheet?project_id={project.id}&date={date.today()}')
        assert response.status_code == 200
        
        # 5. Generate report data through API
        api_response = client.post('/api/reports/attendance/daily-sheet', 
                                  json={
                                      'project_id': str(project.id),
                                      'date': date.today().isoformat()
                                  })
        assert api_response.status_code == 200
        
        report_data = api_response.get_json()
        assert report_data['success'] is True
        assert len(report_data['data']['group_1_rows']) > 0
        assert report_data['data']['group_1_rows'][0]['employee_name'] == 'أحمد المدرب'
        assert report_data['data']['group_1_rows'][0]['dog_name'] == 'الكلب التجريبي'
        
        # 6. Test PDF export
        with patch('attendance_reporting_exporters.export_daily_attendance_pdf') as mock_export:
            mock_export.return_value = 'uploads/test_report.pdf'
            
            export_response = client.post('/api/reports/attendance/export-pdf',
                                        json={
                                            'project_id': str(project.id),
                                            'date': date.today().isoformat()
                                        })
            assert export_response.status_code == 200
            mock_export.assert_called_once()

    def test_complete_training_report_workflow(self, client, db_session, login_admin):
        """Test complete training report workflow with filtering and export"""
        # 1. Set up data
        project = Project(
            name="مشروع التدريب المتقدم",
            description="مشروع تدريب",
            status=ProjectStatus.ACTIVE,
            start_date=date.today(),
            manager_id=login_admin.id
        )
        
        trainer = Employee(
            name="سارة المدربة",
            employee_id="TRN200",
            role=EmployeeRole.TRAINER,
            phone="0502222222"
        )
        
        dog = Dog(
            name="البطل",
            code="HERO001",
            breed="لابرادور",
            gender="MALE",
            birth_date=date(2019, 5, 10),
            microchip_id="98765432109876",
            current_status="ACTIVE"
        )
        
        db_session.add_all([project, trainer, dog])
        db_session.commit()
        
        # 2. Create training session
        session = TrainingSession(
            dog_id=dog.id,
            trainer_id=trainer.id,
            project_id=project.id,
            category=TrainingCategory.DETECTION,
            subject="تدريب الكشف المتقدم",
            session_date=datetime.combine(date.today(), time(10, 30)),
            duration=120,
            success_rating=9,
            location="ميدان التدريب الشمالي",
            weather_conditions="مشمس",
            notes="أداء استثنائي"
        )
        db_session.add(session)
        db_session.commit()
        
        # 3. Navigate to training reports
        response = client.get('/reports/training/trainer-daily')
        assert response.status_code == 200
        assert 'التقرير اليومي للمدرب' in response.get_data(as_text=True)
        
        # 4. Generate report with filters
        api_response = client.post('/api/reports/training/trainer-daily',
                                  json={
                                      'project_id': str(project.id),
                                      'date': date.today().isoformat(),
                                      'trainer_id': str(trainer.id),
                                      'category': 'DETECTION'
                                  })
        assert api_response.status_code == 200
        
        report_data = api_response.get_json()
        assert report_data['success'] is True
        assert len(report_data['data']['sessions']) > 0
        
        session_data = report_data['data']['sessions'][0]
        assert session_data['trainer_name'] == 'سارة المدربة'
        assert session_data['dog_name'] == 'البطل'
        assert session_data['category_ar'] == 'كشف'
        assert session_data['success_rating'] == 9
        
        # 5. Verify summary calculations
        assert len(report_data['data']['summary_by_dog']) > 0
        summary = report_data['data']['summary_by_dog'][0]
        assert summary['dog_name'] == 'البطل'
        assert summary['sessions_count'] == 1
        assert summary['total_duration_min'] == 120
        assert summary['avg_rating'] == 9.0
        
        # 6. Test PDF export
        with patch('trainer_daily_exporters.export_trainer_daily_pdf') as mock_export:
            mock_export.return_value = 'uploads/trainer_report.pdf'
            
            export_response = client.post('/api/reports/training/export-pdf',
                                        json={
                                            'project_id': str(project.id),
                                            'date': date.today().isoformat()
                                        })
            assert export_response.status_code == 200
            mock_export.assert_called_once()

    def test_complete_veterinary_report_workflow(self, client, db_session, login_admin):
        """Test complete veterinary report workflow with medical data"""
        # 1. Set up data
        project = Project(
            name="مشروع الرعاية البيطرية",
            description="مشروع طبي",
            status=ProjectStatus.ACTIVE,
            start_date=date.today(),
            manager_id=login_admin.id
        )
        
        vet = Employee(
            name="د. عبدالله الطبيب",
            employee_id="VET100",
            role=EmployeeRole.VETERINARIAN,
            phone="0553333333"
        )
        
        dog = Dog(
            name="المريض",
            code="PATIENT001",
            breed="بلجيكي مالينوا",
            gender="FEMALE",
            birth_date=date(2018, 12, 5),
            microchip_id="55555555555555",
            current_status="ACTIVE"
        )
        
        db_session.add_all([project, vet, dog])
        db_session.commit()
        
        # 2. Create veterinary visit with complex medical data
        visit = VeterinaryVisit(
            dog_id=dog.id,
            vet_id=vet.id,
            project_id=project.id,
            visit_type=VisitType.TREATMENT,
            visit_date=datetime.combine(date.today(), time(11, 15)),
            reason="فحص وعلاج",
            diagnosis="التهاب مفاصل خفيف",
            temperature=38.8,
            heart_rate=125,
            blood_pressure="120/80",
            weight=28.5,
            medications=[
                {
                    "name": "مضاد التهاب",
                    "dose": "50mg",
                    "frequency": "مرتين يومياً"
                },
                {
                    "name": "مسكن الألم",
                    "dose": "25mg", 
                    "frequency": "عند الحاجة"
                }
            ],
            vital_signs={
                "temp": 38.8,
                "hr": 125,
                "resp": 22,
                "bp": "120/80"
            },
            notes="استجابة جيدة للعلاج"
        )
        db_session.add(visit)
        db_session.commit()
        
        # 3. Navigate to veterinary reports
        response = client.get('/reports/veterinary/daily')
        assert response.status_code == 200
        assert 'التقرير البيطري اليومي' in response.get_data(as_text=True)
        
        # 4. Generate detailed report
        api_response = client.post('/api/reports/veterinary/daily',
                                  json={
                                      'project_id': str(project.id),
                                      'date': date.today().isoformat(),
                                      'visit_type': 'TREATMENT'
                                  })
        assert api_response.status_code == 200
        
        report_data = api_response.get_json()
        assert report_data['success'] is True
        assert len(report_data['data']['visits']) > 0
        
        visit_data = report_data['data']['visits'][0]
        assert visit_data['vet_name'] == 'د. عبدالله الطبيب'
        assert visit_data['dog_name'] == 'المريض'
        assert visit_data['visit_type_ar'] == 'علاج'
        assert 'مضاد التهاب' in visit_data['medications']
        assert 'الحرارة: 38.8' in visit_data['vital_signs']
        
        # 5. Verify summary data
        summary = report_data['data']['summary']
        assert summary['total_visits'] == 1
        assert summary['treatment_visits'] == 1
        assert summary['routine_visits'] == 0

    def test_reports_navigation_and_links(self, client, db_session, login_admin):
        """Test navigation links and UI consistency across report modules"""
        # 1. Test main reports index
        response = client.get('/reports/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        # Check all report links are present
        assert '/reports/attendance/daily-sheet' in html
        assert '/reports/training/trainer-daily' in html
        assert '/reports/veterinary/daily' in html
        assert 'تقرير الحضور اليومي' in html
        assert 'التقرير اليومي للمدرب' in html
        assert 'التقرير البيطري اليومي' in html
        
        # 2. Test breadcrumb navigation
        response = client.get('/reports/attendance/daily-sheet')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert 'nav' in html or 'breadcrumb' in html
        
        # 3. Test cross-module navigation
        response = client.get('/reports/training/trainer-daily')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        # Should have links back to main reports or other modules
        assert '/reports/' in html
        
        # 4. Test responsive design elements
        response = client.get('/reports/veterinary/daily')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        # Check for Bootstrap RTL classes
        assert 'rtl' in html or 'text-end' in html

    def test_reports_permission_enforcement_in_ui(self, client, db_session):
        """Test permission enforcement in report UI access"""
        # 1. Create PROJECT_MANAGER user
        pm_user = User(
            username="pm_ui_test",
            email="pm.ui@test.com",
            role=UserRole.PROJECT_MANAGER
        )
        pm_user.set_password("password")
        db_session.add(pm_user)
        db_session.commit()
        
        # 2. Login as PROJECT_MANAGER
        login_response = client.post('/login', data={
            'username': 'pm_ui_test',
            'password': 'password'
        })
        assert login_response.status_code == 302  # Redirect after login
        
        # 3. Test restricted access to reports without project assignment
        response = client.get('/reports/')
        assert response.status_code == 200
        # Should show limited options for PM users
        
        # 4. Test API endpoints with permission checking
        api_response = client.post('/api/reports/attendance/daily-sheet',
                                  json={
                                      'project_id': 'non-existent-id',
                                      'date': date.today().isoformat()
                                  })
        # Should return permission error or project not found
        assert api_response.status_code in [403, 404, 400]

    def test_reports_export_functionality_integrity(self, client, db_session, login_admin):
        """Test data integrity in exported reports"""
        # 1. Set up comprehensive test data
        project = Project(
            name="مشروع التصدير الشامل",
            description="اختبار التصدير",
            status=ProjectStatus.ACTIVE,
            start_date=date.today(),
            manager_id=login_admin.id
        )
        
        trainer = Employee(
            name="مدرب التصدير",
            employee_id="EXP001",
            role=EmployeeRole.TRAINER,
            phone="0504444444"
        )
        
        dog = Dog(
            name="كلب التصدير",
            code="EXPORT001",
            breed="دوبرمان",
            gender="MALE",
            birth_date=date(2020, 6, 15),
            microchip_id="77777777777777",
            current_status="ACTIVE"
        )
        
        db_session.add_all([project, trainer, dog])
        db_session.commit()
        
        # 2. Create comprehensive data
        # Attendance
        attendance = ProjectAttendanceReporting(
            project_id=project.id,
            employee_id=trainer.id,
            dog_id=dog.id,
            date=date.today(),
            group_no=1,
            seq_no=1,
            check_in_time=time(8, 0),
            check_out_time=time(16, 0)
        )
        
        # Training
        training = TrainingSession(
            dog_id=dog.id,
            trainer_id=trainer.id,
            project_id=project.id,
            category=TrainingCategory.PATROL,
            subject="دورية التصدير",
            session_date=datetime.combine(date.today(), time(10, 0)),
            duration=90,
            success_rating=8,
            notes="اختبار التصدير"
        )
        
        db_session.add_all([attendance, training])
        db_session.commit()
        
        # 3. Test CSV export data integrity
        with patch('attendance_reporting_exporters.export_daily_attendance_csv') as mock_csv:
            mock_csv_data = [
                ['التسلسل', 'اسم الموظف', 'اسم الكلب', 'وقت الدخول', 'وقت الخروج'],
                ['1', 'مدرب التصدير', 'كلب التصدير', '08:00', '16:00']
            ]
            mock_csv.return_value = 'uploads/test_export.csv'
            
            csv_response = client.post('/api/reports/attendance/export-csv',
                                     json={
                                         'project_id': str(project.id),
                                         'date': date.today().isoformat()
                                     })
            assert csv_response.status_code == 200
            mock_csv.assert_called_once()
        
        # 4. Test Excel export with Arabic content
        with patch('trainer_daily_exporters.export_trainer_daily_excel') as mock_excel:
            mock_excel.return_value = 'uploads/test_export.xlsx'
            
            excel_response = client.post('/api/reports/training/export-excel',
                                       json={
                                           'project_id': str(project.id),
                                           'date': date.today().isoformat()
                                       })
            assert excel_response.status_code == 200
            mock_excel.assert_called_once()

    def test_reports_real_time_updates(self, client, db_session, login_admin):
        """Test that reports reflect real-time data changes"""
        # 1. Set up initial data
        project = Project(
            name="مشروع التحديث المباشر",
            description="اختبار التحديث",
            status=ProjectStatus.ACTIVE,
            start_date=date.today(),
            manager_id=login_admin.id
        )
        
        trainer = Employee(
            name="مدرب التحديث",
            employee_id="UPD001",
            role=EmployeeRole.TRAINER,
            phone="0505555555"
        )
        
        dog = Dog(
            name="كلب التحديث",
            code="UPDATE001",
            breed="روت وايلر",
            gender="FEMALE",
            birth_date=date(2019, 9, 20),
            microchip_id="88888888888888",
            current_status="ACTIVE"
        )
        
        db_session.add_all([project, trainer, dog])
        db_session.commit()
        
        # 2. Create initial training session
        session = TrainingSession(
            dog_id=dog.id,
            trainer_id=trainer.id,
            project_id=project.id,
            category=TrainingCategory.DETECTION,
            subject="تدريب أولي",
            session_date=datetime.combine(date.today(), time(9, 0)),
            duration=60,
            success_rating=6
        )
        db_session.add(session)
        db_session.commit()
        
        # 3. Get initial report
        initial_response = client.post('/api/reports/training/trainer-daily',
                                     json={
                                         'project_id': str(project.id),
                                         'date': date.today().isoformat()
                                     })
        assert initial_response.status_code == 200
        initial_data = initial_response.get_json()
        assert initial_data['data']['sessions'][0]['success_rating'] == 6
        assert initial_data['data']['sessions'][0]['subject'] == 'تدريب أولي'
        
        # 4. Update session data
        session.success_rating = 9
        session.subject = 'تدريب متقدم محدث'
        session.notes = 'تم التحديث'
        db_session.commit()
        
        # 5. Get updated report
        updated_response = client.post('/api/reports/training/trainer-daily',
                                     json={
                                         'project_id': str(project.id),
                                         'date': date.today().isoformat()
                                     })
        assert updated_response.status_code == 200
        updated_data = updated_response.get_json()
        assert updated_data['data']['sessions'][0]['success_rating'] == 9
        assert updated_data['data']['sessions'][0]['subject'] == 'تدريب متقدم محدث'
        assert updated_data['data']['sessions'][0]['notes'] == 'تم التحديث'
        
        # 6. Verify summary is also updated
        assert updated_data['data']['summary_by_dog'][0]['avg_rating'] == 9.0

    def test_reports_error_handling_and_validation(self, client, db_session, login_admin):
        """Test error handling and validation in report workflows"""
        # 1. Test invalid project ID
        invalid_response = client.post('/api/reports/attendance/daily-sheet',
                                     json={
                                         'project_id': 'invalid-uuid',
                                         'date': date.today().isoformat()
                                     })
        assert invalid_response.status_code in [400, 404]
        
        # 2. Test invalid date format
        date_response = client.post('/api/reports/training/trainer-daily',
                                  json={
                                      'project_id': str(uuid4()),
                                      'date': 'invalid-date-format'
                                  })
        assert date_response.status_code == 400
        
        # 3. Test missing required parameters
        missing_response = client.post('/api/reports/veterinary/daily',
                                     json={})
        assert missing_response.status_code == 400
        
        # 4. Test graceful handling of no data
        empty_project = Project(
            name="مشروع فارغ",
            description="لا يحتوي على بيانات",
            status=ProjectStatus.ACTIVE,
            start_date=date.today(),
            manager_id=login_admin.id
        )
        db_session.add(empty_project)
        db_session.commit()
        
        empty_response = client.post('/api/reports/attendance/daily-sheet',
                                   json={
                                       'project_id': str(empty_project.id),
                                       'date': date.today().isoformat()
                                   })
        assert empty_response.status_code == 200
        empty_data = empty_response.get_json()
        assert empty_data['success'] is True
        assert len(empty_data['data']['group_1_rows']) == 0