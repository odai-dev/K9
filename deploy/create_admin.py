#!/usr/bin/env python3
"""
K9 Operations Management System - Admin User Creation Script
Copy this file to /home/k9app/app/create_admin.py on your server

Usage:
    source venv/bin/activate
    export $(cat .env | xargs)
    python create_admin.py
"""
import os
import sys
import getpass

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from k9.models.models import User, UserRole
from werkzeug.security import generate_password_hash
import uuid

def create_admin():
    """Create the initial admin user"""
    with app.app_context():
        # Check if admin already exists
        existing = User.query.filter_by(username='admin').first()
        if existing:
            print("المستخدم 'admin' موجود بالفعل")
            response = input("هل تريد إعادة تعيين كلمة المرور؟ (y/n): ")
            if response.lower() != 'y':
                return
            
            # Reset password
            password = getpass.getpass("أدخل كلمة المرور الجديدة: ")
            confirm = getpass.getpass("تأكيد كلمة المرور: ")
            
            if password != confirm:
                print("كلمات المرور غير متطابقة!")
                return
            
            existing.password_hash = generate_password_hash(password)
            db.session.commit()
            print("تم تحديث كلمة المرور بنجاح!")
            return
        
        print("\n=== إنشاء حساب المشرف العام ===\n")
        
        # Get user input
        username = input("اسم المستخدم [admin]: ").strip() or 'admin'
        email = input("البريد الإلكتروني: ").strip()
        
        if not email:
            print("البريد الإلكتروني مطلوب!")
            return
        
        password = getpass.getpass("كلمة المرور: ")
        confirm = getpass.getpass("تأكيد كلمة المرور: ")
        
        if password != confirm:
            print("كلمات المرور غير متطابقة!")
            return
        
        if len(password) < 8:
            print("كلمة المرور يجب أن تكون 8 أحرف على الأقل!")
            return
        
        # Create the admin user
        admin = User()
        admin.id = str(uuid.uuid4())
        admin.username = username
        admin.email = email
        admin.password_hash = generate_password_hash(password)
        admin.role = UserRole.GENERAL_ADMIN
        admin.is_active = True
        
        db.session.add(admin)
        db.session.commit()
        
        print("\n✓ تم إنشاء حساب المشرف العام بنجاح!")
        print(f"  اسم المستخدم: {username}")
        print(f"  البريد الإلكتروني: {email}")
        print(f"  الدور: مشرف عام (GENERAL_ADMIN)")
        print("\n⚠️ تذكر: غير كلمة المرور الافتراضية بعد أول تسجيل دخول!")

if __name__ == '__main__':
    create_admin()
