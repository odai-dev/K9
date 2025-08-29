"""
اختبارات الوحدة لنماذج الحضور والتقارير
تفحص صحة نماذج الحضور وسلوكها المنطقي
"""

import pytest
from datetime import date, time, datetime
from models_attendance_reporting import (
    ProjectAttendanceReporting, AttendanceDayLeave, PMDailyEvaluation,
    AttendanceStatus, LeaveType
)


@pytest.mark.unit
class TestProjectAttendanceReportingModel:
    """اختبارات نموذج تقرير حضور المشروع"""
    
    def test_attendance_record_creation(self, db_session, sample_project, sample_employee):
        """اختبار إنشاء سجل حضور جديد"""
        attendance = ProjectAttendanceReporting()
        attendance.date = date(2024, 8, 29)
        attendance.project_id = sample_project.id
        attendance.employee_id = sample_employee.id
        attendance.group_no = 1
        attendance.seq_no = 1
        attendance.check_in_time = time(8, 0)
        attendance.check_out_time = time(16, 30)
        attendance.status = AttendanceStatus.PRESENT
        attendance.is_project_controlled = True
        
        db_session.add(attendance)
        db_session.commit()
        
        assert attendance.id is not None
        assert attendance.date == date(2024, 8, 29)
        assert attendance.group_no == 1
        assert attendance.seq_no == 1
        assert attendance.status == AttendanceStatus.PRESENT
        assert attendance.is_project_controlled is True
        
    def test_attendance_record_with_substitute(self, db_session, sample_project, sample_employee):
        """اختبار سجل حضور مع موظف بديل"""
        # إنشاء موظف بديل
        substitute = Employee()
        substitute.name = 'محمد سالم'
        substitute.employee_id = 'EMP002'
        substitute.role = EmployeeRole.HANDLER
        substitute.phone = '987654321'
        substitute.email = 'mohammed@example.com'
        substitute.hire_date = date(2023, 3, 1)
        
        db_session.add(substitute)
        db_session.commit()
        
        # إنشاء سجل حضور مع بديل
        attendance = ProjectAttendanceReporting()
        attendance.date = date.today()
        attendance.project_id = sample_project.id
        attendance.employee_id = sample_employee.id
        attendance.substitute_employee_id = substitute.id
        attendance.group_no = 1
        attendance.seq_no = 2
        attendance.status = AttendanceStatus.ABSENT
        
        db_session.add(attendance)
        db_session.commit()
        
        assert attendance.substitute_employee_id == substitute.id
        assert attendance.status == AttendanceStatus.ABSENT
        
    def test_attendance_record_relationships(self, sample_attendance_record):
        """اختبار العلاقات في سجل الحضور"""
        assert sample_attendance_record.project is not None
        assert sample_attendance_record.employee is not None
        assert sample_attendance_record.project.name == 'مشروع الأمن'
        assert sample_attendance_record.employee.name == 'أحمد محمد'
        
    def test_attendance_record_string_representation(self, sample_attendance_record):
        """اختبار التمثيل النصي لسجل الحضور"""
        project_id = sample_attendance_record.project_id
        date_str = sample_attendance_record.date
        expected = f'<ProjectAttendanceReporting {project_id} {date_str} G1#1>'
        assert str(sample_attendance_record) == expected


