"""
خدمة إدارة المستخدمين
User Management Service
"""
from app import db
from k9.models.models import User, UserRole, Employee
from werkzeug.security import generate_password_hash
from typing import List, Dict, Optional
import secrets
import string
import openpyxl


class UserManagementService:
    """خدمة إدارة حسابات المستخدمين"""
    
    @staticmethod
    def generate_password(length: int = 12) -> str:
        """توليد كلمة مرور عشوائية آمنة"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    @staticmethod
    def create_handler_user(username: str, email: str, full_name: str,
                           phone: Optional[str] = None, project_id: Optional[str] = None,
                           dog_id: Optional[str] = None, password: Optional[str] = None) -> tuple:
        """إنشاء حساب سائس جديد"""
        # Check if username exists
        if User.query.filter_by(username=username).first():
            return None, None, f"اسم المستخدم {username} موجود مسبقاً"
        
        # Check if email exists
        if User.query.filter_by(email=email).first():
            return None, None, f"البريد الإلكتروني {email} موجود مسبقاً"
        
        # Generate password if not provided
        if not password:
            password = UserManagementService.generate_password()
        
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            password_hash=generate_password_hash(password),
            role=UserRole.HANDLER,
            phone=phone,
            project_id=project_id,
            dog_id=dog_id,
            active=True
        )
        
        db.session.add(user)
        db.session.commit()
        
        return user, password, None
    
    @staticmethod
    def bulk_import_from_excel(file_path: str) -> tuple:
        """استيراد جماعي من ملف Excel"""
        try:
            wb = openpyxl.load_workbook(file_path)
            ws = wb.active
            
            results = {
                'success': [],
                'errors': []
            }
            
            # Expected columns: name | username | phone | email | project_id | dog_id | password
            # Skip header row
            for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not row or all(cell is None for cell in row):
                    continue
                
                try:
                    name = row[0]
                    username = row[1]
                    phone = row[2] if len(row) > 2 else None
                    email = row[3] if len(row) > 3 else None
                    project_id = row[4] if len(row) > 4 else None
                    dog_id = row[5] if len(row) > 5 else None
                    password = row[6] if len(row) > 6 else None
                    
                    # Validate required fields
                    if not name or not username:
                        results['errors'].append({
                            'row': row_idx,
                            'error': 'الاسم واسم المستخدم مطلوبان'
                        })
                        continue
                    
                    # Generate email if not provided
                    if not email:
                        email = f"{username}@k9system.local"
                    
                    user, generated_password, error = UserManagementService.create_handler_user(
                        username=str(username).strip(),
                        email=str(email).strip(),
                        full_name=str(name).strip(),
                        phone=str(phone).strip() if phone else None,
                        project_id=str(project_id).strip() if project_id else None,
                        dog_id=str(dog_id).strip() if dog_id else None,
                        password=str(password).strip() if password else None
                    )
                    
                    if error:
                        results['errors'].append({
                            'row': row_idx,
                            'username': username,
                            'error': error
                        })
                    else:
                        results['success'].append({
                            'row': row_idx,
                            'username': username,
                            'password': generated_password,
                            'user_id': str(user.id)
                        })
                
                except Exception as e:
                    results['errors'].append({
                        'row': row_idx,
                        'error': str(e)
                    })
            
            return results, None
            
        except Exception as e:
            return None, f"خطأ في قراءة الملف: {str(e)}"
    
    @staticmethod
    def bulk_import_from_csv(file_path: str) -> tuple:
        """استيراد جماعي من ملف CSV"""
        import csv
        
        try:
            results = {
                'success': [],
                'errors': []
            }
            
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_idx, row in enumerate(reader, start=2):
                    try:
                        name = row.get('name', '').strip()
                        username = row.get('username', '').strip()
                        phone = row.get('phone', '').strip() or None
                        email = row.get('email', '').strip() or None
                        project_id = row.get('project_id', '').strip() or None
                        dog_id = row.get('dog_id', '').strip() or None
                        password = row.get('password', '').strip() or None
                        
                        if not name or not username:
                            results['errors'].append({
                                'row': row_idx,
                                'error': 'الاسم واسم المستخدم مطلوبان'
                            })
                            continue
                        
                        if not email:
                            email = f"{username}@k9system.local"
                        
                        user, generated_password, error = UserManagementService.create_handler_user(
                            username=username,
                            email=email,
                            full_name=name,
                            phone=phone,
                            project_id=project_id,
                            dog_id=dog_id,
                            password=password
                        )
                        
                        if error:
                            results['errors'].append({
                                'row': row_idx,
                                'username': username,
                                'error': error
                            })
                        else:
                            results['success'].append({
                                'row': row_idx,
                                'username': username,
                                'password': generated_password,
                                'user_id': str(user.id)
                            })
                    
                    except Exception as e:
                        results['errors'].append({
                            'row': row_idx,
                            'error': str(e)
                        })
            
            return results, None
            
        except Exception as e:
            return None, f"خطأ في قراءة الملف: {str(e)}"
    
    @staticmethod
    def deactivate_user(user_id: str) -> bool:
        """تعطيل حساب مستخدم"""
        user = User.query.get(user_id)
        if user:
            user.active = False
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def activate_user(user_id: str) -> bool:
        """تفعيل حساب مستخدم"""
        user = User.query.get(user_id)
        if user:
            user.active = True
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def reset_password(user_id: str, new_password: Optional[str] = None) -> tuple:
        """إعادة تعيين كلمة المرور"""
        user = User.query.get(user_id)
        if not user:
            return None, "المستخدم غير موجود"
        
        if not new_password:
            new_password = UserManagementService.generate_password()
        
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        return new_password, None
    
    @staticmethod
    def get_all_handlers(project_id: Optional[str] = None) -> List[User]:
        """الحصول على جميع السائسين"""
        query = User.query.filter_by(role=UserRole.HANDLER)
        
        if project_id:
            query = query.filter_by(project_id=project_id)
        
        return query.all()
