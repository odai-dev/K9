# Security Scripts

## validate_security.py

Automated security validation script that scans the K9 Operations codebase for common security vulnerabilities and anti-patterns.

### Usage

Run before any deployment or major commit:

```bash
python3 scripts/validate_security.py
```

### What It Checks

1. **Bypassed Role Checks**: Detects `if True: # Role check bypassed` patterns
2. **Non-Existent Properties**: Flags use of `current_user.is_general_admin` (does not exist)
3. **Missing Authentication**: Warns about routes without `@login_required` decorators
4. **Hardcoded Bypasses**: Finds suspicious admin/role/permission bypasses

### Exit Codes

- **0**: Validation passed (may have warnings)
- **1**: Validation failed (critical errors found)

### Output

The script provides a detailed report showing:
- File path and line number for each issue
- Issue description and severity (ERROR vs WARNING)
- Total count of errors and warnings

### Integration

Consider adding this to your CI/CD pipeline or pre-commit hooks:

```bash
# Exit if validation fails
python3 scripts/validate_security.py || exit 1
```

### Example Output

```
✗ ERROR: Found 2 critical error(s):
  k9/routes/main.py:123 - Bypassed role check found: 'if True'
  k9/templates/base.html:45 - Invalid property: current_user.is_general_admin

✓ Validation PASSED (with 5 warnings)
```

## See Also

- `SECURITY_GUIDELINES.md` - Comprehensive security documentation
- `replit.md` - Project documentation and recent changes
