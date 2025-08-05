#!/usr/bin/env python3
"""
Script to create sample data for the K9 Operations Management System
"""
from app import app, db
from models import (Dog, Employee, Project, User, UserRole, DogStatus, DogGender, 
                   EmployeeRole, ProjectStatus)
from werkzeug.security import generate_password_hash
from datetime import datetime, date
import uuid

def create_sample_data():
    with app.app_context():
        print("Creating sample data...")
        
        # Create sample dogs
        dogs_data = [
            {
                'name': 'ريكس',
                'code': 'K9-001',
                'breed': 'جيرمان شيبرد',
                'family_line': 'سلالة أ',
                'gender': DogGender.MALE,
                'birth_date': date(2020, 3, 15),
                'microchip_id': 'MC001REX',
                'current_status': DogStatus.ACTIVE,
                'location': 'المعسكر الأول',
                'specialization': 'كشف المتفجرات',
                'color': 'أسود وبني',
                'weight': 35.5,
                'height': 65.0
            },
            {
                'name': 'لونا',
                'code': 'K9-002',
                'breed': 'بلجيكان مالينوا',
                'family_line': 'سلالة ب',
                'gender': DogGender.FEMALE,
                'birth_date': date(2021, 1, 20),
                'microchip_id': 'MC002LUN',
                'current_status': DogStatus.ACTIVE,
                'location': 'المعسكر الثاني',
                'specialization': 'كشف المخدرات',
                'color': 'بني فاتح',
                'weight': 28.0,
                'height': 58.0
            },
            {
                'name': 'ماكس',
                'code': 'K9-003',
                'breed': 'روت وايلر',
                'family_line': 'سلالة ج',
                'gender': DogGender.MALE,
                'birth_date': date(2019, 8, 10),
                'microchip_id': 'MC003MAX',
                'current_status': DogStatus.ACTIVE,
                'location': 'المعسكر الأول',
                'specialization': 'الهجوم والحراسة',
                'color': 'أسود وبني',
                'weight': 45.0,
                'height': 70.0
            },
            {
                'name': 'بيلا',
                'code': 'K9-004',
                'breed': 'لابرادور',
                'family_line': 'سلالة د',
                'gender': DogGender.FEMALE,
                'birth_date': date(2022, 2, 5),
                'microchip_id': 'MC004BEL',
                'current_status': DogStatus.TRAINING,
                'location': 'مركز التدريب',
                'specialization': 'البحث والإنقاذ',
                'color': 'ذهبي',
                'weight': 25.0,
                'height': 55.0
            },
            {
                'name': 'شادو',
                'code': 'K9-005',
                'breed': 'جيرمان شيبرد',
                'family_line': 'سلالة أ',
                'gender': DogGender.MALE,
                'birth_date': date(2018, 11, 30),
                'microchip_id': 'MC005SHA',
                'current_status': DogStatus.RETIRED,
                'location': 'منطقة التقاعد',
                'specialization': 'خبير متعدد',
                'color': 'أسود',
                'weight': 40.0,
                'height': 68.0
            }
        ]
        
        for dog_data in dogs_data:
            dog = Dog(**dog_data)
            db.session.add(dog)
        
        # Create sample employees
        employees_data = [
            {
                'name': 'أحمد محمد السائس',
                'employee_id': 'EMP-001',
                'role': EmployeeRole.HANDLER,
                'phone': '0501234567',
                'email': 'ahmed.handler@k9ops.com',
                'hire_date': date(2020, 1, 15),
                'is_active': True,
                'certifications': ['شهادة سائس كلاب', 'دورة الإسعافات الأولية']
            },
            {
                'name': 'د. سارة علي الطبيبة',
                'employee_id': 'EMP-002',
                'role': EmployeeRole.VET,
                'phone': '0502345678',
                'email': 'sara.vet@k9ops.com',
                'hire_date': date(2019, 6, 1),
                'is_active': True,
                'certifications': ['دكتوراه في الطب البيطري', 'شهادة في طب الحيوانات المتخصصة']
            },
            {
                'name': 'خالد عبدالله المدرب',
                'employee_id': 'EMP-003',
                'role': EmployeeRole.TRAINER,
                'phone': '0503456789',
                'email': 'khaled.trainer@k9ops.com',
                'hire_date': date(2021, 3, 10),
                'is_active': True,
                'certifications': ['شهادة في تدريب الكلاب البوليسية', 'دورة السلوك الحيواني']
            },
            {
                'name': 'فهد سعد مسؤول المشروع',
                'employee_id': 'EMP-004',
                'role': EmployeeRole.PROJECT_MANAGER,
                'phone': '0504567890',
                'email': 'fahad.pm@k9ops.com',
                'hire_date': date(2018, 9, 1),
                'is_active': True,
                'certifications': ['ماجستير في إدارة المشاريع', 'شهادة PMP']
            },
            {
                'name': 'عمر حسن السائس',
                'employee_id': 'EMP-005',
                'role': EmployeeRole.HANDLER,
                'phone': '0505678901',
                'email': 'omar.handler@k9ops.com',
                'hire_date': date(2022, 1, 20),
                'is_active': True,
                'certifications': ['شهادة سائس كلاب مبتدئ']
            }
        ]
        
        for emp_data in employees_data:
            employee = Employee(**emp_data)
            db.session.add(employee)
        
        # Create sample projects
        projects_data = [
            {
                'name': 'مشروع أمن الحدود الشرقية',
                'code': 'PROJ-001',
                'main_task': 'تأمين الحدود الشرقية',
                'description': 'مشروع لتأمين الحدود الشرقية باستخدام الكلاب البوليسية المدربة على كشف المتفجرات والمخدرات',
                'start_date': date(2024, 1, 1),
                'expected_completion_date': date(2024, 12, 31),
                'status': ProjectStatus.ACTIVE,
                'location': 'المنطقة الشرقية',
                'mission_type': 'حراسة الحدود',
                'priority': 'HIGH',
                'manager_id': 1  # admin user
            },
            {
                'name': 'تدريب الكلاب الجديدة 2024',
                'code': 'PROJ-002',
                'main_task': 'تدريب الكلاب الجديدة',
                'description': 'برنامج تدريب شامل للكلاب الجديدة المنضمة للوحدة',
                'start_date': date(2024, 2, 1),
                'expected_completion_date': date(2024, 8, 31),
                'status': ProjectStatus.ACTIVE,
                'location': 'مركز التدريب الرئيسي',
                'mission_type': 'تدريب',
                'priority': 'MEDIUM',
                'manager_id': 1
            },
            {
                'name': 'مشروع أمن المطارات',
                'code': 'PROJ-003',
                'main_task': 'حراسة المطارات',
                'description': 'تأمين المطارات الرئيسية باستخدام كلاب كشف المتفجرات',
                'start_date': date(2024, 3, 15),
                'expected_completion_date': date(2024, 11, 30),
                'status': ProjectStatus.PLANNED,
                'location': 'مطارات متعددة',
                'mission_type': 'أمن المطارات',
                'priority': 'HIGH',
                'manager_id': 1
            }
        ]
        
        for proj_data in projects_data:
            project = Project(**proj_data)
            db.session.add(project)
        
        try:
            db.session.commit()
            print("✓ Sample data created successfully!")
            print("Created:")
            print(f"  - {len(dogs_data)} Dogs")
            print(f"  - {len(employees_data)} Employees") 
            print(f"  - {len(projects_data)} Projects")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating sample data: {e}")

if __name__ == '__main__':
    create_sample_data()