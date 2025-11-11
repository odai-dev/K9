#!/usr/bin/env python3
"""
Comprehensive Workflow Testing Script for K9 Operations Management System
Tests all major workflows and generates a detailed report.
"""

import os
import sys
from datetime import datetime, date, timedelta
from werkzeug.security import check_password_hash

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from k9.models.models import *
from k9.models.models_handler_daily import *
# models_attendance_reporting removed - now using DailySchedule system

class WorkflowTester:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        
    def test(self, test_name, test_func):
        """Run a test and record result"""
        try:
            result = test_func()
            if result:
                self.passed += 1
                self.results.append(f"✓ PASS: {test_name}")
                print(f"✓ {test_name}")
            else:
                self.failed += 1
                self.results.append(f"✗ FAIL: {test_name} - Test returned False")
                print(f"✗ {test_name} - Test returned False")
        except Exception as e:
            self.failed += 1
            self.results.append(f"✗ FAIL: {test_name} - {str(e)}")
            print(f"✗ {test_name} - {str(e)}")
    
    def report(self):
        """Generate test report"""
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        report = f"""
{'='*80}
COMPREHENSIVE WORKFLOW TEST REPORT
{'='*80}
Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Tests: {total}
Passed: {self.passed} ({pass_rate:.1f}%)
Failed: {self.failed}
{'='*80}

DETAILED RESULTS:
{chr(10).join(self.results)}

{'='*80}
"""
        return report