@pytest.mark.unit
class TestAttendanceDayLeaveModel:
    """اختبارات نموذج إجازة اليوم"""
    
    def test_day_leave_creation(self, db_session, sample_project, sample_employee):
        """اختبار إنشاء سجل إجازة يومية جديد"""
        leave = AttendanceDayLeave()
        leave.project_id = sample_project.id
        leave.date = date.today()
        leave.seq_no = 1
        leave.employee_id = sample_employee.id
        leave.leave_type = LeaveType.SICK
        leave.note = 'إجازة مرضية - نزلة برد'
        
        db_session.add(leave)
        db_session.commit()
        
        assert leave.id is not None
        assert leave.leave_type == LeaveType.SICK
        assert leave.note == 'إجازة مرضية - نزلة برد'
        assert leave.seq_no == 1
        
    def test_day_leave_types(self, db_session, sample_project, sample_employee):
        """اختبار أنواع الإجازات المختلفة"""
        leave_types = [
            (LeaveType.ANNUAL, 'إجازة سنوية'),
            (LeaveType.EMERGENCY, 'إجازة طارئة'),
            (LeaveType.OTHER, 'إجازة أخرى')
        ]
        
        for i, (leave_type, note) in enumerate(leave_types, 1):
            leave = AttendanceDayLeave()
            leave.project_id = sample_project.id
            leave.date = date.today()
            leave.seq_no = i
            leave.employee_id = sample_employee.id
            leave.leave_type = leave_type
            leave.note = note
            
            db_session.add(leave)
            
        db_session.commit()
        
        # التحقق من وجود جميع أنواع الإجازات
        leaves = AttendanceDayLeave.query.all()
        assert len(leaves) == 3
        leave_type_values = [leave.leave_type for leave in leaves]
        assert LeaveType.ANNUAL in leave_type_values
        assert LeaveType.EMERGENCY in leave_type_values
        assert LeaveType.OTHER in leave_type_values
        
    def test_day_leave_relationships(self, db_session, sample_project, sample_employee):
        """اختبار العلاقات في سجل الإجازة"""
        leave = AttendanceDayLeave()
        leave.project_id = sample_project.id
        leave.date = date.today()
        leave.seq_no = 1
        leave.employee_id = sample_employee.id
        leave.leave_type = LeaveType.ANNUAL
        leave.note = 'إجازة سنوية'
        
        db_session.add(leave)
        db_session.commit()
        
        assert leave.project is not None
        assert leave.employee is not None
        assert leave.project.name == 'مشروع الأمن'
        assert leave.employee.name == 'أحمد محمد'
        
    def test_day_leave_string_representation(self, db_session, sample_project, sample_employee):
        """اختبار التمثيل النصي لسجل الإجازة"""
        leave = AttendanceDayLeave()
        leave.project_id = sample_project.id
        leave.date = date.today()
        leave.seq_no = 1
        leave.employee_id = sample_employee.id
        leave.leave_type = LeaveType.ANNUAL
        
        db_session.add(leave)
        db_session.commit()
        
        project_id = leave.project_id
        date_str = leave.date
        expected = f'<AttendanceDayLeave {project_id} {date_str} #1>'
        assert str(leave) == expected


@pytest.mark.unit
class TestPMDailyEvaluationModel:
    """اختبارات نموذج التقييم اليومي لمسؤول المشروع"""
    
    def test_pm_evaluation_creation(self, db_session, sample_project, sample_employee, sample_dog):
        """اختبار إنشاء تقييم يومي جديد"""
        evaluation = PMDailyEvaluation()
        evaluation.project_id = sample_project.id
        evaluation.date = date.today()
        evaluation.group_no = 1
        evaluation.seq_no = 1
        evaluation.employee_id = sample_employee.id
        evaluation.dog_id = sample_dog.id
        evaluation.site_name = 'البوابة الرئيسية'
        evaluation.shift_name = 'الفترة الصباحية'
        
        # تقييم الفرد
        evaluation.uniform_ok = True
        evaluation.card_ok = True
        evaluation.appearance_ok = True
        evaluation.cleanliness_ok = True
        
        # رعاية الكلب
        evaluation.dog_exam_done = True
        evaluation.dog_fed = True
        evaluation.dog_watered = True
        
        # التدريب
        evaluation.training_tansheti = True
        evaluation.training_other = False
        
        # النزول الميداني
        evaluation.field_deployment_done = True
        
        # الأداء
        evaluation.perf_sais = 'ممتاز'
        evaluation.perf_dog = 'جيد'
        evaluation.perf_mudarrib = 'ممتاز'
        
        db_session.add(evaluation)
        db_session.commit()
        
        assert evaluation.id is not None
        assert evaluation.site_name == 'البوابة الرئيسية'
        assert evaluation.shift_name == 'الفترة الصباحية'
        assert evaluation.uniform_ok is True
        assert evaluation.dog_exam_done is True
        assert evaluation.perf_sais == 'ممتاز'
        
    def test_pm_evaluation_with_leave_replacement(self, db_session, sample_project, sample_employee, sample_dog):
        """اختبار التقييم مع سجل إجازة وبديل"""
        # إنشاء موظف بديل
        replacement = Employee()
        replacement.name = 'عبدالله حسن'
        replacement.employee_id = 'EMP003'
        replacement.role = EmployeeRole.HANDLER
        replacement.phone = '555666777'
        replacement.email = 'abdullah@example.com'
        replacement.hire_date = date(2023, 4, 1)
        
        db_session.add(replacement)
        db_session.commit()
        
        # تقييم مع إجازة وبديل
        evaluation = PMDailyEvaluation()
        evaluation.project_id = sample_project.id
        evaluation.date = date.today()
        evaluation.group_no = 1
        evaluation.seq_no = 1
        evaluation.employee_id = sample_employee.id
        
        # سجل الإجازة
        evaluation.is_on_leave_row = True
        evaluation.on_leave_employee_id = sample_employee.id
        evaluation.on_leave_type = LeaveType.SICK
        evaluation.on_leave_note = 'إجازة مرضية'
        
        # سجل البديل
        evaluation.is_replacement_row = True
        evaluation.replacement_employee_id = replacement.id
        evaluation.replacement_dog_id = sample_dog.id
        
        db_session.add(evaluation)
        db_session.commit()
        
        assert evaluation.is_on_leave_row is True
        assert evaluation.on_leave_type == LeaveType.SICK
        assert evaluation.is_replacement_row is True
        assert evaluation.replacement_employee_id == replacement.id
        
    def test_pm_evaluation_relationships(self, db_session, sample_project, sample_employee, sample_dog):
        """اختبار العلاقات في التقييم اليومي"""
        evaluation = PMDailyEvaluation()
        evaluation.project_id = sample_project.id
        evaluation.date = date.today()
        evaluation.group_no = 1
        evaluation.seq_no = 1
        evaluation.employee_id = sample_employee.id
        evaluation.dog_id = sample_dog.id
        
        db_session.add(evaluation)
        db_session.commit()
        
        assert evaluation.project is not None
        assert evaluation.employee is not None
        assert evaluation.dog is not None
        assert evaluation.project.name == 'مشروع الأمن'
        assert evaluation.employee.name == 'أحمد محمد'
        assert evaluation.dog.name == 'ريكس'
        
    def test_pm_evaluation_string_representation(self, db_session, sample_project, sample_employee):
        """اختبار التمثيل النصي للتقييم اليومي"""
        evaluation = PMDailyEvaluation()
        evaluation.project_id = sample_project.id
        evaluation.date = date.today()
        evaluation.group_no = 2
        evaluation.seq_no = 3
        evaluation.employee_id = sample_employee.id
        
        db_session.add(evaluation)
        db_session.commit()
        
        project_id = evaluation.project_id
        date_str = evaluation.date
        expected = f'<PMDailyEvaluation {project_id} {date_str} G2#3>'
        assert str(evaluation) == expected


