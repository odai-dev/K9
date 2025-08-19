#!/usr/bin/env python3
"""
Simple Sample Data Creator for K9 Operations System
Creates basic employees, projects, and dogs for testing unified matrix
"""

import os
import sys
from datetime import datetime, timedelta
from uuid import uuid4

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import (
    User, UserRole, Employee, EmployeeRole, Project, ProjectStatus,
    Dog, DogStatus, DogGender
)
from werkzeug.security import generate_password_hash

def create_simple_data():
    """Create simple sample data without complex attendance records"""
    with app.app_context():
        print("Creating simple sample data...")
        
        # Clear existing data (except admin user)
        print("Clearing existing data...")
        Dog.query.delete()
        Project.query.delete()
        Employee.query.delete()
        
        # Keep admin user, remove others
        User.query.filter(User.username != 'admin').delete()
        
        db.session.commit()
        
        # Create sample employees
        print("Creating employees...")
        employees = []
        
        # Employee 1: Handler
        emp1 = Employee()
        emp1.id = str(uuid4())
        emp1.employee_id = "EMP001"
        emp1.name = "أحمد محمد علي"
        emp1.role = EmployeeRole.HANDLER
        emp1.phone = "+966501234567"
        emp1.email = "ahmed.ali@k9ops.com"
        emp1.hire_date = datetime(2023, 1, 15).date()
        emp1.is_active = True
        employees.append(emp1)
        
        # Employee 2: Handler  
        emp2 = Employee()
        emp2.id = str(uuid4())
        emp2.employee_id = "EMP002"
        emp2.name = "فاطمة سعد الأحمد"
        emp2.role = EmployeeRole.HANDLER
        emp2.phone = "+966502345678"
        emp2.email = "fatima.saad@k9ops.com"
        emp2.hire_date = datetime(2023, 3, 20).date()
        emp2.is_active = True
        employees.append(emp2)
        
        # Employee 3: Trainer
        emp3 = Employee()
        emp3.id = str(uuid4())
        emp3.employee_id = "EMP003"
        emp3.name = "خالد عبدالله المطيري"
        emp3.role = EmployeeRole.TRAINER
        emp3.phone = "+966503456789"
        emp3.email = "khalid.mutairi@k9ops.com"
        emp3.hire_date = datetime(2022, 11, 10).date()
        emp3.is_active = True
        employees.append(emp3)
        
        # Employee 4: Veterinarian
        emp4 = Employee()
        emp4.id = str(uuid4())
        emp4.employee_id = "EMP004"
        emp4.name = "د. سارة أحمد الزهراني"
        emp4.role = EmployeeRole.VET
        emp4.phone = "+966504567890"
        emp4.email = "sara.zahrani@k9ops.com"
        emp4.hire_date = datetime(2022, 8, 5).date()
        emp4.is_active = True
        employees.append(emp4)
        
        # Employee 5: Project Manager
        emp5 = Employee()
        emp5.id = str(uuid4())
        emp5.employee_id = "EMP005"
        emp5.name = "محمد سالم القحطاني"
        emp5.role = EmployeeRole.PROJECT_MANAGER
        emp5.phone = "+966505678901"
        emp5.email = "mohammed.qahtani@k9ops.com"
        emp5.hire_date = datetime(2022, 6, 1).date()
        emp5.is_active = True
        employees.append(emp5)
        
        # Save employees
        for emp in employees:
            db.session.add(emp)
        
        # Create Project Manager user
        pm_user = User()
        pm_user.username = 'pm_mohammed'
        pm_user.email = 'mohammed.qahtani@k9ops.com'
        pm_user.password_hash = generate_password_hash('pm123')
        pm_user.role = UserRole.PROJECT_MANAGER
        pm_user.full_name = 'محمد سالم القحطاني'
        pm_user.active = True
        db.session.add(pm_user)
        
        db.session.commit()
        print(f"Created {len(employees)} employees")
        
        # Create sample projects
        print("Creating projects...")
        projects = []
        
        # Project 1: Border Security
        proj1 = Project()
        proj1.id = str(uuid4())
        proj1.name = "أمن الحدود الجنوبية"
        proj1.code = "PROJ001"
        proj1.description = "مشروع تأمين الحدود الجنوبية باستخدام الكلاب البوليسية المدربة"
        proj1.status = ProjectStatus.ACTIVE
        proj1.start_date = datetime(2024, 1, 15).date()
        proj1.location = "منطقة الحدود الجنوبية"
        proj1.project_manager_id = emp5.id
        proj1.created_at = datetime.now()
        projects.append(proj1)
        
        # Project 2: Airport Security
        proj2 = Project()
        proj2.id = str(uuid4())
        proj2.name = "أمن المطارات"
        proj2.code = "PROJ002"
        proj2.description = "مشروع كشف المتفجرات والمواد المخدرة في المطارات الدولية"
        proj2.status = ProjectStatus.ACTIVE
        proj2.start_date = datetime(2024, 3, 1).date()
        proj2.location = "مطار الملك عبدالعزيز الدولي"
        proj2.project_manager_id = emp5.id
        proj2.created_at = datetime.now()
        projects.append(proj2)
        
        # Save projects
        for proj in projects:
            db.session.add(proj)
        
        db.session.commit()
        print(f"Created {len(projects)} projects")
        
        # Create sample dogs
        print("Creating dogs...")
        dogs = []
        
        # Dog 1: German Shepherd
        dog1 = Dog()
        dog1.id = str(uuid4())
        dog1.name = "ريكس"
        dog1.code = "DOG001"
        dog1.breed = "German Shepherd"
        dog1.gender = DogGender.MALE
        dog1.birth_date = datetime(2020, 5, 15).date()
        dog1.current_status = DogStatus.ACTIVE
        dog1.microchip_id = "123456789012345"
        dog1.weight = 35.0
        dog1.height = 65.0
        dog1.color = "بني وأسود"
        dogs.append(dog1)
        
        # Dog 2: Belgian Malinois
        dog2 = Dog()
        dog2.id = str(uuid4())
        dog2.name = "لونا"
        dog2.code = "DOG002"
        dog2.breed = "Belgian Malinois"
        dog2.gender = DogGender.FEMALE
        dog2.birth_date = datetime(2021, 3, 20).date()
        dog2.current_status = DogStatus.ACTIVE
        dog2.microchip_id = "234567890123456"
        dog2.weight = 28.0
        dog2.height = 58.0
        dog2.color = "بني فاتح"
        dogs.append(dog2)
        
        # Dog 3: German Shepherd
        dog3 = Dog()
        dog3.id = str(uuid4())
        dog3.name = "ماكس"
        dog3.code = "DOG003"
        dog3.breed = "German Shepherd"
        dog3.gender = DogGender.MALE
        dog3.birth_date = datetime(2019, 8, 10).date()
        dog3.current_status = DogStatus.ACTIVE
        dog3.microchip_id = "345678901234567"
        dog3.weight = 38.0
        dog3.height = 67.0
        dog3.color = "أسود"
        dogs.append(dog3)
        
        # Save dogs
        for dog in dogs:
            db.session.add(dog)
        
        db.session.commit()
        print(f"Created {len(dogs)} dogs")
        
        print("\n✅ Simple sample data creation completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Employees: {len(employees)}")
        print(f"   - Projects: {len(projects)}")
        print(f"   - Dogs: {len(dogs)}")
        
        print(f"\n🔐 Login Credentials:")
        print(f"   Admin: admin / admin123")
        print(f"   Project Manager: pm_mohammed / pm123")

if __name__ == "__main__":
    create_simple_data()