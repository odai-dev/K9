# K9 Operations Management System — Technical & Functional Documentation

> **Version**: Based on codebase snapshot (2025/2026)  
> **Language**: Bilingual system (Arabic primary, English labels in code)  
> **Stack**: Python 3, Flask, SQLAlchemy, PostgreSQL, Gunicorn, Nginx, Docker

---

## Table of Contents

1. [Business Domain & Concepts](#1-business-domain--concepts)
2. [Architecture Overview](#2-architecture-overview)
3. [Data Models](#3-data-models)
4. [Permission & RBAC System](#4-permission--rbac-system)
5. [User Roles & Workflows](#5-user-roles--workflows)
6. [Operational Workflows](#6-operational-workflows)
7. [Route & Blueprint Structure](#7-route--blueprint-structure)
8. [Security Architecture](#8-security-architecture)
9. [Reporting System](#9-reporting-system)
10. [Dashboard & Analytics](#10-dashboard--analytics)
11. [Operational Constraints & Business Rules](#11-operational-constraints--business-rules)
12. [Infrastructure & Deployment](#12-infrastructure--deployment)
13. [Integration Boundaries](#13-integration-boundaries)

---

## 1. Business Domain & Concepts

### 1.1 What is K9?

K9 is a **military/security K9 unit operations management platform** designed for organizations that deploy working dogs (police K9, military detection dogs, security dogs). The system manages the full lifecycle of a working dog — from breeding and puppy training through field deployment, veterinary care, performance evaluation, and eventual retirement.

The platform is **Arabic-first**, targeting organizations in Yemen or the wider MENA region. All UI flash messages and template labels are in Arabic. Enum descriptions and bilingual fields exist in some newer models.

### 1.2 Core Business Entities

| Entity | Description |
|--------|-------------|
| **Dog** | The primary operational asset. Has a unique code, breed, gender, birth date, current status, medical/training history, and assignments. |
| **Employee** | A staff member with a specific role (Handler, Trainer, Breeder, Vet, Project Manager). All system users must be linked to an Employee record. |
| **User** | Auth account for a staff member. Linked 1:1 with Employee. Has a [UserRole](file:///home/odai/Documents/K9/k9/models/models.py#10-17) and optional `project_id` / [dog_id](file:///home/odai/Documents/K9/k9/routes/pm_routes.py#132-142) for scoped access. |
| **Project** | An operational deployment unit (e.g., a field base or security contract). Dogs and employees are assigned to Projects. Each project has one designated Project Manager. |
| **Shift** | A named time slot (e.g., Morning: 06:00–14:00). Shifts define the handler's daily schedule. |
| **DailySchedule** | The schedule for a given project on a given date, containing schedule items. |
| **DailyScheduleItem** | One row in a daily schedule: a Handler is assigned to a Dog for a Shift at a Location. |

### 1.3 Operational Activities

| Activity | Model(s) |
|----------|----------|
| Field handler daily reporting | [HandlerReport](file:///home/odai/Documents/K9/k9/models/models_handler_daily.py#177-229) + sub-models (Health, Training, Care, Behavior, Incident) |
| Shift reporting (quick form) | [ShiftReport](file:///home/odai/Documents/K9/k9/models/models_handler_daily.py#387-434) + sub-models (Health, Behavior, Incident, Attachment) |
| Veterinary care | [VeterinaryVisit](file:///home/odai/Documents/K9/k9/models/models.py#466-530) |
| Dog training | [TrainingSession](file:///home/odai/Documents/K9/k9/models/models.py#441-465) |
| Breeding production | [ProductionCycle](file:///home/odai/Documents/K9/k9/models/models.py#531-564), [HeatCycle](file:///home/odai/Documents/K9/k9/models/models.py#836-858), [MatingRecord](file:///home/odai/Documents/K9/k9/models/models.py#859-886), [PregnancyRecord](file:///home/odai/Documents/K9/k9/models/models.py#887-924), [DeliveryRecord](file:///home/odai/Documents/K9/k9/models/models.py#925-959), [PuppyRecord](file:///home/odai/Documents/K9/k9/models/models.py#960-1011), [PuppyTraining](file:///home/odai/Documents/K9/k9/models/models.py#1012-1053) |
| Incident tracking | [Incident](file:///home/odai/Documents/K9/k9/models/models.py#689-724), [Suspicion](file:///home/odai/Documents/K9/k9/models/models.py#725-763) |
| Performance reviews | [PerformanceEvaluation](file:///home/odai/Documents/K9/k9/models/models.py#764-815) |
| Caretaker daily care | [CaretakerDailyLog](file:///home/odai/Documents/K9/k9/models/models.py#1601-1663) |
| Feeding records | [FeedingLog](file:///home/odai/Documents/K9/k9/models/models.py#1200-1243) |
| Breeding training | [BreedingTrainingActivity](file:///home/odai/Documents/K9/k9/models/models.py#1535-1598) |

### 1.4 Domain Lifecycle: Working Dog

```
[ Breeding ]  →  [ Puppy / Whelping ]  →  [ Puppy Training ]
      ↓
[ Dog Record Created ]  →  [ Assigned to Project ]  →  [ Assigned to Handler ]
      ↓
[ Daily Schedules ]  →  [ Handler Reports / Shift Reports ]
      ↓
[ Vet Visits ]  [ Training Sessions ]  [ Incidents ]  [ Evaluations ]
      ↓
[ Retired / Deceased / Transferred ]
```

---

## 2. Architecture Overview

### 2.1 Application Type

Single-server **Flask monolith** with a modular **Blueprint** structure. No microservices. All logic runs in one Python process (multiple workers via Gunicorn in production).

### 2.2 Technology Stack

| Layer | Technology |
|-------|------------|
| Web Framework | Flask 3.x |
| ORM | SQLAlchemy (via Flask-SQLAlchemy) |
| Database (prod) | PostgreSQL 15 |
| Database (dev) | SQLite (fallback) |
| Auth | Flask-Login |
| CSRF Protection | Flask-WTF / CSRFProtect |
| Migration | Flask-Migrate (Alembic) |
| App Server | Gunicorn |
| Reverse Proxy | Nginx |
| Containerization | Docker + Docker Compose |
| Caching (optional) | Redis |
| Session Storage | Server-side Flask sessions (Redis optional) |
| File Storage | Local filesystem (mounted Docker volume) |

### 2.3 Application Factory ([app.py](file:///home/odai/Documents/K9/app.py))

The [app.py](file:///home/odai/Documents/K9/app.py) file is the **application root** (not a factory pattern in the strict sense, but the entry point). It:

1. Configures the Flask app from [Config](file:///home/odai/Documents/K9/config.py#4-64) class in [config.py](file:///home/odai/Documents/K9/config.py)
2. Initializes extensions: `db`, `login_manager`, [csrf](file:///home/odai/Documents/K9/app.py#124-137), `migrate`
3. Creates the `uploads/` directory
4. Configures session cookies (SameSite=None for Replit compatibility)
5. Registers all Blueprints
6. Registers Jinja global helper functions ([has_permission](file:///home/odai/Documents/K9/app.py#344-374), [is_admin](file:///home/odai/Documents/K9/k9/services/permission_service.py#406-413), [get_notification_link](file:///home/odai/Documents/K9/k9/routes/handler_routes.py#1262-1276), etc.)
7. Registers [SecurityMiddleware](file:///home/odai/Documents/K9/k9/utils/security_middleware.py#7-343) (rate limiting, headers, stale session cleanup)
8. Handles CSRF errors per-endpoint (JSON responses for API paths)

### 2.4 Blueprint Map

| Blueprint | Prefix | Audience |
|-----------|--------|----------|
| `main_bp` | `/` | All authenticated users; admin dashboard |
| `auth_bp` | `/auth` | Login, logout, setup, mode-selection |
| `admin_bp` | `/admin` | General Admin administration |
| `pm_bp` | `/pm` | Project Managers |
| `handler_bp` | `/handler` | Handlers (dog handlers) |
| `supervisor_bp` | `/supervisor` | Supervisors / PMs managing schedules |
| `reports_bp` | `/reports` | Unified report generation |
| `api_bp` | `/api` | REST JSON API endpoints |

---

## 3. Data Models

### 3.1 User & Employee

```
Employee (staff record)
├── id (UUID PK)
├── name, employee_id (unique HR code), role (EmployeeRole enum)
├── phone (unique, Yemen format validated), email
├── hire_date, birth_date, national_id
├── is_active (boolean)
└── → User (1:1 via employee_id FK)

User (auth account)
├── id (UUID PK)
├── username (unique), email (unique)
├── password_hash (Werkzeug), role (UserRole enum)
├── full_name, phone
├── employee_id (FK → Employee, required)
├── project_id (FK → Project, for scoped access)
├── dog_id (FK → Dog, handler's assigned dog)
├── active (boolean), is_active property
├── MFA: mfa_enabled, mfa_secret, backup_codes (JSON)
├── Account lock: failed_login_attempts, locked_until
├── last_login timestamp
└── allowed_sections (JSON, legacy per-section permissions for PMs)
```

**Key constraint**: Every [User](file:///home/odai/Documents/K9/k9/models/models.py#225-287) must be linked to an active [Employee](file:///home/odai/Documents/K9/k9/models/models.py#335-420). Login is denied if this link is missing or the employee is inactive.

### 3.2 Dog

```
Dog
├── id (UUID PK), name, code (unique), breed, gender (DogGender enum)
├── birth_date, current_status (DogStatus: ACTIVE/TRAINING/RETIRED/DECEASED)
├── origin, location, weight_kg
├── assigned_to_user_id (FK → User, current handler)
├── project assignments (M2M via ProjectAssignment)
├── family: father_id, mother_id (self-referential FKs)
├── Documents: photo, national_id_photo, certificate_photo, health_card_photo
├── Metadata: notes, created_at, updated_at
└── Relationships: vet_visits, training_sessions, handler_reports, production_cycles
```

**Dog Status Flow**: `ACTIVE` ↔ `TRAINING` → `RETIRED` / `DECEASED`

### 3.3 Project

```
Project
├── id (UUID PK), name, code (unique), description
├── status (ProjectStatus: PLANNED/ACTIVE/COMPLETED/CANCELLED)
├── start_date, end_date, location, budget, currency
├── manager_id (FK → User), project_manager_id (FK → Employee)
├── success_rating (1-5)
├── is_active (boolean)
└── Assignments: employees (M2M via ProjectAssignment), dogs (M2M via ProjectAssignment)
```

**Project Assignment model** ([ProjectAssignment](file:///home/odai/Documents/K9/k9/models/models.py#653-688)) tracks both dog and employee assignments with [is_active](file:///home/odai/Documents/K9/k9/models/models.py#240-243), `assigned_at`, `removed_at`. This replaced the legacy `project_dog_assignment` and `employee_dog_assignment` tables.

### 3.4 Handler Daily Operations Models

```
DailySchedule
├── id (UUID PK), date, project_id (FK)
├── status (ScheduleStatus: OPEN/LOCKED)
├── created_by_user_id, notes
└── → items: List[DailyScheduleItem]

DailyScheduleItem
├── id (UUID PK), daily_schedule_id (FK)
├── handler_user_id (FK → User), dog_id (FK → Dog), shift_id (FK → Shift)
├── location_id (FK → ProjectLocation), status (ScheduleItemStatus: PRESENT/ABSENT/REPLACED)
├── replacement_handler_id (FK → User, if replaced)
├── replacement_reason (text)
└── → shift_report (1:1 ShiftReport)

HandlerReport (comprehensive daily dog report)
├── id, handler_user_id, dog_id, project_id, schedule_item_id
├── date, location, status (ReportStatus: DRAFT/SUBMITTED/APPROVED/REJECTED/...)
├── submitted_at, review_notes, reviewed_by_user_id, reviewed_at
└── Sub-models:
    ├── HandlerReportHealth (11 body part statuses: eyes, nose, ears, mouth, teeth, gums, front_limbs, back_limbs, hair, tail, rear)
    ├── HandlerReportTraining[] (type, description, time_from/to, notes)
    ├── HandlerReportCare (food_amount/type, supplements, water, grooming, washing, stool color/shape, excretion)
    ├── HandlerReportBehavior (good_behavior_notes, bad_behavior_notes)
    ├── HandlerReportIncident[] (type: SUSPICION/DETECTION, description)
    └── HandlerReportAttachment[] (file path, description)

ShiftReport (quick per-shift report)
├── id, schedule_item_id (FK), handler_user_id, dog_id, shift_id
├── start_time, end_time, location
├── status (same ReportStatus enum), submitted_at
└── Sub-models:
    ├── ShiftReportHealth
    ├── ShiftReportBehavior
    ├── ShiftReportIncident[] + ShiftReportAttachment[]
```

### 3.5 Veterinary Model

```
VeterinaryVisit
├── id, dog_id, vet_id (FK → Employee), project_id
├── visit_type (VisitType enum), visit_date, diagnosis, treatment
├── status (string: DRAFT/PENDING_PM_REVIEW/PM_APPROVED/PM_REJECTED/APPROVED)
├── Physical exam: weight_kg, temperature, pulse, respiratory_rate
├── Health score (1-10)
├── JSON fields: vaccinations (array), medications (array)
├── cost, follow_up_date
├── Workflow: pm_review_notes, reviewed_at, reviewed_by_user_id
└── submitted_at
```

### 3.6 Production System (Breeding)

```
HeatCycle → MatingRecord → PregnancyRecord → DeliveryRecord → PuppyRecord → PuppyTraining
```

Each model links to [Dog](file:///home/odai/Documents/K9/k9/models/models.py#288-334) (female/male), [Employee](file:///home/odai/Documents/K9/k9/models/models.py#335-420) (vet/breeder), and contains detailed biological tracking data (cycle dates, mating attempts, pregnancy weeks, delivery stats, puppy vitals, early training records).

### 3.7 Audit & Access Logging

```
AuditLog (general user action log)
├── user_id, action (AuditAction enum), target_type, target_id
├── description, old_values (JSON), new_values (JSON)
└── ip_address, session_id, created_at

AccessAuditLog (access pattern tracking)
├── user_id, resource_type, resource_id
├── action, outcome (AccessOutcome: SUCCESS/FAILURE/BLOCKED)
├── page_name, project_id, project_name
└── ip_address, user_agent, session_id, created_at

PermissionAuditLog (permission change tracking)
├── changed_by_user_id, target_user_id
├── action (GRANT/REVOKE), permission_key, role_type
└── notes, created_at
```

### 3.8 Supporting Models

| Model | Purpose |
|-------|---------|
| [Shift](file:///home/odai/Documents/K9/k9/models/models.py#1164-1177) | Named time slots with `start_time`, `end_time` |
| [ProjectLocation](file:///home/odai/Documents/K9/k9/models/models.py#614-631) | Named locations within a project |
| [Notification](file:///home/odai/Documents/K9/k9/models/models_handler_daily.py#538-576) | In-app user notifications with type, title, message, read status |
| [Task](file:///home/odai/Documents/K9/k9/models/models_handler_daily.py#598-638) | Assigned tasks with priority, due date, status |
| [Incident](file:///home/odai/Documents/K9/k9/models/models.py#689-724) | Project-level security incidents (type, severity, gps, resolved flag) |
| [Suspicion](file:///home/odai/Documents/K9/k9/models/models.py#725-763) | Suspicious activity reports with evidence collection tracking |
| [PerformanceEvaluation](file:///home/odai/Documents/K9/k9/models/models.py#764-815) | Scored employee evaluations |
| [CaretakerDailyLog](file:///home/odai/Documents/K9/k9/models/models.py#1601-1663) | Daily care log for breeders/caretakers |
| [FeedingLog](file:///home/odai/Documents/K9/k9/models/models.py#1200-1243) | Per-dog feeding records |
| [BreedingTrainingActivity](file:///home/odai/Documents/K9/k9/models/models.py#1535-1598) | Specialized training for breeding program dogs |

---

## 4. Permission & RBAC System

### 4.1 Two-Layer System

The application has a **V2 permission system** ([permissions_v2.py](file:///home/odai/Documents/K9/k9/models/permissions_v2.py) + [permission_service.py](file:///home/odai/Documents/K9/k9/services/permission_service.py)) that coexists with a legacy simpler system ([permissions_new.py](file:///home/odai/Documents/K9/k9/utils/permissions_new.py)). The V2 system adds fine-grained control and audit trails.

### 4.2 User Roles (UserRole enum)

| Role | Code | Description |
|------|------|-------------|
| General Admin | `GENERAL_ADMIN` | System-wide superuser. Can switch to PM mode. |
| Project Manager | `PROJECT_MANAGER` | Manages one assigned project. Sees only their project's data. |
| Handler | `HANDLER` | Field dog handler. Restricted to their own reports and schedules. |
| Supervisor | `SUPERVISOR` | Manages schedules; overlaps with PM role in some routes. |
| Vet | `VET` | Veterinary staff. |
| Trainer | `TRAINER` | Dog trainers. |
| Breeder | `BREEDER` | Breeding program staff. |
| Caretaker | `CARETAKER` | Daily dog care staff. |

### 4.3 V2 Role Types (RoleType)

```
SUPER_ADMIN          → all permissions
PROJECT_MANAGER      → project-scoped permissions
HANDLER              → handler daily operations
SUPERVISOR           → schedule management
VET                  → veterinary permissions
TRAINER              → training permissions
BREEDER              → breeding permissions
CARETAKER            → caretaker permissions
READ_ONLY            → view-only access
AUDITOR              → audit log access
```

### 4.4 Permission Keys (PermissionKey)

Permissions are hierarchical strings in the format `domain.action`:

| Domain | Example Keys |
|--------|-------------|
| dogs | `dogs.view`, `dogs.create`, `dogs.edit`, `dogs.delete` |
| employees | `employees.view`, `employees.create`, `employees.edit` |
| projects | `projects.view`, `projects.create`, `projects.manage` |
| training | `training.view`, `training.create`, `training.edit` |
| veterinary | `veterinary.view`, `veterinary.create`, `veterinary.edit` |
| breeding | `breeding.view`, `breeding.create`, `breeding.manage` |
| handler_daily | `handler_daily.reports.view`, `handler_daily.reports.create`, `handler_daily.reports.edit` |
| supervisor | `supervisor.schedules.view`, `supervisor.schedules.create`, `supervisor.schedules.lock`, `supervisor.schedules.delete` |
| reports | `reports.view`, `reports.create`, `reports.export` |
| pm | `pm.dashboard`, `pm.project.view`, `pm.team.view`, `pm.approvals.view`, `pm.reports.approve` |
| admin | `admin.users`, `admin.system`, `admin.audit` |
| notifications | `notifications.view`, `notifications.manage` |

### 4.5 Permission Resolution (PermissionService)

```python
has_permission(user, key) → bool:
    1. Check cache (in-memory, 5-min TTL per user)
    2. If SUPER_ADMIN role → True
    3. Check PermissionOverride for explicit GRANT/REVOKE
    4. Get user's active UserRoleAssignments
    5. For each role: check ROLE_PERMISSIONS mapping
    6. If project_required: verify user is in the right project scope
    7. Return True if any role grants the permission
```

**Caching**: Permission results are cached per-user-session with a 5-minute TTL to avoid repeated database queries.

### 4.6 UserRoleAssignment

```
UserRoleAssignment
├── user_id (FK), role_id (FK → Role)
├── project_id (FK, optional — project-scoped assignment)
├── granted_by_user_id (FK)
├── expires_at (optional expiration)
└── is_active
```

### 4.7 PermissionOverride

Allows per-user, per-permission exceptions overriding the role defaults:
- `override_type`: `GRANT` or `REVOKE`
- `permission_key`: specific permission to override
- `reason`: required justification text
- `expires_at`: optional expiration
- All changes are recorded in [PermissionAuditLog](file:///home/odai/Documents/K9/k9/models/permissions_v2.py#377-413)

### 4.8 Route Protection Decorators

```python
@login_required                  # Flask-Login: authenticated session
@require_permission('key')       # V2 permission check
@handler_required                # Role check: HANDLER only
@admin_or_pm_required            # Role check: GENERAL_ADMIN or PROJECT_MANAGER
@require_pm_project              # PM has project assigned + access logging
```

---

## 5. User Roles & Workflows

### 5.1 General Admin (GENERAL_ADMIN)

**Access**: System-wide. All projects, all data.

**Dual Mode Feature**: After login, a General Admin with an Employee record is presented a **mode selection screen**:
- **General Admin Mode** (`session['admin_mode'] = 'general_admin'`): Full system administration dashboard, all projects visible.
- **Project Manager Mode** (`session['admin_mode'] = 'project_manager'`): Assumes the PM role for their assigned project, sees a PM dashboard scoped to that project.

The admin can switch modes at any time via `POST /auth/switch-mode` without re-logging in.

**Key Workflows**:
1. **System Setup** (`GET/POST /auth/setup`): First-run wizard if no admin exists. Creates the first admin Employee + User pair.
2. **User Management**: Create/edit/deactivate users, create Project Manager accounts (`/auth/create_manager`).
3. **Project Management**: Create, assign dogs and employees to projects.
4. **System Administration**: Manage roles, permissions, view audit logs.
5. **Cross-project Reporting**: View reports from all projects.

### 5.2 Project Manager (PROJECT_MANAGER)

**Access**: Scoped to their single assigned project.

**Dashboard** (`/pm/dashboard`): Shows:
- Active dog/employee assignment counts
- Incident and suspicion totals
- Evaluation, training, and veterinary session counts
- Pending approval counts (reports, vet visits, breeding activities, caretaker logs)
- Recent activity lists (incidents, suspicions, evaluations, training, vet visits)
- Pending handler reports for quick approval

**Key Workflows**:
1. **Pending Approvals** (`/pm/pending-approvals`): Lists all items needing PM review across report types.
2. **Approve/Reject Handler Reports**: Via `/supervisor/reports/<id>/approve|reject`.
3. **Approve/Reject Vet Visits**: Via `/pm/approve-vet-visit/<id>` and `/pm/reject-vet-visit/<id>`.
4. **Approve/Reject Breeding Activities**: Via `/pm/approve-breeding/<id>`.
5. **Approve/Reject Caretaker Logs**: Via `/pm/approve-caretaker/<id>`.
6. **View Team**: View handlers and their user account status (`/pm/my-team`).
7. **View Dogs**: View per-dog training and vet history (`/pm/my-dogs`).
8. **Schedule Management** (via Supervisor routes): Create and manage daily schedules.

**Project Scoping**: The [get_active_project()](file:///home/odai/Documents/K9/k9/routes/pm_routes.py#46-81) function ensures PMs only see their assigned project. A General Admin in general_admin mode can supply a `project_id` query parameter to view any project.

### 5.3 Handler (HANDLER)

**Access**: Scoped to their own reports and assigned dog. Cannot access other handlers' data.

**Key Constraint — Shift Report Enforcement**: A [before_request](file:///home/odai/Documents/K9/k9/utils/security_middleware.py#24-46) hook on the `handler_bp` checks for pending shift reports (shifts that ended without a submitted report). If any exist, the handler is **blocked** from all routes except:
- Creating/viewing shift reports
- Viewing the "pending reports required" page
- Logout, login, static files

**Dashboard** (`/handler/dashboard`): Shows:
- Assigned project and dog
- Today's (or tomorrow's if today has no schedule) schedule items with shift report status
- List of dogs worked today and their daily report status
- Unread notifications (capped at 5)
- Recent 5 reports
- Monthly stats (total, approved, pending, this-month reports)
- Count of pending shift reports

**Key Workflows**:
1. **New Daily Report** (`/handler/report/new`): Create a comprehensive daily dog report. Form includes health (11 body parts), training sessions (6 types), care (feeding, grooming, stool), behavior (good/bad notes), and incidents (suspicion/detection).
2. **Pre-population**: When a dog_id is provided, the form pre-fills from that dog's shift reports for the same date.
3. **New Shift Report** (`/handler/shift-report/new`): Quick shift-end report. Also parses health, behavior, incidents with file attachments.
4. **Edit Report**: Only DRAFT status reports can be edited. Ownership check enforced.
5. **Submit Report**: Changes status from DRAFT → SUBMITTED, triggering PM notification.
6. **View Notifications**: In-app notification inbox.

### 5.4 Supervisor / Schedule Manager

**Access**: Admin or PM required (via `@admin_or_pm_required`).

**Key Workflows**:
1. **Schedule Index** (`/supervisor/schedules`): List all daily schedules with filters (date range, project, status).
2. **Create Schedule** (`/supervisor/schedules/create`): Create a daily schedule for a project date. Add schedule items (handler + dog + shift + location). Handlers and dogs are loaded dynamically via API (`/supervisor/api/handlers-by-project/<id>`, `/supervisor/api/dogs-by-project/<id>`).
3. **Lock / Unlock Schedule**: A locked schedule cannot be deleted or modified. Auto-lock is scheduled at 23:59 (configurable via `SCHEDULE_AUTO_LOCK_HOUR/MINUTE` env vars).
4. **Delete Schedule**: Only unlocked schedules with no associated reports.
5. **Replace Handler**: Update a schedule item to use a replacement handler, with a reason.
6. **Report Review** (`/supervisor/reports`): View and approve/reject handler daily reports. Sends in-app notifications to handlers.

---

## 6. Operational Workflows

### 6.1 Handler Daily Report Lifecycle

```
Handler creates report (DRAFT)
       ↓
Handler submits report (SUBMITTED)
       ↓
PM reviews report
  ├── Approve → APPROVED (notification sent to handler)
  ├── Reject (reason required) → REJECTED (notification sent)
  └── Request Edits → back to DRAFT (handler revises)
       ↓
[Optional] PM forwards to General Admin (FORWARDED_TO_ADMIN)
       ↓
Admin final approval (APPROVED_BY_ADMIN) or rejection (REJECTED_BY_ADMIN)
```

The [ReportStatus](file:///home/odai/Documents/K9/k9/models/models_handler_daily.py#28-39) enum has these exact states: `DRAFT`, `SUBMITTED`, `APPROVED`, `APPROVED_BY_PM`, `FORWARDED_TO_ADMIN`, `APPROVED_BY_ADMIN`, `REJECTED`, `REJECTED_BY_PM`, `REJECTED_BY_ADMIN`.

### 6.2 Shift Report Workflow

```
Shift ends (time check via DailyScheduleItem.shift.end_time)
       ↓
Handler is "blocked" from non-shift routes
       ↓
Handler fills ShiftReport (health + behavior + incidents + attachments)
       ↓
Handler submits → SUBMITTED
       ↓
Block is lifted → handler can access rest of system
       ↓
That shift's data is available for pre-filling the HandlerReport the same day
```

### 6.3 Unified Report System

The [ReportContext](file:///home/odai/Documents/K9/k9/models/report_models.py#173-319) model and `UnifiedReportService` implement a **Generate Once → Preview → Export** pattern:

1. A [ReportContext](file:///home/odai/Documents/K9/k9/models/report_models.py#173-319) is created linking to a source report (e.g., a [HandlerReport](file:///home/odai/Documents/K9/k9/models/models_handler_daily.py#177-229)).
2. The service generates and **caches** the report data as JSON in `cached_data`.
3. Subsequent preview requests return the cached version (no re-querying).
4. Cache is invalidated when source data changes (`cache_valid = False`).
5. Exports (PDF/Excel/CSV/JSON) are tracked in [ReportExportHistory](file:///home/odai/Documents/K9/k9/models/report_models.py#325-385).
6. Status follows [UnifiedReportStatus](file:///home/odai/Documents/K9/k9/models/report_models.py#41-55): `DRAFT` → `SUBMITTED` → `PM_REVIEWED` → `PM_APPROVED/PM_REJECTED` → `FORWARDED_TO_ADMIN` → `APPROVED/REJECTED/ARCHIVED`.
7. Every status transition is recorded in [ReportApprovalHistory](file:///home/odai/Documents/K9/k9/models/report_models.py#391-445).

### 6.4 Veterinary Visit Workflow

```
Vet creates visit record (DRAFT)
       ↓
Vet submits → PENDING_PM_REVIEW
       ↓
PM reviews
  ├── Approve → PM_APPROVED
  └── Reject → PM_REJECTED (with review_notes)
       ↓
[If escalated] → APPROVED (general admin final)
```

### 6.5 Schedule Management Flow

```
Supervisor creates DailySchedule for [project, date]
       ↓
Add DailyScheduleItems (handler + dog + shift + location)
       ↓
Schedule is OPEN (editable)
       ↓
If handler absent → update item status to ABSENT or REPLACED
  └── Replace with another handler (replacement_handler_id set)
       ↓
Schedule auto-locks at 23:59 → LOCKED
  └── Handlers can still submit shift reports after lock
```

### 6.6 Breeding Production Workflow

```
HeatCycle (female dog goes into heat)
       ↓
MatingRecord (mating attempt with male dog, success/failure)
       ↓
PregnancyRecord (confirmed pregnancy, expected delivery date)
       ↓
DeliveryRecord (birth event: puppies born, survived count)
       ↓
PuppyRecord × N (individual puppy tracking)
       ↓
PuppyTraining × N (early developmental training for each puppy)
```

---

## 7. Route & Blueprint Structure

### 7.1 Main Routes (`main_bp` — `/`)

The largest route file. Contains:
- `/` landing (index)
- `/dashboard` admin dashboard
- Dog management CRUD
- Employee management CRUD
- Project management CRUD
- Training session management
- Veterinary visit management
- Production/breeding management
- Incident and suspicion management
- Performance evaluations
- Reports (historical views)
- Administration (user management, audit logs)

### 7.2 Auth Routes (`auth_bp` — `/auth`)

| Route | Method | Description |
|-------|--------|-------------|
| `/auth/login` | GET/POST | Login form. MFA check, account lock check, mode selection redirect |
| `/auth/logout` | GET | Logout, session cleanup |
| `/auth/setup` | GET/POST | First-run system setup (no admin exists gate) |
| `/auth/select-mode` | GET/POST | Mode selection for GENERAL_ADMIN |
| `/auth/switch-mode` | POST | Toggle between general_admin and project_manager modes |
| `/auth/create_manager` | GET/POST | Create PROJECT_MANAGER account (admin only) |

### 7.3 Handler Routes (`handler_bp` — `/handler`)

| Route | Description |
|-------|-------------|
| `/handler/dashboard` | Handler home with schedule, reports, notifications |
| `/handler/daily-reports/select` | Choose a dog for a new daily report |
| `/handler/report/new` | Create new daily report (GET: form, POST: save/submit) |
| `/handler/report/<id>/edit` | Edit DRAFT report |
| `/handler/report/<id>` | View report detail |
| `/handler/shift-report/<id>` | View shift report |
| `/handler/shift-report/new` | Create shift report |
| `/handler/my-shift-reports` | List handler's shift reports |
| `/handler/notifications` | Notification inbox |
| `/handler/profile` | Profile view |
| `/handler/pending-reports-required` | Blocking page when shift reports pending |

### 7.4 PM Routes (`pm_bp` — `/pm`)

| Route | Description |
|-------|-------------|
| `/pm/dashboard` | PM summary dashboard with stats and pending approvals |
| `/pm/project` | View project details |
| `/pm/my-team` | View team members with handler account status |
| `/pm/my-dogs` | View project dogs with activity info |
| `/pm/pending-approvals` | All pending approval items across types |
| `/pm/approve-vet-visit/<id>` | Approve vet visit |
| `/pm/reject-vet-visit/<id>` | Reject vet visit |
| `/pm/approve-breeding/<id>` | Approve breeding activity |
| `/pm/reject-breeding/<id>` | Reject breeding activity |
| `/pm/approve-caretaker/<id>` | Approve caretaker log |
| `/pm/reject-caretaker/<id>` | Reject caretaker log |

### 7.5 Supervisor Routes (`supervisor_bp` — `/supervisor`)

| Route | Description |
|-------|-------------|
| `/supervisor/schedules` | List daily schedules with filters |
| `/supervisor/schedules/create` | Create new daily schedule |
| `/supervisor/schedules/<id>` | View schedule detail |
| `/supervisor/schedules/<id>/lock` | Lock schedule (POST) |
| `/supervisor/schedules/<id>/unlock` | Unlock schedule (POST) |
| `/supervisor/schedules/<id>/delete` | Delete unlocked schedule (POST) |
| `/supervisor/schedules/item/<id>/replace-handler` | Replace handler in schedule item |
| `/supervisor/api/handlers-by-project/<id>` | JSON: handlers in project |
| `/supervisor/api/dogs-by-project/<id>` | JSON: dogs in project |
| `/supervisor/api/locations-by-project/<id>` | JSON: locations in project |
| `/supervisor/reports` | List handler reports for review |
| `/supervisor/reports/<id>` | View report detail |
| `/supervisor/reports/<id>/approve` | Approve report (POST, JSON) |
| `/supervisor/reports/<id>/reject` | Reject report (POST, JSON, reason required) |
| `/supervisor/api/pm/reports/pending` | PM: get all pending reports (all types) |
| `/supervisor/api/pm/reports/<type>/<id>` | PM: get/approve/reject/request-edits on specific report |

---

## 8. Security Architecture

### 8.1 Authentication Flow

```
1. User submits username + password
2. Username lookup → User.query.filter_by(username=...)
3. AccountLockoutManager.is_account_locked() → check failed_login_attempts + locked_until
4. check_password_hash(user.password_hash, password)
5. If MFA enabled:
   a. First request: store pending_user_id in session → render MFA form
   b. Verify TOTP (pyotp) or backup code
   c. Backup code used → removed from backup_codes list
6. Employee link validation (required for all users)
7. login_user(user, remember=remember)
8. Clear stale session data
9. load_user_permissions() → populate session permissions cache
10. For GENERAL_ADMIN with Employee: redirect to mode selection
11. For others: redirect to next_page or dashboard
```

### 8.2 Multi-Factor Authentication (MFA)

- **TOTP**: Time-based one-time passwords (via `pyotp`)
- **Backup Codes**: One-time use codes stored as JSON array in `user.backup_codes`
- **Fields**: `user.mfa_enabled`, `user.mfa_secret`
- **Verification**: `MFAManager.verify_totp()`, `MFAManager.verify_backup_code()`
- Failed MFA increments failed login counter (same lockout logic as password failures)

### 8.3 Account Lockout

- `AccountLockoutManager` class tracks `failed_login_attempts` on the [User](file:///home/odai/Documents/K9/k9/models/models.py#225-287) model
- Account is locked for a configurable duration (`locked_until`) after N failures
- `SecurityHelper.log_security_event()` records all security events with IP and user agent

### 8.4 Security Middleware ([SecurityMiddleware](file:///home/odai/Documents/K9/k9/utils/security_middleware.py#7-343))

Applied to every request via `app.before_request` / `app.after_request`:

**Before Request**:
- **Rate Limiting**: 1,500 requests per 5 minutes per IP (configurable via `RATE_LIMIT_REQUESTS` env var). In-memory storage (Redis-ready). Responds with HTTP 429.
- **IP Blocking**: Checks `BLOCKED_IPS` environment variable. Returns HTTP 403.
- **Request Size**: Rejects requests over 16MB with HTTP 413.
- **Stale Session Cleanup**: On every request, removes admin session flags ([admin_mode](file:///home/odai/Documents/K9/k9/utils/security_middleware.py#75-123), `pending_mode_selection`) for users that don't have GENERAL_ADMIN role.

**After Request** (security headers added):
```
Content-Security-Policy: ...
X-XSS-Protection: 1; mode=block
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), ...
Strict-Transport-Security: (HTTPS only)
Cache-Control: no-cache, no-store (for sensitive pages: /admin, /auth, /login, /employees, /users)
```

**CSP Configuration**: Allows CDN resources (Bootstrap, FontAwesome, jQuery from jsDelivr/cdnjs/stackpath), data: URIs for QR codes, and `frame-ancestors` for Replit iframe embedding. Script-src and style-src include `'unsafe-inline'`.

### 8.5 CSRF Protection

- **Flask-WTF CSRFProtect** applied globally
- CSRF time limit: 3600 seconds (1 hour, via `WTF_CSRF_TIME_LIMIT`)
- Login endpoint is `@csrf.exempt` (standard practice)
- JSON API endpoints that need CSRF exemption use `@csrf.exempt` per-route
- CSRF errors return JSON for API paths (`/admin/permissions/` prefix, `request.is_json`, `accept_mimetypes.accept_json`)

### 8.6 Password Security

- **Hashing**: Werkzeug `generate_password_hash` / `check_password_hash`
- **Validation** (`PasswordValidator`): Enforces complexity rules (minimum length, uppercase, lowercase, digits, special characters)

### 8.7 URL/Redirect Safety

```python
def is_safe_url(target):
    """Validates redirect target stays on same domain (prevents open redirect)"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
```

Used for `?next=` redirect parameter in login.

### 8.8 File Upload Security

- Max file size: **16MB** (enforced by Flask's `MAX_CONTENT_LENGTH` and [SecurityMiddleware](file:///home/odai/Documents/K9/k9/utils/security_middleware.py#7-343))
- Files stored in `uploads/` directory with separate sub-paths per module
- `AttachmentService.save_attachment()` and `save_report_attachment()` wrap file saving with error handling

---

## 9. Reporting System

### 9.1 Report Types

The [UnifiedReportType](file:///home/odai/Documents/K9/k9/models/report_models.py#20-39) enum covers all report categories:

| Code | Arabic Name | Description |
|------|------------|-------------|
| `HANDLER` | تقرير السائس اليومي | Daily handler-dog comprehensive report |
| `SHIFT` | تقرير الوردية | Quick per-shift report |
| `TRAINER` | تقرير المدرب | Training session report |
| `VET` | تقرير الطبيب البيطري | Veterinary visit report |
| `CARETAKER` | تقرير المربي اليومي | Caretaker daily care log |
| `ATTENDANCE` | تقرير الحضور | Attendance summary |
| `INCIDENT` | تقرير الحوادث | Incident report |
| `FEEDING` | تقرير التغذية | Feeding records |
| `CHECKUP` | تقرير الفحص الصحي | Health checkup |
| `GROOMING` | تقرير العناية | Grooming records |
| `DEWORMING` | تقرير مكافحة الديدان | Deworming log |
| `PRODUCTION` | تقرير الإنتاج | Breeding production |
| `EVALUATION` | تقرير التقييم | Performance evaluation |
| `CUSTOM` | تقرير مخصص | Custom report |

### 9.2 Report Export Formats

[ExportFormat](file:///home/odai/Documents/K9/k9/models/report_models.py#57-66): `PDF`, `EXCEL`, `CSV`, `JSON`

All exports are tracked in [ReportExportHistory](file:///home/odai/Documents/K9/k9/models/report_models.py#325-385) (who, when, what format, file path, file size, success/error).

### 9.3 Report Priority

[ReportPriority](file:///home/odai/Documents/K9/k9/models/report_models.py#68-77): `LOW`, `NORMAL`, `HIGH`, `URGENT`

### 9.4 Report Definition Registry

[ReportDefinition](file:///home/odai/Documents/K9/k9/models/report_models.py#83-167) acts as a **catalog** of report types. Each definition specifies:
- `required_permissions`: JSON array of permission keys needed to view/create
- `data_fields`: JSON schema for the report's required/optional fields
- `requires_project`, `requires_dog`, `requires_employee`, `supports_attachments`
- `requires_pm_approval`, `requires_admin_approval`: workflow flags
- `icon` (FontAwesome class), `color` (Bootstrap class), `sort_order`, [is_active](file:///home/odai/Documents/K9/k9/models/models.py#240-243)

### 9.5 Approval Workflow Integration

Every [ReportContext](file:///home/odai/Documents/K9/k9/models/report_models.py#173-319) has full workflow tracking:
- PM review fields: `pm_reviewed_by_user_id`, `pm_reviewed_at`, `pm_review_notes`, `pm_review_status`
- Admin review fields: `admin_reviewed_by_user_id`, `admin_reviewed_at`, `admin_review_notes`, `admin_review_status`
- [ReportApprovalHistory](file:///home/odai/Documents/K9/k9/models/report_models.py#391-445) records every status transition with actor, timestamp, notes, and rejection reason

---

## 10. Dashboard & Analytics

### 10.1 DashboardService

Provides aggregated statistics and chart-ready data for both PM and Admin dashboards.

**Admin Dashboard Data** ([get_admin_dashboard_data()](file:///home/odai/Documents/K9/k9/services/dashboard_service.py#399-412)):
- Dogs by project (bar chart)
- Dogs by status (pie chart)
- Employee distribution by role (pie chart)
- Project status overview (pie chart)
- System-wide report status distribution
- System-wide 30-day attendance trends (present/absent/replaced line chart)
- System-wide training stats (sessions, unique dogs)
- System-wide vet visit stats

**PM Dashboard Data** ([get_pm_dashboard_data(project_id)](file:///home/odai/Documents/K9/k9/services/dashboard_service.py#387-398)):
- Handler report status distribution for project
- 30-day attendance trends for project
- Top 10 handlers by dogs worked
- 6-month report submission trend
- Project training stats
- Project vet visit stats

### 10.2 Chart Data Formats

All chart methods return:
- **Pie/bar charts**: `{'labels': [...], 'data': [...], 'total': N}`
- **Line charts (multi-dataset)**: `{'labels': [...], 'datasets': [{label, data, borderColor, backgroundColor}, ...]}`

Arabic month names are used for date labels.

---

## 11. Operational Constraints & Business Rules

### 11.1 Phone Number Validation

- All employee/admin phone numbers are validated as Yemen phone numbers (`validate_yemen_phone()`)
- Format: Yemeni mobile numbers (+967 prefix pattern)

### 11.2 UUID Primary Keys

- All models use UUID as primary key (via `get_uuid_column()` model utility)
- `Config.is_sqlite()` detects database type for UUID compatibility handling
- UUID generation: `default_uuid` callable

### 11.3 Shift Report Enforcement Rule

- **Mandatory**: Handlers cannot access any part of the handler interface (except shift report creation and logout) while they have pending shift reports.
- **Pending definition**: A [DailyScheduleItem](file:///home/odai/Documents/K9/k9/models/models_handler_daily.py#132-171) where the handler was marked PRESENT or REPLACED, the shift's `end_time` has passed (or the date is in the past), and no [ShiftReport](file:///home/odai/Documents/K9/k9/models/models_handler_daily.py#387-434) exists for that item.

### 11.4 Grace Period

- `HANDLER_REPORT_GRACE_MINUTES`: Default 240 minutes (4 hours). Controls when a completed shift is flagged as needing a report. (Note: this is configured but the core logic checks `end_time <= current_time` directly; the grace period may be used in service-layer logic).

### 11.5 Schedule Locking Rules

- Only unlocked schedules can be deleted.
- Schedules with associated reports cannot be deleted even if unlocked.
- Auto-lock occurs at `SCHEDULE_AUTO_LOCK_HOUR:SCHEDULE_AUTO_LOCK_MINUTE` (default 23:59).

### 11.6 Report Editing Rules

- Only `DRAFT` status reports can be edited.
- Handlers can only edit their own reports (ownership check: `report.handler_user_id == current_user.id`).
- Submission changes status from DRAFT → SUBMITTED and cannot be undone without PM action.

### 11.7 Project Scoping

- Project Managers can only see data belonging to their assigned project.
- Project scoping is enforced at service and route level via [require_pm_project](file:///home/odai/Documents/K9/k9/routes/pm_routes.py#82-131) decorator and [get_active_project()](file:///home/odai/Documents/K9/k9/routes/pm_routes.py#46-81) helper.
- Dog access in PM routes is checked via [ProjectAssignment](file:///home/odai/Documents/K9/k9/models/models.py#653-688) membership.

### 11.8 Employee Requirement

- Every [User](file:///home/odai/Documents/K9/k9/models/models.py#225-287) account must have a linked [Employee](file:///home/odai/Documents/K9/k9/models/models.py#335-420) record. Login is blocked if `user.employee_id` is missing or the linked employee is inactive.

### 11.9 Rejection Requires Reason

- Report rejection requires a non-empty `review_notes` / `reason`. Validated both at route level (API endpoints return 400) and by business rule.

### 11.10 Notification System

- Notifications are created for: report approved, report rejected, schedule assignment, system alerts.
- Notifications are **NOT** sent for new schedule creation (commented out: `DailyScheduleService.notify_handlers_of_new_schedule(...)` is disabled; schedules appear only in the handler dashboard).

### 11.11 Handler Dog Discovery

Dogs are discovered for a handler report in this priority:
1. Handler's directly assigned dog (`user.dog_id`)
2. Dogs assigned to handlers in the same project
3. Unassigned active dogs

### 11.12 Database Compatibility

- Production: PostgreSQL with `pool_recycle=300`, `pool_pre_ping=True`
- Development: SQLite with `check_same_thread=False`
- UUID columns: handled via `get_uuid_column()` which adapts to the database type

---

## 12. Infrastructure & Deployment

### 12.1 Production Docker Compose Services

| Service | Image | Purpose |
|---------|-------|---------|
| `db` | postgres:15-alpine | Primary database. Health-checked. Persistent volume `db_data`. Backup volume mounted. |
| `web` | Custom (Dockerfile.multistage) | Flask + Gunicorn app. Depends on `db` health. Volumes: uploads, logs. Memory: 512MB-1GB, CPU: 0.5-1.0. |
| `nginx` | nginx:1.25-alpine | Reverse proxy + SSL termination. Ports 80/443. Serves static and uploads directly. |
| `redis` | redis:7-alpine | Optional caching/session store. Requires password (`REDIS_PASSWORD`). Persistent with AOF. |
| [backup](file:///home/odai/Documents/K9/app.py#921-959) | postgres:15-alpine | Optional. Runs on `--profile backup`. Mounts `/backups` and `backup.sh` script. |

### 12.2 Network

Docker bridge network `k9-network` on subnet `172.20.0.0/16`. All services communicate on this internal network. Only Nginx exposes external ports.

### 12.3 Volumes

| Volume | Mounted In | Purpose |
|--------|-----------|---------|
| `db_data` | `db` | PostgreSQL data persistence |
| `uploads_data` | `web` + `nginx` | User-uploaded files |
| `logs_data` | `web` | Application logs |
| `static_data` | `nginx` | Static assets (served by Nginx directly) |
| `redis_data` | `redis` | Redis AOF persistence |

### 12.4 Gunicorn Configuration

Configured via environment variables:
- `GUNICORN_WORKERS`: Number of worker processes (default 4)
- `GUNICORN_MAX_REQUESTS`: Max requests per worker before restart (default 1000)
- `GUNICORN_MAX_REQUESTS_JITTER`: Jitter to avoid simultaneous restarts (default 100)

### 12.5 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SESSION_SECRET` | **Yes** | Flask secret key for session signing |
| `DATABASE_URL` | **Yes (prod)** | `postgresql://user:pass@host:port/db` |
| `FLASK_ENV` | Yes | `production` or `development` |
| `POSTGRES_*` | Yes (prod) | Individual DB connection params |
| `REDIS_PASSWORD` | No | Required if Redis service is used |
| `RATE_LIMIT_REQUESTS` | No | Default 1500 per 5 minutes |
| `BLOCKED_IPS` | No | Comma-separated IP list to block |
| `HANDLER_REPORT_GRACE_MINUTES` | No | Default 240 (4 hours) |
| `SCHEDULE_AUTO_LOCK_HOUR` | No | Default 23 (11 PM) |
| `SCHEDULE_AUTO_LOCK_MINUTE` | No | Default 59 |
| `NOTIFICATION_POLL_INTERVAL` | No | Default 30 seconds |

### 12.6 Logging

- Application logs use Python's `logging` module with configurable log level
- Security events logged at `WARNING`/`ERROR` levels
- Admin access logged at `INFO` level
- Suspicious request patterns (SQLi, XSS markers, path traversal) logged at `WARNING`
- Docker containers use `json-file` log driver with max 10MB × 3 files rotation

---

## 13. Integration Boundaries

### 13.1 Internal Boundaries

The system has a single database and a modular monolith with clear internal boundaries:

| Boundary | Direction | Description |
|----------|-----------|-------------|
| Routes ↔ Services | Routes call Services | Business logic encapsulated in service classes |
| Services ↔ Models | Services query/update Models | No direct DB access from routes |
| Jinja env ↔ Permission Service | Templates call [has_permission()](file:///home/odai/Documents/K9/app.py#344-374) | UI elements conditionally rendered |
| Session ↔ Permission Cache | Permissions cached in server memory | Cache keyed by user_id with TTL |

### 13.2 External Integrations

**Current (as of codebase)**:
- **None in production**. The system is fully self-contained.

**Infrastructure adjacent**:
- **PostgreSQL**: Only external data store
- **Redis**: Optional session/cache store (not yet wired in app code, present in Docker Compose only)
- **Nginx**: SSL termination, static file serving

**Designed for compatibility with**:
- **Replit**: Session cookies configured with `SameSite=None`, `Secure=False` when on Replit. CSP `frame-ancestors` allows Replit iframe embedding.

### 13.3 File System Integration

- Uploads stored at `UPLOAD_FOLDER = <project_root>/uploads/`
- Sub-paths used: `uploads/shift_reports/`, `uploads/handler_reports/`
- Files served via a route that maps `uploads/<path>` to the filesystem

### 13.4 MFA Integration

- TOTP via `pyotp` library (no external service)
- QR code generation for MFA setup (base64 data URI, no external image service)
- Backup codes generated and stored locally in `user.backup_codes` JSON field

### 13.5 Potential Future Integrations (inferred from model design)

- **Email notifications**: `email` field on Employee/User; no SMTP integration observed in reviewed code but infrastructure is present.
- **SMS notifications**: Phone numbers are collected and validated; no SMS gateway integrated.
- **Backup service**: `backup.sh` script + backup Docker service suggest external storage or scheduled backup destination.

---

## Appendix A: Enum Reference

### UserRole
`GENERAL_ADMIN`, `PROJECT_MANAGER`, `HANDLER`, `SUPERVISOR`, `VET`, `TRAINER`, `BREEDER`, `CARETAKER`

### EmployeeRole
`HANDLER`, `TRAINER`, `BREEDER`, `VET`, `PROJECT_MANAGER`

### DogStatus
`ACTIVE`, `TRAINING`, `RETIRED`, `DECEASED`

### DogGender
`MALE`, `FEMALE`

### ProjectStatus
`PLANNED`, `ACTIVE`, `COMPLETED`, `CANCELLED`

### ReportStatus (HandlerReport/ShiftReport)
`DRAFT`, `SUBMITTED`, `APPROVED`, `APPROVED_BY_PM`, `FORWARDED_TO_ADMIN`, `APPROVED_BY_ADMIN`, `REJECTED`, `REJECTED_BY_PM`, `REJECTED_BY_ADMIN`

### UnifiedReportStatus
`DRAFT`, `SUBMITTED`, `PM_REVIEWED`, `PM_APPROVED`, `PM_REJECTED`, `FORWARDED_TO_ADMIN`, `APPROVED`, `REJECTED`, `ARCHIVED`

### ScheduleStatus (DailySchedule)
`OPEN`, `LOCKED`

### ScheduleItemStatus
`PRESENT`, `ABSENT`, `REPLACED`

### TrainingType
`FITNESS`, `AGILITY`, `OBEDIENCE`, `BALL`, `EXPLOSIVES`, `OTHER`

### IncidentType
`SUSPICION`, `DETECTION`

### AuditAction
`LOGIN`, `LOGOUT`, `CREATE`, `UPDATE`, `DELETE`, `SETUP`, `MODE_SELECTION`, `SECURITY_EVENT`, and more.

### AccessOutcome
`SUCCESS`, `FAILURE`, `BLOCKED`

---

## Appendix B: Permission Key Quick Reference

```
admin.*              → Admin panel access
dogs.*               → Dog management
employees.*          → Employee management
projects.*           → Project management
training.*           → Training sessions
veterinary.*         → Vet visits
breeding.*           → Breeding management
handler_daily.*      → Handler daily/shift reports
supervisor.*         → Schedule management
pm.*                 → PM dashboard & approvals
reports.*            → Report generation and export
notifications.*      → Notification management
auth.*               → Auth management (create managers)
```

---

*End of K9 Technical Documentation*
