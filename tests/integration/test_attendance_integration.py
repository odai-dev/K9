"""
اختبارات التكامل للحضور والتقارير
تفحص تفاعل مكونات الحضور مع قاعدة البيانات والنظام
"""

import pytest
from datetime import date, time, datetime, timedelta
from models import Project, Employee, Dog, User, UserRole, EmployeeRole, DogStatus, DogGender, ProjectStatus
from models_attendance_reporting import (
    ProjectAttendanceReporting, AttendanceDayLeave, PMDailyEvaluation,
    AttendanceStatus, LeaveType
)


@pytest.mark.integration
@pytest.mark.database
class TestAttendanceIntegration:
    """اختبارات تكامل نظام الحضور"""
    
    def test_complete_attendance_workflow(self, db_session):
        """اختبار سير العمل الكامل للحضور"""
        # إنشاء البيانات الأساسية
        employee = Employee()
        employee.name = 'سالم أحمد'
        employee.employee_id = 'EMP100'
        employee.role = EmployeeRole.HANDLER
        employee.phone = '123456789'
        employee.email = 'salem@example.com'
        employee.hire_date = date(2023, 1, 1)
        employee.active = True
        
        project = Project()
        project.name = 'مشروع تجريبي'
        project.code = 'TEST001'
        project.main_task = 'اختبار النظام'
        project.description = 'مشروع للاختبار'
        project.status = ProjectStatus.ACTIVE
        project.start_date = date.today()
        project.location = 'الرياض'
        project.priority = 'HIGH'
        
        db_session.add_all([employee, project])
        db_session.commit()
        
        # إنشاء سجل حضور
        attendance = ProjectAttendanceReporting()
        attendance.date = date.today()
        attendance.project_id = project.id
        attendance.employee_id = employee.id
        attendance.group_no = 1
        attendance.seq_no = 1
        attendance.check_in_time = time(8, 0)
        attendance.check_out_time = time(16, 0)
        attendance.status = AttendanceStatus.PRESENT
        
        db_session.add(attendance)
        db_session.commit()
        
        # التحقق من صحة البيانات
        saved_attendance = ProjectAttendanceReporting.query.filter_by(
            project_id=project.id,
            employee_id=employee.id,
            date=date.today()
        ).first()
        
        assert saved_attendance is not None
        assert saved_attendance.status == AttendanceStatus.PRESENT
        assert saved_attendance.project.name == 'مشروع تجريبي'
        assert saved_attendance.employee.name == 'سالم أحمد'
        
    def test_attendance_with_leave_management(self, db_session):
        """اختبار إدارة الحضور مع الإجازات"""
        # إنشاء البيانات الأساسية
        employee1 = Employee()
        employee1.name = 'أحمد محمد'
        employee1.employee_id = 'EMP101'
        employee1.role = EmployeeRole.TRAINER
        employee1.phone = '111222333'
        employee1.email = 'ahmed@example.com'
        employee1.hire_date = date(2023, 2, 1)
        
        employee2 = Employee()
        employee2.name = 'محمد سالم'
        employee2.employee_id = 'EMP102'
        employee2.role = EmployeeRole.TRAINER
        employee2.phone = '444555666'
        employee2.email = 'mohammed@example.com'
        employee2.hire_date = date(2023, 3, 1)
        
        project = Project()
        project.name = 'مشروع الإجازات'
        project.code = 'LEAVE001'
        project.main_task = 'اختبار إدارة الإجازات'
        project.status = ProjectStatus.ACTIVE
        project.start_date = date.today()
        project.location = 'جدة'
        
        db_session.add_all([employee1, employee2, project])
        db_session.commit()
        
        # الموظف الأول في إجازة
        leave = AttendanceDayLeave()
        leave.project_id = project.id
        leave.date = date.today()
        leave.seq_no = 1
        leave.employee_id = employee1.id
        leave.leave_type = LeaveType.SICK
        leave.note = 'إجازة مرضية - نزلة برد'
        
        # الموظف الثاني يحضر كبديل
        attendance = ProjectAttendanceReporting()
        attendance.date = date.today()
        attendance.project_id = project.id
        attendance.employee_id = employee1.id  # الموظف الأصلي
        attendance.substitute_employee_id = employee2.id  # البديل
        attendance.group_no = 1
        attendance.seq_no = 1
        attendance.status = AttendanceStatus.ABSENT
        
        db_session.add_all([leave, attendance])
        db_session.commit()
        
        # التحقق من صحة البيانات
        saved_leave = AttendanceDayLeave.query.filter_by(
            project_id=project.id,
            employee_id=employee1.id,
            date=date.today()
        ).first()
        
        saved_attendance = ProjectAttendanceReporting.query.filter_by(
            project_id=project.id,
            date=date.today()
        ).first()
        
        assert saved_leave is not None
        assert saved_leave.leave_type == LeaveType.SICK
        assert saved_leave.employee.name == 'أحمد محمد'
        
        assert saved_attendance is not None
        assert saved_attendance.status == AttendanceStatus.ABSENT
        assert saved_attendance.substitute_employee.name == 'محمد سالم'
        
    def test_pm_daily_evaluation_workflow(self, db_session):
        """اختبار سير عمل التقييم اليومي لمسؤول المشروع"""
        # إنشاء البيانات الأساسية
        employee = Employee()
        employee.name = 'عبدالرحمن خالد'
        employee.employee_id = 'EMP103'
        employee.role = EmployeeRole.HANDLER
        employee.phone = '777888999'
        employee.email = 'abdulrahman@example.com'
        employee.hire_date = date(2023, 4, 1)
        
        dog = Dog()
        dog.name = 'تايجر'
        dog.code = 'DOG100'
        dog.breed = 'جيرمن شيبرد'
        dog.gender = DogGender.MALE
        dog.birth_date = date(2022, 1, 15)
        dog.status = DogStatus.ACTIVE
        dog.weight = 40.0
        dog.height = 70.0
        dog.color = 'أسود وبني'
        
        project = Project()
        project.name = 'مشروع التقييم'
        project.code = 'EVAL001'
        project.main_task = 'اختبار نظام التقييم'
        project.status = ProjectStatus.ACTIVE
        project.start_date = date.today()
        project.location = 'الدمام'
        project.project_manager_id = employee.id
        
        db_session.add_all([employee, dog, project])
        db_session.commit()
        
        # إنشاء تقييم يومي شامل
        evaluation = PMDailyEvaluation()
        evaluation.project_id = project.id
        evaluation.date = date.today()
        evaluation.group_no = 1
        evaluation.seq_no = 1
        evaluation.employee_id = employee.id
        evaluation.dog_id = dog.id
        evaluation.site_name = 'البوابة الشمالية'
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
        
        # تقييم الأداء
        evaluation.perf_sais = 'ممتاز'
        evaluation.perf_dog = 'جيد'
        evaluation.perf_mudarrib = 'ممتاز'
        evaluation.perf_sehi = 'جيد'
        
        # ملاحظات المخالفات
        evaluation.violations = 'لا توجد مخالفات'
        
        db_session.add(evaluation)
        db_session.commit()
        
        # التحقق من صحة البيانات
        saved_evaluation = PMDailyEvaluation.query.filter_by(
            project_id=project.id,
            date=date.today(),
            employee_id=employee.id
        ).first()
        
        assert saved_evaluation is not None
        assert saved_evaluation.site_name == 'البوابة الشمالية'
        assert saved_evaluation.uniform_ok is True
        assert saved_evaluation.dog_exam_done is True
        assert saved_evaluation.perf_sais == 'ممتاز'
        assert saved_evaluation.violations == 'لا توجد مخالفات'
        assert saved_evaluation.employee.name == 'عبدالرحمن خالد'
        assert saved_evaluation.dog.name == 'تايجر'
        
    def test_attendance_data_consistency(self, db_session):
        """اختبار اتساق البيانات في النظام"""
        # إنشاء مشروع مع عدة موظفين وكلاب
        project = Project()
        project.name = 'مشروع الاتساق'
        project.code = 'CONSIST001'
        project.main_task = 'اختبار اتساق البيانات'
        project.status = ProjectStatus.ACTIVE
        project.start_date = date.today()
        project.location = 'مكة المكرمة'
        
        employees = []
        dogs = []
        
        # إنشاء 3 موظفين
        for i in range(1, 4):
            employee = Employee()
            employee.name = f'موظف {i}'
            employee.employee_id = f'EMP20{i}'
            employee.role = EmployeeRole.HANDLER
            employee.phone = f'55512345{i}'
            employee.email = f'employee{i}@example.com'
            employee.hire_date = date(2023, i, 1)
            employees.append(employee)
            
        # إنشاء 3 كلاب
        for i in range(1, 4):
            dog = Dog()
            dog.name = f'كلب {i}'
            dog.code = f'DOG20{i}'
            dog.breed = 'جيرمن شيبرد'
            dog.gender = DogGender.MALE if i % 2 else DogGender.FEMALE
            dog.birth_date = date(2022, i, 1)
            dog.status = DogStatus.ACTIVE
            dog.weight = 30.0 + i * 2
            dog.height = 60.0 + i * 3
            dog.color = f'لون {i}'
            dogs.append(dog)
            
        db_session.add(project)
        db_session.add_all(employees)
        db_session.add_all(dogs)
        db_session.commit()
        
        # إنشاء سجلات حضور لكل موظف
        attendance_records = []
        for i, employee in enumerate(employees, 1):
            attendance = ProjectAttendanceReporting()
            attendance.date = date.today()
            attendance.project_id = project.id
            attendance.employee_id = employee.id
            attendance.dog_id = dogs[i-1].id  # ربط كل موظف بكلب
            attendance.group_no = 1
            attendance.seq_no = i
            attendance.check_in_time = time(8, 0)
            attendance.check_out_time = time(16, 0)
            attendance.status = AttendanceStatus.PRESENT
            attendance_records.append(attendance)
            
        db_session.add_all(attendance_records)
        db_session.commit()
        
        # التحقق من اتساق البيانات
        project_attendances = ProjectAttendanceReporting.query.filter_by(
            project_id=project.id,
            date=date.today()
        ).all()
        
        assert len(project_attendances) == 3
        
        # التحقق من أن كل سجل حضور مرتبط بموظف وكلب صحيحين
        for attendance in project_attendances:
            assert attendance.employee is not None
            assert attendance.dog is not None
            assert attendance.project is not None
            assert attendance.employee.name.startswith('موظف')
            assert attendance.dog.name.startswith('كلب')
            assert attendance.project.name == 'مشروع الاتساق'


