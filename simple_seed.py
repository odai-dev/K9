#!/usr/bin/env python3
"""
Simple seed script to add sample data to the K9 Operations Management System

This script creates realistic sample data that follows all current business rules:
- Only creates employee and dog sample data, no additional user accounts
- Projects are managed by the admin user only
- Project Managers (employees) can only be assigned to ONE active project at a time
- Projects have proper status transitions (PLANNED -> ACTIVE -> COMPLETED)
- Employees are properly assigned to projects with role-based permissions
- Dogs are assigned to projects and handlers appropriately
- All data follows the current database schema and validation rules
"""

from app import app, db
from models import (
    Dog, DogGender, DogStatus, Employee, EmployeeRole, 
    Project, ProjectStatus, User, UserRole
)
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
import uuid

def create_simple_data():
    with app.app_context():
        print("🌱 Adding sample data to K9 Operations Management System...")
        
        # Check if sample data already exists
        existing_dog = Dog.query.filter_by(code='K9-001').first()
        existing_employee = Employee.query.filter_by(employee_id='EMP-001').first()
        if existing_dog or existing_employee:
            print("⚠️ Sample data already exists. Skipping creation.")
            print("🔐 Login credentials:")
            print("   admin / admin123 (General Admin)")
            return
        
        try:
            # No additional users created - only admin user exists
            created_users = []
            
            # Create sample dogs
            dogs_data = [
                {
                    'name': 'ريكس',
                    'code': 'K9-001',
                    'breed': 'الراعي الألماني',
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
                    'breed': 'الراعي البلجيكي',
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
                    'breed': 'الروت وايلر',
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
                    'breed': 'اللابرادور',
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
                    'breed': 'الراعي الألماني', 
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
            
            created_dogs = []
            for dog_data in dogs_data:
                dog = Dog()
                for key, value in dog_data.items():
                    setattr(dog, key, value)
                db.session.add(dog)
                created_dogs.append(dog)
            
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
                }
            ]
            
            created_employees = []
            for emp_data in employees_data:
                employee = Employee()
                for key, value in emp_data.items():
                    setattr(employee, key, value)
                db.session.add(employee)
                created_employees.append(employee)
            
            # Commit employees first to get their IDs
            db.session.commit()
            
            # No project manager assignments - following updated business rules
            
            # Create sample projects following business rule: 
            # Project Manager can only be assigned to one ACTIVE project at a time
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
                    'manager_id': 1,  # admin user
                    'project_manager_id': None  # No project manager assignment
                },
                {
                    'name': 'تدريب الكلاب الجديدة 2025',
                    'code': 'PROJ-002',
                    'main_task': 'تدريب الكلاب الجديدة',
                    'description': 'برنامج تدريب شامل للكلاب الجديدة المنضمة للوحدة',
                    'start_date': date(2025, 2, 1),
                    'expected_completion_date': date(2025, 8, 31),
                    'status': ProjectStatus.PLANNED,  # PLANNED, not ACTIVE - respects the business rule
                    'location': 'مركز التدريب الرئيسي',
                    'mission_type': 'تدريب',
                    'priority': 'MEDIUM',
                    'manager_id': 1,  # admin user
                    'project_manager_id': None  # No PM assigned yet since this project is PLANNED
                },
                {
                    'name': 'مشروع أمن المطارات',
                    'code': 'PROJ-003',
                    'main_task': 'حراسة المطارات',
                    'description': 'تأمين المطارات الرئيسية باستخدام كلاب كشف المتفجرات',
                    'start_date': date(2025, 3, 15),
                    'expected_completion_date': date(2025, 11, 30),
                    'status': ProjectStatus.COMPLETED,  # COMPLETED project - allows PM reassignment
                    'location': 'مطارات متعددة',
                    'mission_type': 'أمن المطارات',
                    'priority': 'HIGH',
                    'manager_id': 1,  # admin user
                    'project_manager_id': None
                }
            ]
            
            created_projects = []
            for proj_data in projects_data:
                project = Project()
                for key, value in proj_data.items():
                    setattr(project, key, value)
                db.session.add(project)
                created_projects.append(project)
            
            # Commit projects first to establish their IDs properly
            db.session.commit()
            
            # Refresh all objects to ensure proper ID assignment
            for dog in created_dogs:
                db.session.refresh(dog)
            for emp in created_employees:
                db.session.refresh(emp)
            for proj in created_projects:
                db.session.refresh(proj)
            
            # Create assignments between dogs and projects only - no project manager assignments
            # Find the active project and assign some dogs to it
            active_project = None
            for project in created_projects:
                if project.status == ProjectStatus.ACTIVE:
                    active_project = project
                    break
                    
            if active_project:
                # Assign some dogs to the active project
                for dog in created_dogs[:3]:  # Assign first 3 dogs
                    active_project.assigned_dogs.append(dog)
            
            db.session.commit()
            
            print("✅ Sample data created successfully!")
            print("📊 Created:")
            print(f"   🐕 {len(created_dogs)} dogs")
            print(f"   👨‍💼 {len(created_employees)} employees")
            print(f"   📋 {len(created_projects)} projects")
            print()
            print("🔐 Login credentials:")
            print("   admin / admin123 (General Admin)")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating sample data: {e}")
            raise

if __name__ == '__main__':
    create_simple_data()