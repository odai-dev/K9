# Handler Daily System - Technical Documentation

## Overview
نظام شامل لإدارة العمليات اليومية للسائسين (K9 Handlers) في وحدات الكلاب العسكرية/الشرطية، مع دعم كامل للغة العربية وRTL.

## Database Schema

### New Tables

#### 1. DailySchedule
جدول الجداول اليومية - يحتوي على جدول العمل اليومي لكل مشروع.

**Columns:**
- `id` (UUID, PK)
- `date` (Date, Required) - التاريخ
- `project_id` (UUID, FK → Project, Nullable) - المشروع
- `status` (Enum: OPEN, LOCKED) - الحالة
- `created_by_user_id` (UUID, FK → User)
- `notes` (Text, Nullable)
- `created_at`, `updated_at` (Timestamps)

**Indexes:**
- `idx_daily_schedule_date` على `date`
- `idx_daily_schedule_project` على `project_id`

**Relationships:**
- `schedule_items` → DailyScheduleItem (1:N)
- `handler_reports` → HandlerReport (1:N)

---

#### 2. DailyScheduleItem
عناصر الجدول اليومي - تحديد السائس والكلب والوردية لكل يوم.

**Columns:**
- `id` (UUID, PK)
- `daily_schedule_id` (UUID, FK → DailySchedule, Required)
- `employee_id` (UUID, FK → Employee, Required) - السائس المخطط
- `dog_id` (UUID, FK → Dog, Nullable) - الكلب المخصص
- `shift_id` (UUID, FK → Shift, Nullable) - الوردية
- `status` (Enum: PLANNED, PRESENT, ABSENT, REPLACED) - الحالة
- `absence_reason` (Text, Nullable) - سبب الغياب
- `replacement_employee_id` (UUID, FK → Employee, Nullable) - البديل
- `replacement_notes` (Text, Nullable)
- `created_at`, `updated_at` (Timestamps)

**Indexes:**
- `idx_schedule_item_schedule` على `daily_schedule_id`
- `idx_schedule_item_employee` على `employee_id`

**Relationships:**
- `schedule` → DailySchedule (N:1)
- `employee` → Employee (N:1)
- `dog` → Dog (N:1)
- `shift` → Shift (N:1)
- `replacement_employee` → Employee (N:1)
- `handler_reports` → HandlerReport (1:N)

---

#### 3. HandlerReport
التقارير اليومية للسائس - تقرير شامل عن اليوم.

**Columns:**
- `id` (UUID, PK)
- `date` (Date, Required)
- `handler_user_id` (UUID, FK → User, Required) - السائس
- `schedule_item_id` (UUID, FK → DailyScheduleItem, Nullable)
- `dog_id` (UUID, FK → Dog, Required)
- `project_id` (UUID, FK → Project, Nullable)
- `shift_id` (UUID, FK → Shift, Nullable)
- `status` (Enum: DRAFT, SUBMITTED, APPROVED, REJECTED) - الحالة
- `location` (String(200), Nullable) - الموقع
- `submitted_at` (DateTime, Nullable)
- `reviewed_by_user_id` (UUID, FK → User, Nullable)
- `reviewed_at` (DateTime, Nullable)
- `review_notes` (Text, Nullable)
- `created_at`, `updated_at` (Timestamps)

**Indexes:**
- `idx_handler_report_date` على `date`
- `idx_handler_report_handler` على `handler_user_id`
- `idx_handler_report_status` على `status`

**Relationships:**
- `health` → HandlerReportHealth (1:1)
- `training` → HandlerReportTraining (1:N)
- `care` → HandlerReportCare (1:1)
- `behavior` → HandlerReportBehavior (1:1)
- `incidents` → HandlerReportIncident (1:N)
- `attachments` → HandlerReportAttachment (1:N)

---

#### 4. HandlerReportHealth
الفحص الصحي اليومي للكلب.

**Columns:**
- `id` (UUID, PK)
- `report_id` (UUID, FK → HandlerReport, Required)
- `overall_condition` (String(50)) - الحالة العامة
- `appetite` (String(50)) - الشهية
- `energy_level` (String(50)) - مستوى النشاط
- `temperature` (Decimal(4,2), Nullable) - الحرارة
- `weight` (Decimal(5,2), Nullable) - الوزن
- `coat_condition` (String(100), Nullable) - حالة الفراء
- `injuries` (Text, Nullable) - إصابات
- `medications` (JSON, Default=[]) - الأدوية
- `vet_visit_needed` (Boolean, Default=False)
- `vet_visit_reason` (Text, Nullable)
- `notes` (Text, Nullable)