@pytest.mark.integration
@pytest.mark.database
class TestAttendanceQueryPerformance:
    """اختبارات أداء استعلامات الحضور"""
    
    def test_attendance_queries_with_large_dataset(self, db_session):
        """اختبار الاستعلامات مع مجموعة بيانات كبيرة"""
        # إنشاء مشروع كبير
        project = Project()
        project.name = 'مشروع كبير'
        project.code = 'BIG001'
        project.main_task = 'اختبار الأداء'
        project.status = ProjectStatus.ACTIVE
        project.start_date = date.today() - timedelta(days=30)
        project.location = 'الرياض'
        
        db_session.add(project)
        db_session.commit()
        
        # إنشاء عدد كبير من الموظفين
        employees = []
        for i in range(1, 21):  # 20 موظف
            employee = Employee()
            employee.name = f'موظف كبير {i}'
            employee.employee_id = f'BIGE{i:03d}'
            employee.role = EmployeeRole.HANDLER
            employee.phone = f'5551234{i:02d}'
            employee.email = f'bigemp{i}@example.com'
            employee.hire_date = date(2023, 1, 1)
            employees.append(employee)
            
        db_session.add_all(employees)
        db_session.commit()
        
        # إنشاء سجلات حضور لمدة 30 يوم
        attendance_records = []
        for day_offset in range(30):
            current_date = date.today() - timedelta(days=day_offset)
            for i, employee in enumerate(employees, 1):
                attendance = ProjectAttendanceReporting()
                attendance.date = current_date
                attendance.project_id = project.id
                attendance.employee_id = employee.id
                attendance.group_no = 1 if i <= 10 else 2
                attendance.seq_no = i if i <= 10 else i - 10
                attendance.check_in_time = time(8, 0)
                attendance.check_out_time = time(16, 0)
                attendance.status = AttendanceStatus.PRESENT
                attendance_records.append(attendance)
                
        db_session.add_all(attendance_records)
        db_session.commit()
        
        # اختبار استعلامات مختلفة
        
        # 1. استعلام حسب التاريخ والمشروع
        start_time = datetime.now()
        daily_attendance = ProjectAttendanceReporting.query.filter_by(
            project_id=project.id,
            date=date.today()
        ).all()
        query_time_1 = (datetime.now() - start_time).total_seconds()
        
        assert len(daily_attendance) == 20
        assert query_time_1 < 1.0  # يجب أن يكون أقل من ثانية واحدة
        
        # 2. استعلام حسب الفترة الزمنية
        start_time = datetime.now()
        week_attendance = ProjectAttendanceReporting.query.filter(
            ProjectAttendanceReporting.project_id == project.id,
            ProjectAttendanceReporting.date >= date.today() - timedelta(days=7),
            ProjectAttendanceReporting.date <= date.today()
        ).all()
        query_time_2 = (datetime.now() - start_time).total_seconds()
        
        assert len(week_attendance) == 160  # 20 موظف × 8 أيام
        assert query_time_2 < 2.0  # يجب أن يكون أقل من ثانيتين
        
        # 3. استعلام مع join
        start_time = datetime.now()
        attendance_with_employee = db_session.query(ProjectAttendanceReporting).join(
            Employee
        ).filter(
            ProjectAttendanceReporting.project_id == project.id,
            ProjectAttendanceReporting.date == date.today(),
            Employee.active == True
        ).all()
        query_time_3 = (datetime.now() - start_time).total_seconds()
        
        assert len(attendance_with_employee) == 20
        assert query_time_3 < 1.5  # يجب أن يكون أقل من ثانية ونصف


