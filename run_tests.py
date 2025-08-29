#!/usr/bin/env python3
"""
سكريبت تشغيل الاختبارات الشاملة للنظام
يتضمن اختبارات الوحدة واختبارات التكامل مع تقارير التغطية
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """تشغيل أمر مع وصف وإرجاع النتيجة"""
    print(f"\n{'='*60}")
    print(f"تشغيل: {description}")
    print(f"الأمر: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            check=False
        )
        
        print(f"رمز الإنهاء: {result.returncode}")
        
        if result.stdout:
            print("الإخراج:")
            print(result.stdout)
            
        if result.stderr:
            print("الأخطاء:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"خطأ في تشغيل الأمر: {e}")
        return False

def main():
    """تشغيل جميع الاختبارات"""
    print(f"بدء تشغيل الاختبارات الشاملة - {datetime.now()}")
    
    # التأكد من وجود مجلد الاختبارات
    if not os.path.exists('tests'):
        print("خطأ: مجلد الاختبارات غير موجود")
        sys.exit(1)
    
    success_count = 0
    total_tests = 0
    
    # قائمة الاختبارات المطلوب تشغيلها
    test_commands = [
        {
            'command': 'python -m pytest tests/unit/ -v --tb=short',
            'description': 'اختبارات الوحدة للنماذج والدوال'
        },
        {
            'command': 'python -m pytest tests/integration/ -v --tb=short',
            'description': 'اختبارات التكامل للحضور والتدريب'
        },
        {
            'command': 'python -m pytest tests/ -v --cov=. --cov-report=term-missing',
            'description': 'جميع الاختبارات مع تقرير التغطية'
        },
        {
            'command': 'python -m pytest tests/unit/test_models.py -v',
            'description': 'اختبارات النماذج الأساسية'
        },
        {
            'command': 'python -m pytest tests/unit/test_attendance_models.py -v',
            'description': 'اختبارات نماذج الحضور'
        }
    ]
    
    # تشغيل كل اختبار
    for test in test_commands:
        total_tests += 1
        if run_command(test['command'], test['description']):
            success_count += 1
            print(f"✅ نجح: {test['description']}")
        else:
            print(f"❌ فشل: {test['description']}")
    
    # تقرير النتائج النهائية
    print(f"\n{'='*80}")
    print(f"تقرير النتائج النهائية")
    print(f"{'='*80}")
    print(f"إجمالي الاختبارات: {total_tests}")
    print(f"نجح: {success_count}")
    print(f"فشل: {total_tests - success_count}")
    print(f"نسبة النجاح: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("🎉 جميع الاختبارات نجحت!")
        return 0
    else:
        print("⚠️  بعض الاختبارات فشلت")
        return 1

if __name__ == "__main__":
    sys.exit(main())