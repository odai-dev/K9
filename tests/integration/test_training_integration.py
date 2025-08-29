"""
اختبارات التكامل للتدريب والأداء
تفحص تفاعل مكونات التدريب مع قاعدة البيانات والنظام
"""

import pytest
from datetime import date, datetime, timedelta
from models import (
    Project, Employee, Dog, TrainingSession, VeterinaryVisit, PerformanceEvaluation,
    UserRole, EmployeeRole, DogStatus, DogGender, TrainingCategory, ProjectStatus,
    VisitType, PerformanceRating
)


@pytest.mark.integration
@pytest.mark.database
class TestTrainingIntegration:
    """اختبارات تكامل نظام التدريب"""
    
    def test_complete_training_workflow(self, db_session):
        """اختبار سير العمل الكامل للتدريب"""
        # إنشاء البيانات الأساسية
        trainer = Employee()
        trainer.name = 'مدرب محترف'
        trainer.employee_id = 'TRAIN001'
        trainer.role = EmployeeRole.TRAINER
        trainer.phone = '555100200'
        trainer.email = 'trainer@example.com'
        trainer.hire_date = date(2023, 1, 1)
        
        dog = Dog()
        dog.name = 'شامبيون'
        dog.code = 'TDOG001'
        dog.breed = 'جيرمن شيبرد'
        dog.gender = DogGender.MALE
        dog.birth_date = date(2022, 3, 15)
        dog.status = DogStatus.TRAINING
        dog.weight = 38.0
        dog.height = 68.0
        dog.color = 'أسود وذهبي'
        
        project = Project()
        project.name = 'مشروع التدريب المتقدم'
        project.code = 'ADVTRAIN001'
        project.main_task = 'تدريب الكلاب على المهام المتقدمة'
        project.status = ProjectStatus.ACTIVE
        project.start_date = date.today() - timedelta(days=30)
        project.expected_completion_date = date.today() + timedelta(days=90)
        project.location = 'مركز التدريب الرئيسي'
        project.project_manager_id = trainer.id
        
        db_session.add_all([trainer, dog, project])
        db_session.commit()
        
        # برنامج تدريبي متدرج
        training_program = [
            (TrainingCategory.OBEDIENCE, 'تدريب الطاعة الأساسي', 60, 7),
            (TrainingCategory.OBEDIENCE, 'تدريب الطاعة المتقدم', 90, 8),
            (TrainingCategory.DETECTION, 'تدريب كشف المواد الأولي', 120, 6),
            (TrainingCategory.DETECTION, 'تدريب كشف المتفجرات', 150, 9),
            (TrainingCategory.AGILITY, 'تدريب الرشاقة والسرعة', 75, 8),
            (TrainingCategory.FITNESS, 'تدريب اللياقة البدنية', 45, 7),
        ]
        
        training_sessions = []
        for i, (category, subject, duration, rating) in enumerate(training_program):
            session = TrainingSession()
            session.dog_id = dog.id
            session.trainer_id = trainer.id
            session.project_id = project.id
            session.category = category
            session.subject = subject
            session.training_date = date.today() - timedelta(days=30-i*5)
            session.duration_minutes = duration
            session.success_rating = rating
            session.location = f'ساحة التدريب {i+1}'
            session.notes = f'تدريب {subject} - أداء {"ممتاز" if rating >= 8 else "جيد" if rating >= 6 else "يحتاج تحسين"}'
            session.weather_conditions = 'مناسب للتدريب'
            training_sessions.append(session)
            
        db_session.add_all(training_sessions)
        db_session.commit()
        
        # التحقق من التقدم في التدريب
        saved_sessions = TrainingSession.query.filter_by(
            dog_id=dog.id,
            project_id=project.id
        ).order_by(TrainingSession.training_date).all()
        
        assert len(saved_sessions) == 6
        
        # التحقق من تقدم الأداء
        average_rating = sum(session.success_rating for session in saved_sessions) / len(saved_sessions)
        assert average_rating >= 7.0  # متوسط أداء جيد
        
        # التحقق من تنوع التدريبات
        categories_covered = set(session.category for session in saved_sessions)
        assert TrainingCategory.OBEDIENCE in categories_covered
        assert TrainingCategory.DETECTION in categories_covered
        assert TrainingCategory.AGILITY in categories_covered
        assert TrainingCategory.FITNESS in categories_covered
        
        # التحقق من العلاقات
        for session in saved_sessions:
            assert session.dog.name == 'شامبيون'
            assert session.trainer.name == 'مدرب محترف'
            assert session.project.name == 'مشروع التدريب المتقدم'
            
    def test_training_with_veterinary_monitoring(self, db_session):
        """اختبار التدريب مع المتابعة البيطرية"""
        # إنشاء البيانات الأساسية
        trainer = Employee()
        trainer.name = 'مدرب التخصص'
        trainer.employee_id = 'SPEC001'
        trainer.role = EmployeeRole.TRAINER
        trainer.phone = '555200300'
        trainer.email = 'specialist@example.com'
        trainer.hire_date = date(2023, 2, 1)
        
        vet = Employee()
        vet.name = 'طبيب بيطري'
        vet.employee_id = 'VET001'
        vet.role = EmployeeRole.VET
        vet.phone = '555300400'
        vet.email = 'vet@example.com'
        vet.hire_date = date(2023, 1, 15)
        
        dog = Dog()
        dog.name = 'أطلس'
        dog.code = 'ATLAS001'
        dog.breed = 'بلجيكي مالينويز'
        dog.gender = DogGender.MALE
        dog.birth_date = date(2021, 8, 10)
        dog.status = DogStatus.TRAINING
        dog.weight = 32.0
        dog.height = 62.0
        dog.color = 'بني فاتح'
        
        project = Project()
        project.name = 'مشروع التدريب الطبي'
        project.code = 'MEDTRAIN001'
        project.main_task = 'تدريب مع متابعة طبية'
        project.status = ProjectStatus.ACTIVE
        project.start_date = date.today() - timedelta(days=15)
        project.location = 'مركز التدريب الطبي'
        
        db_session.add_all([trainer, vet, dog, project])
        db_session.commit()
        
        # برنامج تدريبي مكثف مع فحوصات دورية
        training_dates = [
            date.today() - timedelta(days=14),
            date.today() - timedelta(days=10),
            date.today() - timedelta(days=7),
            date.today() - timedelta(days=3),
        ]
        
        vet_checkup_dates = [
            date.today() - timedelta(days=15),  # فحص قبل البدء
            date.today() - timedelta(days=8),   # فحص أثناء التدريب
            date.today() - timedelta(days=1),   # فحص نهائي
        ]
        
        # إنشاء جلسات التدريب
        training_sessions = []
        for i, training_date in enumerate(training_dates):
            session = TrainingSession()
            session.dog_id = dog.id
            session.trainer_id = trainer.id
            session.project_id = project.id
            session.category = TrainingCategory.DETECTION
            session.subject = f'تدريب كشف متقدم - المرحلة {i+1}'
            session.training_date = training_date
            session.duration_minutes = 120 + i * 15  # تدريب أطول تدريجياً
            session.success_rating = 6 + i  # تحسن تدريجي
            session.location = 'ساحة التدريب المتخصص'
            session.notes = f'تدريب مكثف - المرحلة {i+1}'
            session.weather_conditions = 'مناسب'
            training_sessions.append(session)
            
        # إنشاء الفحوصات البيطرية
        vet_visits = []
        for i, visit_date in enumerate(vet_checkup_dates):
            visit = VeterinaryVisit()
            visit.dog_id = dog.id
            visit.vet_id = vet.id
            visit.project_id = project.id
            visit.visit_type = VisitType.ROUTINE
            visit.visit_date = datetime.combine(visit_date, datetime.min.time())
            visit.weight = 32.0 - i * 0.3  # فقدان وزن طفيف من التدريب
            visit.temperature = 38.2 + i * 0.1
            visit.heart_rate = 80 + i * 5
            visit.symptoms = 'فحص دوري' if i == 0 else 'متابعة التدريب المكثف'
            visit.diagnosis = 'الكلب بحالة صحية ممتازة'
            visit.treatment = 'لا يوجد علاج مطلوب'
            visit.notes = f'فحص دوري رقم {i+1} - متابعة برنامج التدريب'
            vet_visits.append(visit)
            
        db_session.add_all(training_sessions + vet_visits)
        db_session.commit()
        
        # التحقق من التكامل بين التدريب والرعاية الطبية
        saved_trainings = TrainingSession.query.filter_by(dog_id=dog.id).all()
        saved_visits = VeterinaryVisit.query.filter_by(dog_id=dog.id).all()
        
        assert len(saved_trainings) == 4
        assert len(saved_visits) == 3
        
        # التحقق من تحسن الأداء
        performance_improvement = saved_trainings[-1].success_rating - saved_trainings[0].success_rating
        assert performance_improvement >= 2  # تحسن بمقدار نقطتين على الأقل
        
        # التحقق من المتابعة الطبية
        weight_loss = saved_visits[0].weight - saved_visits[-1].weight
        assert 0 <= weight_loss <= 1.0  # فقدان وزن طبيعي من التدريب
        
        # التحقق من أن جميع الفحوصات تشير لحالة صحية جيدة
        for visit in saved_visits:
            assert 'ممتازة' in visit.diagnosis or 'جيدة' in visit.diagnosis
            
    def test_performance_evaluation_integration(self, db_session):
        """اختبار تكامل تقييم الأداء مع التدريب"""
        # إنشاء البيانات الأساسية
        trainer = Employee()
        trainer.name = 'مقيم الأداء'
        trainer.employee_id = 'EVAL001'
        trainer.role = EmployeeRole.TRAINER
        trainer.phone = '555400500'
        trainer.email = 'evaluator@example.com'
        trainer.hire_date = date(2023, 1, 1)
        
        handler = Employee()
        handler.name = 'سائس ماهر'
        handler.employee_id = 'HAND001'
        handler.role = EmployeeRole.HANDLER
        handler.phone = '555500600'
        handler.email = 'handler@example.com'
        handler.hire_date = date(2023, 2, 1)
        
        dog = Dog()
        dog.name = 'صقر'
        dog.code = 'FALCON001'
        dog.breed = 'جيرمن شيبرد'
        dog.gender = DogGender.MALE
        dog.birth_date = date(2021, 12, 1)
        dog.status = DogStatus.ACTIVE
        dog.weight = 35.0
        dog.height = 65.0
        dog.color = 'أسود'
        
        project = Project()
        project.name = 'مشروع تقييم الأداء'
        project.code = 'PERFEVAL001'
        project.main_task = 'تقييم أداء الفريق'
        project.status = ProjectStatus.ACTIVE
        project.start_date = date.today() - timedelta(days=20)
        project.location = 'مركز التقييم'
        
        db_session.add_all([trainer, handler, dog, project])
        db_session.commit()
        
        # تدريبات متنوعة
        training_sessions = []
        training_data = [
            (TrainingCategory.OBEDIENCE, 8, 'تدريب طاعة ممتاز'),
            (TrainingCategory.DETECTION, 9, 'كشف متفجرات بدقة عالية'),
            (TrainingCategory.AGILITY, 7, 'رشاقة جيدة تحتاج تحسين'),
            (TrainingCategory.ATTACK, 8, 'هجوم محكم ومنضبط'),
        ]
        
        for i, (category, rating, notes) in enumerate(training_data):
            session = TrainingSession()
            session.dog_id = dog.id
            session.trainer_id = trainer.id
            session.project_id = project.id
            session.category = category
            session.subject = f'تدريب {category.value}'
            session.training_date = date.today() - timedelta(days=15-i*3)
            session.duration_minutes = 90
            session.success_rating = rating
            session.location = 'ساحة التقييم'
            session.notes = notes
            training_sessions.append(session)
            
        # تقييمات الأداء
        evaluations = []
        
        # تقييم الموظف (السائس)
        employee_eval = PerformanceEvaluation()
        employee_eval.project_id = project.id
        employee_eval.target_employee_id = handler.id
        employee_eval.evaluation_date = date.today() - timedelta(days=5)
        employee_eval.rating = PerformanceRating.EXCELLENT
        employee_eval.uniform_ok = True
        employee_eval.id_card_ok = True
        employee_eval.appearance_ok = True
        employee_eval.cleanliness_ok = True
        employee_eval.punctuality = 9
        employee_eval.job_knowledge = 8
        employee_eval.teamwork = 9
        employee_eval.communication = 8
        employee_eval.strengths = 'التزام ممتاز ومعرفة جيدة بالكلاب'
        employee_eval.areas_for_improvement = 'تطوير مهارات التواصل'
        employee_eval.comments = 'سائس متميز يظهر التزاماً عالياً'
        evaluations.append(employee_eval)
        
        # تقييم الكلب
        dog_eval = PerformanceEvaluation()
        dog_eval.project_id = project.id
        dog_eval.target_dog_id = dog.id
        dog_eval.evaluation_date = date.today() - timedelta(days=3)
        dog_eval.rating = PerformanceRating.EXCELLENT
        dog_eval.obedience_level = 9
        dog_eval.detection_accuracy = 8
        dog_eval.physical_condition = 9
        dog_eval.handler_relationship = 9
        dog_eval.strengths = 'طاعة ممتازة وعلاقة قوية مع السائس'
        dog_eval.areas_for_improvement = 'تحسين دقة الكشف'
        dog_eval.comments = 'كلب متميز بأداء عالي'
        evaluations.append(dog_eval)
        
        db_session.add_all(training_sessions + evaluations)
        db_session.commit()
        
        # التحقق من التكامل
        saved_trainings = TrainingSession.query.filter_by(dog_id=dog.id).all()
        saved_evaluations = PerformanceEvaluation.query.filter_by(project_id=project.id).all()
        
        assert len(saved_trainings) == 4
        assert len(saved_evaluations) == 2
        
        # التحقق من متوسط الأداء في التدريب
        training_avg = sum(t.success_rating for t in saved_trainings) / len(saved_trainings)
        assert training_avg >= 8.0  # أداء ممتاز
        
        # التحقق من تقييمات الأداء
        employee_evaluation = next(e for e in saved_evaluations if e.target_employee_id is not None)
        dog_evaluation = next(e for e in saved_evaluations if e.target_dog_id is not None)
        
        assert employee_evaluation.rating == PerformanceRating.EXCELLENT
        assert dog_evaluation.rating == PerformanceRating.EXCELLENT
        assert employee_evaluation.target_employee.name == 'سائس ماهر'
        assert dog_evaluation.target_dog.name == 'صقر'
        
        # التحقق من الاتساق بين التدريب والتقييم
        # الكلب الذي حصل على تقييم ممتاز يجب أن يكون له أداء جيد في التدريب
        high_performance_sessions = [t for t in saved_trainings if t.success_rating >= 8]
        assert len(high_performance_sessions) >= 3  # معظم الجلسات بأداء عالي


