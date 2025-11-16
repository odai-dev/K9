#!/usr/bin/env python3
"""
Security Validation Script
Scans codebase for common security anti-patterns and disabled checks.
Run before deployment to catch issues early.
"""

import os
import sys
import re
from pathlib import Path

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def error(msg):
    print(f"{Colors.RED}✗ ERROR: {msg}{Colors.END}")

def warning(msg):
    print(f"{Colors.YELLOW}⚠ WARNING: {msg}{Colors.END}")

def success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

class SecurityValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def scan_file(self, filepath):
        """Scan a single file for security issues"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            # Check 1: Bypassed role checks
            if 'if True:  # Role check bypassed' in content:
                for i, line in enumerate(lines, 1):
                    if 'if True:  # Role check bypassed' in line:
                        self.errors.append(
                            f"{filepath}:{i} - Bypassed role check found: 'if True'"
                        )
            
            # Check 2: Disabled role checks
            if '# ROLE CHECK DISABLED:' in content:
                for i, line in enumerate(lines, 1):
                    if '# ROLE CHECK DISABLED:' in line:
                        self.warnings.append(
                            f"{filepath}:{i} - Disabled role check comment found"
                        )
            
            # Check 3: Non-existent properties
            if 'current_user.is_general_admin' in content:
                for i, line in enumerate(lines, 1):
                    if 'current_user.is_general_admin' in line:
                        self.errors.append(
                            f"{filepath}:{i} - Invalid property: current_user.is_general_admin (use is_admin() instead)"
                        )
            
            # Check 4: Hardcoded admin bypass (common mistake)
            patterns = [
                r'if\s+True\s*:\s*#.*admin',
                r'if\s+True\s*:\s*#.*role',
                r'if\s+True\s*:\s*#.*permission',
            ]
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    for i, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            self.errors.append(
                                f"{filepath}:{i} - Suspicious hardcoded bypass: {line.strip()}"
                            )
            
            # Check 5: Missing @login_required on routes
            if filepath.endswith('_routes.py') or filepath.endswith('/routes/'):
                route_pattern = r'@\w+\.route\('
                login_required_pattern = r'@login_required'
                
                route_positions = []
                for i, line in enumerate(lines, 1):
                    if re.search(route_pattern, line):
                        route_positions.append((i, line.strip()))
                
                for route_line, route_code in route_positions:
                    # Check the 5 lines before the route for @login_required
                    start = max(0, route_line - 6)
                    end = route_line
                    preceding_lines = '\n'.join(lines[start:end])
                    
                    # Skip if this is a public route (auth, etc)
                    if '/auth/' in filepath or 'auth_bp' in preceding_lines:
                        continue
                    
                    if '@login_required' not in preceding_lines:
                        self.warnings.append(
                            f"{filepath}:{route_line} - Route may be missing @login_required: {route_code}"
                        )
        
        except Exception as e:
            warning(f"Could not scan {filepath}: {e}")
    
    def scan_directory(self, directory, extensions=None):
        """Recursively scan directory for issues"""
        if extensions is None:
            extensions = ['.py', '.html']
        
        info(f"Scanning {directory}...")
        
        for root, dirs, files in os.walk(directory):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', 'node_modules', '.venv']]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    filepath = os.path.join(root, file)
                    self.scan_file(filepath)
    
    def report(self):
        """Print validation report"""
        print("\n" + "="*70)
        print("SECURITY VALIDATION REPORT")
        print("="*70 + "\n")
        
        if self.errors:
            error(f"Found {len(self.errors)} critical error(s):")
            for err in self.errors:
                print(f"  {err}")
            print()
        
        if self.warnings:
            warning(f"Found {len(self.warnings)} warning(s):")
            for warn in self.warnings[:10]:  # Show first 10
                print(f"  {warn}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more")
            print()
        
        if not self.errors and not self.warnings:
            success("No security issues found!")
            return True
        
        if self.errors:
            error(f"Validation FAILED with {len(self.errors)} critical error(s)")
            return False
        else:
            success(f"Validation PASSED (with {len(self.warnings)} warnings)")
            return True

def main():
    """Run security validation"""
    validator = SecurityValidator()
    
    # Scan key directories
    directories = ['k9/routes', 'k9/utils', 'k9/templates', 'k9/api']
    
    for directory in directories:
        if os.path.exists(directory):
            validator.scan_directory(directory)
    
    # Generate report
    success_status = validator.report()
    
    # Exit with appropriate code
    sys.exit(0 if success_status else 1)

if __name__ == '__main__':
    main()