---

#### 5. HandlerReportTraining
سجل التدريبات اليومية.

**Columns:**
- `id` (UUID, PK)
- `report_id` (UUID, FK → HandlerReport, Required)
- `training_type` (String(100)) - نوع التدريب
- `duration_minutes` (Integer) - المدة بالدقائق
- `performance_rating` (Integer, 1-5) - التقييم
- `skills_practiced` (JSON, Default=[]) - المهارات
- `notes` (Text, Nullable)

---

#### 6. HandlerReportCare
الرعاية اليومية (تغذية، نظافة، إخراج).

**Columns:**
- `id` (UUID, PK)
- `report_id` (UUID, FK → HandlerReport, Required)
- `feeding_times` (JSON, Default=[])
- `food_amount_kg` (Decimal(5,2), Nullable)
- `water_consumption` (String(50), Nullable)
- `grooming_done` (Boolean, Default=False)
- `grooming_notes` (Text, Nullable)
- `exercise_duration_minutes` (Integer, Nullable)
- `exercise_type` (String(100), Nullable)
- `bathroom_breaks` (Integer, Default=0)
- `stool_condition` (String(50), Nullable)
- `notes` (Text, Nullable)

---

#### 7. HandlerReportBehavior
ملاحظات سلوكية.

**Columns:**
- `id` (UUID, PK)
- `report_id` (UUID, FK → HandlerReport, Required)
- `mood` (String(50)) - المزاج
- `obedience_level` (String(50)) - الطاعة
- `aggression_signs` (Boolean, Default=False)
- `anxiety_signs` (Boolean, Default=False)
- `social_interactions` (Text, Nullable)
- `unusual_behaviors` (Text, Nullable)
- `notes` (Text, Nullable)

---

#### 8. HandlerReportIncident
الحوادث والطوارئ.

**Columns:**
- `id` (UUID, PK)
- `report_id` (UUID, FK → HandlerReport, Required)
- `incident_time` (DateTime, Required)
- `incident_type` (String(100)) - نوع الحادث
- `severity` (String(50)) - الخطورة
- `description` (Text, Required)
- `action_taken` (Text, Nullable)
- `witnesses` (JSON, Default=[])
- `reported_to_supervisor` (Boolean, Default=False)

---

#### 9. HandlerReportAttachment
المرفقات (صور، ملفات PDF).

**Columns:**
- `id` (UUID, PK)
- `report_id` (UUID, FK → HandlerReport, Required)
- `file_type` (String(50)) - نوع الملف
- `file_path` (String(500)) - المسار
- `file_size` (Integer) - الحجم بالبايتات
- `file_hash` (String(64)) - SHA256
- `description` (Text, Nullable)
- `uploaded_at` (DateTime)

---

#### 10. Notification
نظام الإشعارات في الوقت الفعلي.

**Columns:**
- `id` (UUID, PK)
- `user_id` (UUID, FK → User, Required) - المستلم
- `notification_type` (Enum) - النوع
- `title` (String(200)) - العنوان
- `message` (Text) - الرسالة
- `read` (Boolean, Default=False)
- `related_type` (String(100), Nullable) - نوع الكائن المرتبط
- `related_id` (UUID, Nullable) - معرف الكائن
- `created_at` (DateTime)

**Notification Types:**
- `SCHEDULE_CREATED` - جدول جديد
- `SCHEDULE_UPDATED` - تحديث الجدول
- `EMPLOYEE_REPLACED` - تم استبدالك
- `REPORT_SUBMITTED` - تقرير جديد
- `REPORT_APPROVED` - تم اعتماد التقرير
- `REPORT_REJECTED` - تم رفض التقرير
- `REPORT_DUE_SOON` - التقرير قريب الاستحقاق
- `REPORT_OVERDUE` - التقرير متأخر

**Indexes:**
- `idx_notification_user` على `user_id`
- `idx_notification_read` على `read`

---

### Modified Tables

#### User Table Additions
تم توسيع جدول User بالحقول التالية:

