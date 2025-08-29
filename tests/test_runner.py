#!/usr/bin/env python3
"""
سكريبت تشغيل اختبارات التقارير الشامل
يشغل جميع اختبارات النظام مع تقارير مفصلة
"""

import subprocess
import sys
import os
import time
from datetime import datetime

def run_command(command, description):
    """تشغيل أمر مع عرض النتائج"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    execution_time = time.time() - start_time
    
    print(f"⏱️  وقت التنفيذ: {execution_time:.2f} ثانية")
    
    if result.returncode == 0:
        print(f"✅ {description} - نجح")
        if result.stdout:
            print(f"📊 النتائج:\n{result.stdout}")
    else:
        print(f"❌ {description} - فشل")
        if result.stderr:
            print(f"🚨 الأخطاء:\n{result.stderr}")
        if result.stdout:
            print(f"📄 المخرجات:\n{result.stdout}")
    
    return result.returncode == 0

def main():
    """تشغيل جميع اختبارات النظام"""
    print(f"""
    🎯 نظام اختبارات التقارير الشامل
    {'='*50}
    التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    المسار: {os.getcwd()}
    """)
    
    # قائمة الاختبارات
    tests = [
        # اختبارات الوحدة - القاعدة العريضة لهرم الاختبارات
        {
            "command": "python -m pytest tests/unit/test_reports_services.py -v --tb=short",
            "description": "اختبارات الوحدة - خدمات التقارير"
        },
        {
            "command": "python -m pytest tests/unit/test_reports_exporters.py -v --tb=short",
            "description": "اختبارات الوحدة - مصدرات التقارير"
        },
        {
            "command": "python -m pytest tests/unit/ -m 'unit and reports' -v",
            "description": "جميع اختبارات الوحدة للتقارير"
        },
        
        # اختبارات التكامل - الطبقة الوسطى
        {
            "command": "python -m pytest tests/integration/test_reports_integration.py -v --tb=short",
            "description": "اختبارات التكامل - تدفق البيانات بين الوحدات"
        },
        {
            "command": "python -m pytest tests/integration/test_reports_performance.py -v --tb=short",
            "description": "اختبارات الأداء - مجموعات البيانات الكبيرة"
        },
        
        # اختبارات النهاية إلى النهاية - القمة المدببة
        {
            "command": "python -m pytest tests/e2e/test_reports_e2e.py -v --tb=short",
            "description": "اختبارات النهاية إلى النهاية - سيناريوهات المستخدم الكاملة"
        },
        
        # اختبارات خاصة
        {
            "command": "python -m pytest tests/ -m 'export' -v",
            "description": "اختبارات التصدير - PDF/Excel/CSV"
        },
        {
            "command": "python -m pytest tests/ -m 'slow' -v --maxfail=3",
            "description": "الاختبارات البطيئة - الأداء والقابلية للتوسع"
        },
        
        # تغطية شاملة
        {
            "command": "python -m pytest tests/ --cov=attendance_reporting_services --cov=trainer_daily_services --cov-report=term-missing --cov-report=html",
            "description": "تقرير التغطية الشامل"
        }
    ]
    
    results = []
    successful_tests = 0
    
    for test in tests:
        success = run_command(test["command"], test["description"])
        results.append({
            "description": test["description"],
            "success": success
        })
        if success:
            successful_tests += 1
    
    # تقرير النتائج النهائي
    print(f"\n{'='*60}")
    print(f"📋 ملخص النتائج النهائي")
    print(f"{'='*60}")
    
    for result in results:
        status = "✅ نجح" if result["success"] else "❌ فشل"
        print(f"{status} - {result['description']}")
    
    print(f"\n📊 إجمالي النتائج:")
    print(f"✅ نجح: {successful_tests}")
    print(f"❌ فشل: {len(results) - successful_tests}")
    print(f"📈 معدل النجاح: {(successful_tests/len(results)*100):.1f}%")
    
    if successful_tests == len(results):
        print(f"\n🎉 تهانينا! جميع الاختبارات نجحت")
        print(f"✨ نظام التقارير جاهز للإنتاج")
        return 0
    else:
        print(f"\n⚠️  بعض الاختبارات فشلت، يرجى مراجعة الأخطاء")
        return 1

if __name__ == "__main__":
    sys.exit(main())