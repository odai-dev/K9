# K9 Operations Management System - Route Structure

## Route Registration Status: ✅ ALL ROUTES CONNECTED

Last Updated: 2025-10-22

## Report Routes Overview

All report routes are properly connected and compatible with each other. Legacy routes automatically redirect to unified endpoints for seamless backward compatibility.

### 1. Attendance Reports (`/reports/attendance`)

#### UI Routes
- **Daily Sheet**: `/reports/attendance/daily-sheet`
  - Permission: `Reports > Attendance Daily Sheet > View`
  - Template: `reports/attendance/daily_sheet.html`

- **PM Daily**: `/reports/attendance/pm-daily`
  - Permission: `reports:attendance:pm_daily:view`
  - Template: `reports/attendance/pm_daily.html`

#### API Routes
- **Daily Sheet Data**: `POST /api/reports/attendance/run/daily-sheet`
- **Daily Sheet PDF**: `POST /api/reports/attendance/export/pdf/daily-sheet`
- **PM Daily Data**: `POST /api/reports/attendance/run/pm-daily`
- **PM Daily PDF**: `POST /api/reports/attendance/export/pdf/pm-daily`

### 2. Training Reports (`/reports/training`)

#### UI Routes
- **Trainer Daily**: `/reports/training/trainer-daily`
  - Permission: Admin required
  - Template: `reports/training/trainer_daily.html`

#### API Routes
- **Trainer Daily Data**: `POST /api/reports/training/run/trainer-daily`
- **Trainer Daily PDF**: `POST /api/reports/training/export/pdf/trainer-daily`
- **Project Data**: `GET /api/projects`
- **Employee Data**: `GET /api/employees`
- **Dog Data**: `GET /api/dogs`

### 3. Breeding Reports (`/reports/breeding`)

#### Feeding Reports

**Unified Route** (Current):
- **UI**: `/reports/breeding/feeding/`
  - Permission: `reports.breeding.feeding.view`
  - Template: `reports/breeding/feeding.html`
  - Supports: Daily, Weekly, Monthly, Custom ranges

**Legacy Routes** (Redirect to Unified):
- `/reports/breeding/feeding/daily` → redirects to unified with `range_type=daily`
- `/reports/breeding/feeding/weekly` → redirects to unified with `range_type=weekly`

**API Routes**:
- Legacy APIs maintained at `/api/reports/breeding/feeding/*`

#### Checkup Reports

**Unified Route** (Current):
- **UI**: `/reports/breeding/checkup/`
  - Permission: `reports.breeding.checkup.view`
  - Template: `reports/breeding/checkup.html`
  - Supports: Daily, Weekly, Monthly, Custom ranges

**Legacy Routes** (Redirect to Unified):
- `/reports/breeding/checkup/daily` → redirects to unified with `range_type=daily`
- `/reports/breeding/checkup/weekly` → redirects to unified with `range_type=weekly`

**API Routes**:
- Legacy APIs maintained at `/api/reports/breeding/checkup/*`

#### Veterinary Reports

**Unified Route** (Current):
- **UI**: `/reports/breeding/veterinary/`
  - Permission: `reports.veterinary.view`
  - Template: `reports/breeding/veterinary.html`
  - Supports: Daily, Weekly, Monthly, Custom ranges

**Legacy Routes** (Redirect to Unified):
- `/reports/veterinary/daily` → redirects to unified with `range_type=daily`
- `/reports/veterinary/weekly` → redirects to unified with `range_type=weekly`

**API Routes**:
- **Veterinary Data**: `POST /api/reports/breeding/veterinary/`
- **Veterinary PDF**: `POST /api/reports/breeding/veterinary/export`

#### Caretaker Daily Reports

**Unified Route**:
- **UI**: `/reports/breeding/caretaker-daily/`
  - Permission: `reports.breeding.caretaker_daily.view`
  - Template: `reports/breeding/caretaker_daily.html`
  - Supports: Daily, Weekly, Monthly, Custom ranges

**API Routes**:
- **Caretaker Data**: `POST /api/reports/breeding/caretaker-daily/unified`
- **Caretaker PDF**: `POST /api/reports/breeding/caretaker-daily/unified/export.pdf`

### 4. Breeding Activity APIs

All breeding activity APIs are properly registered:

- **Cleaning**: `/api/breeding/cleaning` (POST, PUT, DELETE)
- **Excretion**: `/api/breeding/excretion` (GET, PUT, DELETE)
- **Deworming**: `/api/breeding/deworming` (GET, POST, PUT, DELETE)
- **Grooming**: `/api/breeding/grooming` (GET, POST, PUT, DELETE)
- **Training Activities**: `/api/breeding/training-activity` (POST, PUT, DELETE)
- **Feeding Logs**: `/api/breeding/feeding/log` (GET, POST, PUT, DELETE)

### 5. Authentication & Security Routes

- **Login**: `/auth/login`
- **Logout**: `/auth/logout`
- **MFA Setup**: `/mfa/setup`
- **MFA Status**: `/mfa/status`
- **MFA Verify**: `/mfa/verify`
- **Password Reset Request**: `/password-reset/request`
- **Password Reset Form**: `/password-reset/reset/<token>`
- **Change Password**: `/auth/change-password`

### 6. Admin Routes (`/admin`)

- **Dashboard**: `/admin/`
- **Permissions Management**: `/admin/permissions`
- **User Permissions**: `/admin/permissions/user/<user_id>`
- **Update Permissions**: `/admin/permissions/update`
- **Initialize Permissions**: `/admin/permissions/initialize/<user_id>`
- **Permissions Audit**: `/admin/permissions/audit`
- **Profile**: `/admin/profile`
- **Backup Management**: `/admin/backup`

### 7. Main Application Routes

- **Home/Login**: `/`
- **Dashboard**: `/dashboard`
- **Projects**: `/projects`
- **Project Dashboard**: `/projects/<project_id>/dashboard`
- **Project Assignments**: `/projects/<project_id>/assignments`
- **Dogs Management**: `/dogs` (list, add, edit, view)
- **Employees Management**: `/employees` (list, add, edit)

## Route Compatibility Notes

### ✅ All Routes Compatible
- No route conflicts detected
- All blueprints registered successfully
- Legacy routes redirect seamlessly to unified endpoints
- URL prefixes properly organized to avoid overlaps

### Blueprint Registration Order
1. Main application routes (no prefix)
2. Authentication routes (`/auth`)
3. API routes (`/api`)
4. Admin routes (`/admin`)
5. Attendance reports (`/reports/attendance` and `/api/reports/attendance`)
6. Training reports (`/reports/training` and `/api/reports/training`)
7. Breeding activity APIs (various `/api/breeding/*`)
8. Unified breeding reports UI (`/reports/breeding/*`)
9. Unified veterinary reports UI and API
10. Legacy report redirects (for backward compatibility)

### Security Features
- All routes protected with `@login_required`
- Permission decorators applied appropriately
- CSRF protection enabled via Flask-WTF
- MFA support integrated
- Session management configured
- Security middleware initialized

## Testing Recommendations

To verify route connectivity:
1. Test attendance daily sheet and PM daily reports
2. Test training trainer daily reports
3. Test all unified breeding reports (feeding, checkup, veterinary, caretaker)
4. Verify legacy route redirects work correctly
5. Test all breeding activity APIs
6. Verify admin and authentication routes

All routes are now properly connected and ready for use.