```python
# New fields
role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.GENERAL_ADMIN)
phone = db.Column(db.String(20), nullable=True)
project_id = db.Column(UUID, db.ForeignKey('project.id'), nullable=True)
dog_id = db.Column(UUID, db.ForeignKey('dog.id'), nullable=True)
active = db.Column(db.Boolean, default=True, nullable=False)

# New UserRole Enum values
class UserRole(Enum):
    GENERAL_ADMIN = "GENERAL_ADMIN"
    PROJECT_MANAGER = "PROJECT_MANAGER"
    HANDLER = "HANDLER"  # NEW
```

---

## Services Layer

### 1. DailyScheduleService
إدارة الجداول اليومية.

**Methods:**
- `create_schedule(date, project_id, created_by_user_id, notes)` - إنشاء جدول
- `add_schedule_item(schedule_id, employee_id, dog_id, shift_id)` - إضافة عنصر
- `mark_present(item_id)` - تسجيل حضور
- `mark_absent(item_id, reason)` - تسجيل غياب
- `replace_employee(item_id, replacement_employee_id, reason, notes)` - استبدال سائس
- `lock_schedule(schedule_id)` - إقفال الجدول
- `get_handler_schedule_for_date(handler_user_id, target_date)` - جدول السائس

---

### 2. HandlerReportService
إدارة التقارير اليومية.

**Methods:**
- `create_report(handler_user_id, date, dog_id, ...)` - إنشاء تقرير
- `submit_report(report_id)` - إرسال للمراجعة
- `approve_report(report_id, reviewer_user_id, notes)` - اعتماد
- `reject_report(report_id, reviewer_user_id, notes)` - رفض
- `add_training_log(report_id, training_type, duration, ...)` - إضافة تدريب
- `add_incident(report_id, incident_time, incident_type, ...)` - إضافة حادث
- `add_attachment(report_id, file_type, file_path, ...)` - إضافة مرفق
- `can_submit_report(handler_user_id, schedule_item_id)` - التحقق من الصلاحية

---

### 3. NotificationService
إدارة الإشعارات.

**Methods:**
- `create_notification(user_id, notification_type, title, message, ...)` - إنشاء
- `mark_as_read(notification_id)` - تعليم كمقروء
- `mark_all_as_read(user_id)` - تعليم الكل
- `get_unread_notifications(user_id, limit)` - غير المقروءة
- `get_all_notifications(user_id, limit, offset)` - الكل
- `get_unread_count(user_id)` - العدد

---

### 4. UserManagementService
إدارة المستخدمين.

**Methods:**
- `create_handler_user(username, email, full_name, phone, project_id, dog_id)` - إنشاء سائس
- `bulk_import_users(file_path, default_role)` - استيراد جماعي
- `deactivate_user(user_id)` - تعطيل حساب
- `activate_user(user_id)` - تفعيل حساب
- `update_user_project(user_id, project_id)` - تحديث المشروع
- `generate_password()` - توليد كلمة مرور

---

## Routes & Blueprints

### 1. handler_routes.py
`/handler/*` - مسارات السائسين

**Endpoints:**
- `GET /handler/dashboard` - لوحة التحكم
- `GET /handler/reports/new` - تقرير جديد
- `POST /handler/reports/new` - إنشاء تقرير
- `GET /handler/reports/<id>/edit` - تعديل تقرير
- `POST /handler/reports/<id>/edit` - حفظ تعديلات
- `POST /handler/reports/<id>/submit` - إرسال للمراجعة
- `GET /handler/reports/<id>` - عرض التقرير
- `GET /handler/notifications` - الإشعارات
- `POST /handler/notifications/<id>/mark-read` - تعليم كمقروء
- `POST /handler/notifications/mark-all-read` - تعليم الكل

**Decorators:**
- `@login_required` - تسجيل دخول مطلوب
- `@handler_required` - سائس فقط

---

### 2. schedule_routes.py
`/supervisor/schedules/*` - إدارة الجداول