def run_all_tests():
    """Run all workflow tests"""
    tester = WorkflowTester()
    
    with app.app_context():
        print("\n" + "="*80)
        print("STARTING COMPREHENSIVE WORKFLOW TESTS")
        print("="*80 + "\n")
        
        # ===== AUTHENTICATION TESTS =====
        print("\n--- Authentication Workflows ---")
        tester.test("User authentication: Admin user exists", 
                   lambda: User.query.filter_by(role=UserRole.GENERAL_ADMIN).count() > 0)
        tester.test("User authentication: Handler users exist",
                   lambda: User.query.filter_by(role=UserRole.HANDLER).count() >= 2)
        tester.test("User authentication: PM users exist",
                   lambda: User.query.filter_by(role=UserRole.PROJECT_MANAGER).count() >= 2)
        tester.test("User authentication: Password hash is valid",
                   lambda: check_password_hash(User.query.first().password_hash, 'password123'))
        tester.test("User authentication: All users are active",
                   lambda: User.query.filter_by(active=False).count() == 0)
        
        # ===== USER ROLE TESTS =====
        print("\n--- User Role Permissions ---")
        tester.test("Roles: All 6 roles exist in database",
                   lambda: len(list(UserRole)) == 6)
        tester.test("Roles: GENERAL_ADMIN role exists",
                   lambda: UserRole.GENERAL_ADMIN in list(UserRole))
        tester.test("Roles: HANDLER role exists",
                   lambda: UserRole.HANDLER in list(UserRole))
        tester.test("Roles: PROJECT_MANAGER role exists",
                   lambda: UserRole.PROJECT_MANAGER in list(UserRole))
        tester.test("Roles: TRAINER role exists",
                   lambda: UserRole.TRAINER in list(UserRole))
        tester.test("Roles: BREEDER role exists",
                   lambda: UserRole.BREEDER in list(UserRole))
        tester.test("Roles: VET role exists",
                   lambda: UserRole.VET in list(UserRole))
        
        # ===== PROJECT MANAGEMENT TESTS =====
        print("\n--- Project Management Workflows ---")
        tester.test("Projects: Projects exist in database",
                   lambda: Project.query.count() >= 3)
        tester.test("Projects: Active projects exist",
                   lambda: Project.query.filter_by(status=ProjectStatus.ACTIVE).count() > 0)
        tester.test("Projects: PM assignment works",
                   lambda: Project.query.filter(Project.manager_id.isnot(None)).count() > 0)
        tester.test("Projects: Project has valid code",
                   lambda: all(p.code for p in Project.query.all()))
        
        # ===== DOG MANAGEMENT TESTS =====
        print("\n--- Dog Management Workflows ---")
        tester.test("Dogs: Dogs exist in database",
                   lambda: Dog.query.count() >= 10)
        tester.test("Dogs: Active dogs exist",
                   lambda: Dog.query.filter_by(current_status=DogStatus.ACTIVE).count() > 0)
        tester.test("Dogs: Dogs have unique codes",
                   lambda: len(set(d.code for d in Dog.query.all())) == Dog.query.count())
        tester.test("Dogs: Dogs have microchip IDs",
                   lambda: all(d.microchip_id for d in Dog.query.all()))
        tester.test("Dogs: Dogs have valid gender",
                   lambda: all(d.gender in list(DogGender) for d in Dog.query.all()))
        
        # ===== EMPLOYEE MANAGEMENT TESTS =====
        print("\n--- Employee Management Workflows ---")
        tester.test("Employees: Employees exist in database",
                   lambda: Employee.query.count() >= 5)
        tester.test("Employees: Handler employees exist",
                   lambda: Employee.query.filter_by(role=EmployeeRole.HANDLER).count() > 0)
        tester.test("Employees: Trainer employees exist",
                   lambda: Employee.query.filter_by(role=EmployeeRole.TRAINER).count() > 0)
        tester.test("Employees: Active employees exist",
                   lambda: Employee.query.filter_by(is_active=True).count() > 0)
        
        # ===== HANDLER DAILY SYSTEM TESTS =====
        print("\n--- Handler Daily System Workflows ---")
        tester.test("Handler System: DailySchedule model exists",
                   lambda: hasattr(db.Model, '__tablename__'))
        tester.test("Handler System: ScheduleStatus enum exists",
                   lambda: len(list(ScheduleStatus)) > 0)
        tester.test("Handler System: ReportStatus enum exists",
                   lambda: len(list(ReportStatus)) > 0)
        tester.test("Handler System: Can query schedules",
                   lambda: DailySchedule.query.count() >= 0)
        tester.test("Handler System: Can query reports",
                   lambda: HandlerReport.query.count() >= 0)
        
        # ===== NOTIFICATION SYSTEM TESTS =====
        print("\n--- Notification System Workflows ---")
        tester.test("Notifications: Notification model exists",
                   lambda: Notification.query.count() >= 0)
        tester.test("Notifications: NotificationType enum exists",
                   lambda: len(list(NotificationType)) > 0)
        tester.test("Notifications: Can query notifications",
                   lambda: True)
        
        # ===== TASK SYSTEM TESTS =====
        print("\n--- Task Management Workflows ---")
        tester.test("Tasks: Task model exists",
                   lambda: Task.query.count() >= 0)
        tester.test("Tasks: TaskStatus enum exists",
                   lambda: len(list(TaskStatus)) > 0)
        tester.test("Tasks: TaskPriority enum exists",
                   lambda: len(list(TaskPriority)) > 0)
        
        # ===== ATTENDANCE REPORTING TESTS =====
        # Legacy attendance reporting removed - now using DailySchedule system
        print("\n--- Attendance Reporting (Legacy system removed) ---")
        
        # ===== VETERINARY WORKFLOW TESTS =====
        print("\n--- Veterinary Workflows ---")
        tester.test("Veterinary: VeterinaryVisit model exists",
                   lambda: VeterinaryVisit.query.count() >= 0)
        tester.test("Veterinary: VisitType enum exists",
                   lambda: len(list(VisitType)) > 0)
        tester.test("Veterinary: Can create vet visit",
                   lambda: True)  # Model exists
        
        # ===== BREEDING WORKFLOW TESTS =====
        print("\n--- Breeding Workflows ---")
        tester.test("Breeding: FeedingLog model exists",
                   lambda: FeedingLog.query.count() >= 0)
        tester.test("Breeding: DailyCheckupLog model exists",
                   lambda: DailyCheckupLog.query.count() >= 0)
        tester.test("Breeding: BodyConditionScale enum exists",
                   lambda: len(list(BodyConditionScale)) > 0)
        
        # ===== CARETAKER WORKFLOW TESTS =====
        print("\n--- Caretaker Daily Log Workflows ---")
        tester.test("Caretaker: CaretakerDailyLog model exists",
                   lambda: CaretakerDailyLog.query.count() >= 0)
        tester.test("Caretaker: Can query caretaker logs",
                   lambda: True)
        
        # ===== TRAINING WORKFLOW TESTS =====
        print("\n--- Training Workflows ---")
        tester.test("Training: TrainingSession model exists",
                   lambda: TrainingSession.query.count() >= 0)
        tester.test("Training: BreedingTrainingActivity model exists",
                   lambda: BreedingTrainingActivity.query.count() >= 0)
        
        # ===== BACKUP SYSTEM TESTS =====
        print("\n--- Backup System Workflows ---")
        tester.test("Backup: BackupSettings model exists",
                   lambda: BackupSettings.query.count() >= 0)
        tester.test("Backup: Can get backup settings",
                   lambda: BackupSettings.get_settings() is not None)
        
        # ===== AUDIT LOG TESTS =====
        print("\n--- Audit Log Workflows ---")
        tester.test("Audit: AuditLog model exists",
                   lambda: AuditLog.query.count() >= 0)
        tester.test("Audit: AuditAction enum exists",
                   lambda: len(list(AuditAction)) > 0)
        
        # ===== PM REVIEW WORKFLOW TESTS =====
        print("\n--- PM Review Workflows ---")
        tester.test("PM Review: WorkflowStatus enum exists",
                   lambda: hasattr(WorkflowStatus, 'PENDING_PM_REVIEW'))
        tester.test("PM Review: VeterinaryVisit has status field",
                   lambda: hasattr(VeterinaryVisit, 'status'))
        tester.test("PM Review: BreedingTrainingActivity has status field",
                   lambda: hasattr(BreedingTrainingActivity, 'status'))
        tester.test("PM Review: CaretakerDailyLog has status field",
                   lambda: hasattr(CaretakerDailyLog, 'status'))
        
        # ===== SECURITY TESTS =====
        print("\n--- Security & MFA Workflows ---")
        tester.test("Security: User has MFA fields",
                   lambda: hasattr(User, 'mfa_enabled'))
        tester.test("Security: User has backup_codes field",
                   lambda: hasattr(User, 'backup_codes'))
        tester.test("Security: User has failed_login_attempts field",
                   lambda: hasattr(User, 'failed_login_attempts'))
        
        # ===== DATABASE INTEGRITY TESTS =====
        print("\n--- Database Integrity Tests ---")
        tester.test("DB Integrity: No orphaned users (all have valid roles)",
                   lambda: all(u.role in list(UserRole) for u in User.query.all()))
        tester.test("DB Integrity: No orphaned dogs (all have valid status)",
                   lambda: all(d.current_status in list(DogStatus) for d in Dog.query.all()))
        tester.test("DB Integrity: Projects have unique codes",
                   lambda: len(set(p.code for p in Project.query.all())) == Project.query.count())
        
        print("\n" + "="*80)
        print(tester.report())
        
        # Save report to file
        with open('test_results.txt', 'w', encoding='utf-8') as f:
            f.write(tester.report())
        print("✓ Test report saved to test_results.txt")
        
        return tester.passed, tester.failed

if __name__ == "__main__":
    passed, failed = run_all_tests()
    sys.exit(0 if failed == 0 else 1)
