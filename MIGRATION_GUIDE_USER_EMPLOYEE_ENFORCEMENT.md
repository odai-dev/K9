# User-Employee Enforcement Migration Guide

## Overview
All users in the system must now be linked to employee records. This ensures proper access control and data integrity.

## What Changed

### 1. Database Schema
- Added required `employee_id` foreign key to the `User` model
- All users must have a linked employee record
- Added validation to prevent creating users without employee records

### 2. User Creation Flow
- **Setup Route**: First-time admin creation now creates employee record first
- **Admin Script**: `scripts/create_admin_user.py` updated to require employee details
- **Login Security**: Added check to prevent login if employee record is missing or inactive

### 3. Migration Required
Before these changes take effect, you **MUST** run the database migration:

```bash
# Apply the migration
flask db upgrade
```

This migration will:
1. Add the `employee_id` column to the `user` table
2. Link existing users to their employee records (if they exist)
3. Create new employee records for users without them
4. Enforce the NOT NULL constraint on `employee_id`

## How to Use

### Creating New Admin Users
When creating admin users with the script, you'll now need to provide employee details:

```bash
python scripts/create_admin_user.py
```

You'll be prompted for:
- Username
- Email
- Full name
- **Employee ID** (new requirement)
- **Phone number** (new requirement)
- Password

### Initial System Setup
The setup page (`/setup`) will automatically create both user and employee records for the first admin.

## Important Notes

### ⚠️ Before Deploying
1. **Backup your database** before running the migration
2. Run `flask db upgrade` to apply the schema changes
3. Verify all users have employee records by checking the admin dashboard

### Migration Safety
The migration script will:
- ✅ Preserve all existing user data
- ✅ Link users to existing employees where possible
- ✅ Create new employee records for users without them
- ✅ Support both PostgreSQL and SQLite databases

### Rollback
If needed, you can rollback the migration:

```bash
flask db downgrade
```

## Testing
After migration, test the following:
1. ✓ Login with existing users
2. ✓ Create new admin users via script
3. ✓ Initial system setup (if applicable)
4. ✓ Check that all users show linked employee information

## Troubleshooting

### Issue: Login fails with "User account not linked to employee"
**Solution**: Run the migration script to ensure all users have employee records:
```bash
flask db upgrade
```

### Issue: Cannot create new users
**Solution**: Ensure you're providing employee details when creating users. All users must have:
- Employee ID
- Phone number
- Name
- Email

### Issue: Migration fails
**Solution**: 
1. Check database logs for specific errors
2. Ensure database is accessible
3. Verify you have the latest code from the repository
4. Contact support with the error message

## Files Modified
- `k9/models/models.py` - User model with required employee_id
- `k9/routes/auth.py` - Updated setup route and login security
- `scripts/create_admin_user.py` - Updated to create employee records
- `migrations/versions/add_required_employee_id_to_user.py` - New migration

## Summary
This change strengthens the security and data integrity of the system by ensuring that all users are properly registered employees with complete personnel records.