@pytest.mark.integration
@pytest.mark.database
class TestAttendanceBusinessLogic:
    """اختبارات المنطق التجاري للحضور"""
    
    def test_attendance_status_transitions(self, db_session):
        """اختبار انتقالات حالة الحضور"""
        # إنشاء البيانات الأساسية
        employee = Employee()
        employee.name = 'موظف الانتقالات'
        employee.employee_id = 'TRANS001'
        employee.role = EmployeeRole.HANDLER
        employee.phone = '555000111'
        employee.email = 'transitions@example.com'
        employee.hire_date = date(2023, 1, 1)
        
        project = Project()
        project.name = 'مشروع الانتقالات'
        project.code = 'TRANS001'
        project.main_task = 'اختبار انتقالات الحالة'
        project.status = ProjectStatus.ACTIVE
        project.start_date = date.today()
        project.location = 'الرياض'
        
        db_session.add_all([employee, project])
        db_session.commit()
        
        # سيناريوهات مختلفة لحالات الحضور
        test_scenarios = [
            (AttendanceStatus.PRESENT, time(8, 0), time(16, 0)),
            (AttendanceStatus.LATE, time(8, 30), time(16, 0)),
            (AttendanceStatus.ABSENT, None, None),
            (AttendanceStatus.SICK, None, None),
            (AttendanceStatus.LEAVE, None, None),
            (AttendanceStatus.REMOTE, time(9, 0), time(17, 0)),
            (AttendanceStatus.OVERTIME, time(8, 0), time(18, 0)),
        ]
        
        attendance_records = []
        for i, (status, check_in, check_out) in enumerate(test_scenarios, 1):
            attendance = ProjectAttendanceReporting()
            attendance.date = date.today() - timedelta(days=i)
            attendance.project_id = project.id
            attendance.employee_id = employee.id
            attendance.group_no = 1
            attendance.seq_no = i
            attendance.check_in_time = check_in
            attendance.check_out_time = check_out
            attendance.status = status
            attendance_records.append(attendance)
            
        db_session.add_all(attendance_records)
        db_session.commit()
        
        # التحقق من صحة السيناريوهات
        saved_records = ProjectAttendanceReporting.query.filter_by(
            project_id=project.id,
            employee_id=employee.id
        ).order_by(ProjectAttendanceReporting.seq_no).all()
        
        assert len(saved_records) == 7
        
        # التحقق من كل سيناريو
        for i, (expected_status, expected_check_in, expected_check_out) in enumerate(test_scenarios):
            record = saved_records[i]
            assert record.status == expected_status
            assert record.check_in_time == expected_check_in
            assert record.check_out_time == expected_check_out
            
    def test_leave_type_business_rules(self, db_session):
        """اختبار قواعد العمل لأنواع الإجازات"""
        # إنشاء البيانات الأساسية
        employee = Employee()
        employee.name = 'موظف الإجازات'
        employee.employee_id = 'LEAVE001'
        employee.role = EmployeeRole.TRAINER
        employee.phone = '555000222'
        employee.email = 'leaves@example.com'
        employee.hire_date = date(2023, 1, 1)
        
        project = Project()
        project.name = 'مشروع الإجازات'
        project.code = 'LEAVE001'
        project.main_task = 'اختبار أنواع الإجازات'
        project.status = ProjectStatus.ACTIVE
        project.start_date = date.today()
        project.location = 'جدة'
        
        db_session.add_all([employee, project])
        db_session.commit()
        
        # أنواع مختلفة من الإجازات مع ملاحظاتها
        leave_scenarios = [
            (LeaveType.ANNUAL, 'إجازة سنوية - راحة'),
            (LeaveType.SICK, 'إجازة مرضية - التهاب حلق'),
            (LeaveType.EMERGENCY, 'إجازة طارئة - ظروف عائلية'),
            (LeaveType.OTHER, 'إجازة أخرى - مناسبة شخصية'),
        ]
        
        leave_records = []
        for i, (leave_type, note) in enumerate(leave_scenarios, 1):
            leave = AttendanceDayLeave()
            leave.project_id = project.id
            leave.date = date.today() - timedelta(days=i)
            leave.seq_no = i
            leave.employee_id = employee.id
            leave.leave_type = leave_type
            leave.note = note
            leave_records.append(leave)
            
        db_session.add_all(leave_records)
        db_session.commit()
        
        # التحقق من صحة البيانات
        saved_leaves = AttendanceDayLeave.query.filter_by(
            project_id=project.id,
            employee_id=employee.id
        ).order_by(AttendanceDayLeave.seq_no).all()
        
        assert len(saved_leaves) == 4
        
        # التحقق من كل نوع إجازة
        for i, (expected_type, expected_note) in enumerate(leave_scenarios):
            leave = saved_leaves[i]
            assert leave.leave_type == expected_type
            assert leave.note == expected_note
            
        # إحصائيات الإجازات
        annual_leaves = [l for l in saved_leaves if l.leave_type == LeaveType.ANNUAL]
        sick_leaves = [l for l in saved_leaves if l.leave_type == LeaveType.SICK]
        emergency_leaves = [l for l in saved_leaves if l.leave_type == LeaveType.EMERGENCY]
        other_leaves = [l for l in saved_leaves if l.leave_type == LeaveType.OTHER]
        
        assert len(annual_leaves) == 1
        assert len(sick_leaves) == 1
        assert len(emergency_leaves) == 1
        assert len(other_leaves) == 1