@pytest.mark.unit
class TestAttendanceModelValidations:
    """اختبارات التحقق من صحة نماذج الحضور"""
    
    def test_attendance_unique_constraint(self, db_session, sample_project, sample_employee):
        """اختبار قيد الفرادة في سجل الحضور"""
        # إنشاء سجل حضور أول
        attendance1 = ProjectAttendanceReporting()
        attendance1.date = date.today()
        attendance1.project_id = sample_project.id
        attendance1.group_no = 1
        attendance1.seq_no = 1
        attendance1.employee_id = sample_employee.id
        
        db_session.add(attendance1)
        db_session.commit()
        
        # محاولة إنشاء سجل آخر بنفس المعرفات
        attendance2 = ProjectAttendanceReporting()
        attendance2.date = date.today()
        attendance2.project_id = sample_project.id
        attendance2.group_no = 1
        attendance2.seq_no = 1  # نفس المعرفات
        
        db_session.add(attendance2)
        
        # يجب أن يرفع خطأ بسبب انتهاك قيد الفرادة
        with pytest.raises(Exception):
            db_session.commit()
            
    def test_day_leave_unique_constraint(self, db_session, sample_project, sample_employee):
        """اختبار قيد الفرادة في سجل الإجازة اليومية"""
        # إنشاء سجل إجازة أول
        leave1 = AttendanceDayLeave()
        leave1.project_id = sample_project.id
        leave1.date = date.today()
        leave1.seq_no = 1
        leave1.employee_id = sample_employee.id
        leave1.leave_type = LeaveType.ANNUAL
        
        db_session.add(leave1)
        db_session.commit()
        
        # محاولة إنشاء سجل آخر بنفس المعرفات
        leave2 = AttendanceDayLeave()
        leave2.project_id = sample_project.id
        leave2.date = date.today()
        leave2.seq_no = 1  # نفس المعرفات
        leave2.leave_type = LeaveType.SICK
        
        db_session.add(leave2)
        
        # يجب أن يرفع خطأ بسبب انتهاك قيد الفرادة
        with pytest.raises(Exception):
            db_session.commit()


@pytest.mark.unit
class TestAttendanceStatusEnum:
    """اختبارات enum حالة الحضور"""
    
    def test_attendance_status_values(self):
        """اختبار قيم حالة الحضور"""
        assert AttendanceStatus.PRESENT.value == "PRESENT"
        assert AttendanceStatus.ABSENT.value == "ABSENT"
        assert AttendanceStatus.LATE.value == "LATE"
        assert AttendanceStatus.SICK.value == "SICK"
        assert AttendanceStatus.LEAVE.value == "LEAVE"
        assert AttendanceStatus.REMOTE.value == "REMOTE"
        assert AttendanceStatus.OVERTIME.value == "OVERTIME"
        
    def test_leave_type_values(self):
        """اختبار قيم أنواع الإجازات"""
        assert LeaveType.ANNUAL.value == "ANNUAL"
        assert LeaveType.SICK.value == "SICK"
        assert LeaveType.EMERGENCY.value == "EMERGENCY"
        assert LeaveType.OTHER.value == "OTHER"