**Endpoints:**
- `GET /supervisor/schedules` - قائمة الجداول
- `GET /supervisor/schedules/create` - نموذج إنشاء
- `POST /supervisor/schedules/create` - إنشاء جدول
- `GET /supervisor/schedules/<id>` - عرض الجدول
- `GET /supervisor/schedules/<id>/edit` - تعديل
- `POST /supervisor/schedules/<id>/edit` - حفظ
- `POST /supervisor/schedules/<id>/lock` - إقفال
- `POST /supervisor/schedules/items/<id>/present` - حضور
- `POST /supervisor/schedules/items/<id>/absent` - غياب
- `POST /supervisor/schedules/items/<id>/replace` - استبدال
- `GET /supervisor/reports` - قائمة التقارير
- `GET /supervisor/reports/<id>` - عرض التقرير
- `POST /supervisor/reports/<id>/approve` - اعتماد
- `POST /supervisor/reports/<id>/reject` - رفض

**Decorators:**
- `@login_required`
- `@supervisor_required` - مشرف/مدير مشروع فقط

---

### 3. user_management_routes.py
`/admin/users/*` - إدارة المستخدمين

**Endpoints:**
- `GET /admin/users` - قائمة المستخدمين
- `GET /admin/users/create` - إنشاء مستخدم
- `POST /admin/users/create` - حفظ مستخدم
- `GET /admin/users/bulk-import` - استيراد جماعي
- `POST /admin/users/bulk-import` - رفع ملف
- `GET /admin/users/template` - تحميل قالب Excel
- `GET /admin/users/<id>/edit` - تعديل
- `POST /admin/users/<id>/edit` - حفظ تعديلات
- `POST /admin/users/<id>/deactivate` - تعطيل
- `POST /admin/users/<id>/activate` - تفعيل

**Decorators:**
- `@login_required`
- `@admin_required` - مدير عام فقط

---

## Configuration (config.py)

### Handler Daily System Settings

```python
# Handler Report Settings
HANDLER_REPORT_GRACE_MINUTES = int(os.environ.get('HANDLER_REPORT_GRACE_MINUTES', 240))  # 4 hours

# Schedule Auto-Lock Settings
SCHEDULE_AUTO_LOCK_HOUR = int(os.environ.get('SCHEDULE_AUTO_LOCK_HOUR', 23))  # 11 PM
SCHEDULE_AUTO_LOCK_MINUTE = int(os.environ.get('SCHEDULE_AUTO_LOCK_MINUTE', 59))  # 11:59 PM

# Notification Settings
NOTIFICATION_POLL_INTERVAL = int(os.environ.get('NOTIFICATION_POLL_INTERVAL', 30))  # seconds
```

---

## Automated Cron Jobs

### 1. Auto-Lock Yesterday Schedules
**Schedule:** يومياً الساعة 23:59  
**Function:** `auto_lock_yesterday_schedules()`  
**Purpose:** إقفال جميع الجداول من الأمس تلقائياً

```python
# في app.py
backup_scheduler.add_job(
    auto_lock_yesterday_schedules,
    trigger=CronTrigger(hour=23, minute=59),
    id='auto_lock_schedules',
    name='Auto Lock Yesterday Schedules'
)
```

---

### 2. Cleanup Old Notifications
**Schedule:** أسبوعياً، الإثنين الساعة 2:00 صباحاً  
**Function:** `cleanup_old_notifications(days=30)`  
**Purpose:** حذف الإشعارات المقروءة الأقدم من 30 يوم

```python
# في app.py
backup_scheduler.add_job(
    cleanup_old_notifications,
    trigger=CronTrigger(day_of_week='mon', hour=2, minute=0),
    id='cleanup_notifications',
    name='Cleanup Old Notifications'
)
```

---

## Security Features

### 1. Role-Based Access Control (RBAC)

**Decorators:**
```python
@handler_required      # HANDLER role only
@supervisor_required   # PROJECT_MANAGER or GENERAL_ADMIN
@admin_required        # GENERAL_ADMIN only
```

### 2. Data Isolation
- Handlers يرون جداولهم ومشاريعهم فقط
- Project Managers يرون مشاريعهم فقط
- General Admins يرون كل شيء

### 3. Audit Trail
جميع الجداول تحتوي على:
- `created_by_user_id`
- `reviewed_by_user_id`
- `created_at`, `updated_at`

---

## Grace Period System

### Concept
السماح للسائس بإرسال التقرير بعد انتهاء الوردية بفترة سماح محددة.

### Implementation
```python
# في HandlerReportService.can_submit_report()
grace_period = timedelta(minutes=Config.HANDLER_REPORT_GRACE_MINUTES)
shift_end = datetime.combine(schedule_item.schedule.date, shift.end_time)
deadline = shift_end + grace_period

if datetime.utcnow() > deadline:
    return False, "انتهت فترة السماح لإرسال التقرير"
```