@pytest.mark.integration
@pytest.mark.database
class TestTrainingProgressTracking:
    """اختبارات تتبع التقدم في التدريب"""
    
    def test_long_term_training_progress(self, db_session):
        """اختبار تتبع التقدم طويل المدى في التدريب"""
        # إنشاء مدرب وكلب للتتبع طويل المدى
        trainer = Employee()
        trainer.name = 'مدرب التطوير'
        trainer.employee_id = 'DEV001'
        trainer.role = EmployeeRole.TRAINER
        trainer.phone = '555600700'
        trainer.email = 'developer@example.com'
        trainer.hire_date = date(2023, 1, 1)
        
        dog = Dog()
        dog.name = 'نجم'
        dog.code = 'STAR001'
        dog.breed = 'لابرادور'
        dog.gender = DogGender.FEMALE
        dog.birth_date = date(2022, 1, 1)
        dog.status = DogStatus.TRAINING
        dog.weight = 28.0
        dog.height = 55.0
        dog.color = 'ذهبي'
        
        project = Project()
        project.name = 'مشروع التطوير المستمر'
        project.code = 'CONTDEV001'
        project.main_task = 'تطوير مهارات الكلاب بشكل مستمر'
        project.status = ProjectStatus.ACTIVE
        project.start_date = date.today() - timedelta(days=120)
        project.expected_completion_date = date.today() + timedelta(days=60)
        project.location = 'مركز التطوير'
        
        db_session.add_all([trainer, dog, project])
        db_session.commit()
        
        # برنامج تدريبي مدته 4 أشهر مع تقدم تدريجي
        training_phases = [
            # المرحلة الأولى: التأسيس (شهر 1)
            [(TrainingCategory.OBEDIENCE, 4, 'بداية التدريب'),
             (TrainingCategory.OBEDIENCE, 5, 'تحسن طفيف'),
             (TrainingCategory.OBEDIENCE, 6, 'أداء مقبول'),
             (TrainingCategory.OBEDIENCE, 7, 'تقدم جيد')],
            
            # المرحلة الثانية: التطوير (شهر 2)
            [(TrainingCategory.DETECTION, 5, 'بداية تدريب الكشف'),
             (TrainingCategory.DETECTION, 6, 'فهم أساسي'),
             (TrainingCategory.OBEDIENCE, 8, 'تطور في الطاعة'),
             (TrainingCategory.DETECTION, 7, 'تحسن في الكشف')],
            
            # المرحلة الثالثة: التقدم (شهر 3)
            [(TrainingCategory.AGILITY, 6, 'بداية تدريب الرشاقة'),
             (TrainingCategory.DETECTION, 8, 'كشف متقدم'),
             (TrainingCategory.OBEDIENCE, 9, 'طاعة ممتازة'),
             (TrainingCategory.AGILITY, 7, 'رشاقة جيدة')],
            
            # المرحلة الرابعة: الإتقان (شهر 4)
            [(TrainingCategory.FITNESS, 8, 'لياقة عالية'),
             (TrainingCategory.DETECTION, 9, 'كشف متميز'),
             (TrainingCategory.AGILITY, 8, 'رشاقة متقدمة'),
             (TrainingCategory.OBEDIENCE, 10, 'طاعة مثالية')],
        ]
        
        training_sessions = []
        session_date = date.today() - timedelta(days=120)
        
        for phase_index, phase in enumerate(training_phases):
            for week_index, (category, rating, notes) in enumerate(phase):
                session = TrainingSession()
                session.dog_id = dog.id
                session.trainer_id = trainer.id
                session.project_id = project.id
                session.category = category
                session.subject = f'{category.value} - المرحلة {phase_index + 1}'
                session.training_date = session_date
                session.duration_minutes = 60 + phase_index * 15  # مدة أطول مع التقدم
                session.success_rating = rating
                session.location = f'ساحة المرحلة {phase_index + 1}'
                session.notes = notes
                session.weather_conditions = 'مناسب'
                training_sessions.append(session)
                
                session_date += timedelta(days=7)  # جلسة كل أسبوع
                
        db_session.add_all(training_sessions)
        db_session.commit()
        
        # تحليل التقدم
        saved_sessions = TrainingSession.query.filter_by(
            dog_id=dog.id
        ).order_by(TrainingSession.training_date).all()
        
        assert len(saved_sessions) == 16  # 4 جلسات × 4 مراحل
        
        # تحليل التقدم في كل فئة
        obedience_sessions = [s for s in saved_sessions if s.category == TrainingCategory.OBEDIENCE]
        detection_sessions = [s for s in saved_sessions if s.category == TrainingCategory.DETECTION]
        agility_sessions = [s for s in saved_sessions if s.category == TrainingCategory.AGILITY]
        
        # التحقق من التحسن المستمر في الطاعة
        obedience_ratings = [s.success_rating for s in obedience_sessions]
        assert obedience_ratings == [4, 5, 6, 7, 8, 9, 10]  # تحسن مستمر
        
        # التحقق من التطور في الكشف
        detection_ratings = [s.success_rating for s in detection_sessions]
        assert all(r1 <= r2 for r1, r2 in zip(detection_ratings[:-1], detection_ratings[1:]))  # تطور مستمر
        
        # التحقق من الأداء العام
        overall_avg_early = sum(s.success_rating for s in saved_sessions[:4]) / 4
        overall_avg_late = sum(s.success_rating for s in saved_sessions[-4:]) / 4
        
        improvement = overall_avg_late - overall_avg_early
        assert improvement >= 3.0  # تحسن كبير بمرور الوقت
        
        # التحقق من تنوع التدريبات
        categories_used = set(s.category for s in saved_sessions)
        assert len(categories_used) >= 4  # استخدام فئات متنوعة
        
    def test_multi_dog_training_comparison(self, db_session):
        """اختبار مقارنة التدريب بين عدة كلاب"""
        # إنشاء مدرب واحد لعدة كلاب
        trainer = Employee()
        trainer.name = 'مدرب المقارنات'
        trainer.employee_id = 'COMP001'
        trainer.role = EmployeeRole.TRAINER
        trainer.phone = '555700800'
        trainer.email = 'comparator@example.com'
        trainer.hire_date = date(2023, 1, 1)
        
        # إنشاء 3 كلاب بخصائص مختلفة
        dogs_data = [
            ('برق', 'LIGHTNING001', 'جيرمن شيبرد', DogGender.MALE, 40.0, 70.0),
            ('نور', 'LIGHT001', 'لابرادور', DogGender.FEMALE, 30.0, 58.0),
            ('عاصفة', 'STORM001', 'بلجيكي مالينويز', DogGender.MALE, 35.0, 65.0),
        ]
        
        dogs = []
        for name, code, breed, gender, weight, height in dogs_data:
            dog = Dog()
            dog.name = name
            dog.code = code
            dog.breed = breed
            dog.gender = gender
            dog.birth_date = date(2022, 6, 1)
            dog.status = DogStatus.TRAINING
            dog.weight = weight
            dog.height = height
            dog.color = 'متنوع'
            dogs.append(dog)
            
        project = Project()
        project.name = 'مشروع المقارنة'
        project.code = 'COMPARE001'
        project.main_task = 'مقارنة أداء الكلاب في التدريب'
        project.status = ProjectStatus.ACTIVE
        project.start_date = date.today() - timedelta(days=30)
        project.location = 'مركز المقارنات'
        
        db_session.add_all([trainer] + dogs + [project])
        db_session.commit()
        
        # نفس البرنامج التدريبي لجميع الكلاب مع نتائج مختلفة
        training_schedule = [
            (TrainingCategory.OBEDIENCE, 'تدريب الطاعة الأساسي'),
            (TrainingCategory.DETECTION, 'تدريب كشف المواد'),
            (TrainingCategory.AGILITY, 'تدريب الرشاقة'),
            (TrainingCategory.FITNESS, 'تدريب اللياقة'),
        ]
        
        # نتائج مختلفة لكل كلب (تفسر الاختلافات الفردية)
        performance_patterns = [
            [8, 9, 7, 8],  # برق: ممتاز في الكشف
            [7, 6, 9, 7],  # نور: ممتازة في الرشاقة
            [9, 8, 8, 9],  # عاصفة: ممتاز بشكل عام
        ]
        
        training_sessions = []
        for dog_index, dog in enumerate(dogs):
            for exercise_index, (category, subject) in enumerate(training_schedule):
                session = TrainingSession()
                session.dog_id = dog.id
                session.trainer_id = trainer.id
                session.project_id = project.id
                session.category = category
                session.subject = f'{subject} - {dog.name}'
                session.training_date = date.today() - timedelta(days=25-exercise_index*5)
                session.duration_minutes = 90
                session.success_rating = performance_patterns[dog_index][exercise_index]
                session.location = 'ساحة المقارنة'
                session.notes = f'تدريب {dog.name} في {category.value}'
                training_sessions.append(session)
                
        db_session.add_all(training_sessions)
        db_session.commit()
        
        # تحليل المقارنة
        saved_sessions = TrainingSession.query.filter_by(project_id=project.id).all()
        assert len(saved_sessions) == 12  # 3 كلاب × 4 تمارين
        
        # حساب متوسط الأداء لكل كلب
        dog_averages = {}
        for dog in dogs:
            dog_sessions = [s for s in saved_sessions if s.dog_id == dog.id]
            dog_averages[dog.name] = sum(s.success_rating for s in dog_sessions) / len(dog_sessions)
            
        # التحقق من الأداء المتوقع
        assert dog_averages['عاصفة'] > dog_averages['برق'] > dog_averages['نور']
        
        # تحليل نقاط القوة لكل كلب
        for dog in dogs:
            dog_sessions = [s for s in saved_sessions if s.dog_id == dog.id]
            best_category = max(dog_sessions, key=lambda s: s.success_rating).category
            
            if dog.name == 'برق':
                assert best_category == TrainingCategory.DETECTION
            elif dog.name == 'نور':
                assert best_category == TrainingCategory.AGILITY
            elif dog.name == 'عاصفة':
                # يجب أن يكون متميز في عدة مجالات
                high_scores = [s for s in dog_sessions if s.success_rating >= 8]
                assert len(high_scores) >= 3