### Configuration
```bash
# في .env
HANDLER_REPORT_GRACE_MINUTES=240  # 4 hours default
```

---

## Future Enhancements (Pending Tasks)

### Frontend Development (Tasks 11-13)
- [ ] Handler Dashboard HTML
- [ ] Report Forms (new, edit, view)
- [ ] Schedule Management UI
- [ ] User Management UI with Bulk Import interface
- [ ] Notification panel

### Mobile-First Design (Task 14)
- [ ] Convert tables to Cards for mobile
- [ ] Bottom Navigation Bar
- [ ] Touch-friendly interactions

### Dark Mode (Task 15)
- [ ] Dark theme implementation
- [ ] Theme toggle

### Real-time Notifications (Task 16)
- [ ] Long-polling implementation
- [ ] Or WebSocket for instant updates

### File Upload System (Task 17)
- [ ] Image/PDF upload
- [ ] SHA256 hashing
- [ ] Secure storage

### PDF Export (Task 18)
- [ ] Arabic RTL PDF reports
- [ ] ReportLab templates

### Testing (Task 19)
- [ ] Unit tests for services
- [ ] Integration tests for routes
- [ ] E2E tests

---

## File Structure

```
k9/
├── models/
│   ├── models.py                    # Extended User model
│   └── models_handler_daily.py      # All Handler Daily tables
├── services/
│   ├── handler_service.py           # DailySchedule, HandlerReport, Notification services
│   └── user_management_service.py   # User management & bulk import
├── routes/
│   ├── handler_routes.py            # Handler endpoints
│   ├── schedule_routes.py           # Supervisor schedule endpoints
│   └── user_management_routes.py    # Admin user management
├── utils/
│   └── schedule_utils.py            # Cron job utilities
└── decorators.py                    # @handler_required, @supervisor_required

config.py                            # Handler system configuration
app.py                               # Cron job registration
```

---

## API Response Formats

### Success Response
```json
{
  "success": true,
  "data": {...},
  "message": "نجح العملية"
}
```

### Error Response
```json
{
  "success": false,
  "error": "رسالة الخطأ",
  "code": "ERROR_CODE"
}
```

---

## Testing Checklist

### Backend Testing
- [x] Database models created successfully
- [x] Services layer tested
- [x] Routes registered
- [x] Cron jobs scheduled
- [x] Notifications working
- [x] User management working
- [x] Architect reviewed and approved

### Frontend Testing (Pending)
- [ ] Handler dashboard loads
- [ ] Report creation works
- [ ] Schedule management works
- [ ] Notifications display
- [ ] Bulk import works
- [ ] Mobile responsive

---

## Deployment Notes

### Environment Variables
```bash
DATABASE_URL=postgresql://...
SESSION_SECRET=...
HANDLER_REPORT_GRACE_MINUTES=240
SCHEDULE_AUTO_LOCK_HOUR=23
SCHEDULE_AUTO_LOCK_MINUTE=59
NOTIFICATION_POLL_INTERVAL=30
```

### Database Migration
```bash
flask db migrate -m "Add Handler Daily System"
flask db upgrade
```

### Production Checklist
- [ ] Environment variables set
- [ ] Database migrated
- [ ] Cron jobs verified
- [ ] File upload directory created
- [ ] Permissions tested
- [ ] Logs monitored

---

## Support & Maintenance

### Regular Tasks
- **Daily:** Monitor cron job logs
- **Weekly:** Check notification cleanup
- **Monthly:** Review grace period settings
- **Quarterly:** Audit user accounts

### Troubleshooting

#### Cron Jobs Not Running
```bash
# Check scheduler status in logs
grep "Auto-lock schedules job scheduled" logs/
grep "Notification cleanup job scheduled" logs/
```

#### Notifications Not Appearing
```python
# Check notification service
from k9.services.handler_service import NotificationService
count = NotificationService.get_unread_count(user_id)
```

#### Reports Not Submitting
- Check grace period configuration
- Verify schedule_item exists
- Check user permissions

---

**Last Updated:** October 26, 2025  
**Status:** ✅ Backend Complete & Architect Approved  
**Next Phase:** Frontend Development (Tasks 11-13)
