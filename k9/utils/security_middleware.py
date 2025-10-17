from flask import request, g, current_app, abort
from datetime import datetime, timedelta
import os
import re
from typing import Dict, List, Optional

class SecurityMiddleware:
    """Security middleware for enhanced protection."""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security middleware with Flask app."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Rate limiting storage (in production use Redis)
        if not hasattr(app, 'rate_limit_storage'):
            app.rate_limit_storage = {}
    
    def before_request(self):
        """Execute before each request."""
        # Rate limiting
        if not self._check_rate_limit():
            abort(429)  # Too Many Requests
        
        # IP blocking (basic implementation)
        if self._is_blocked_ip():
            abort(403)  # Forbidden
        
        # Request size limiting
        if self._is_request_too_large():
            abort(413)  # Request Entity Too Large
        
        # Set security context
        g.request_start_time = datetime.utcnow()
        g.client_ip = self._get_client_ip()
        g.user_agent = request.headers.get('User-Agent', '')
    
    def after_request(self, response):
        """Execute after each request."""
        # Add security headers
        self._add_security_headers(response)
        
        # Log request if needed
        self._log_request(response)
        
        return response
    
    def _check_rate_limit(self) -> bool:
        """Basic rate limiting implementation."""
        if current_app.testing:
            return True
        
        ip = self._get_client_ip()
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=5)
        
        # Clean old entries
        storage = current_app.rate_limit_storage
        if ip in storage:
            storage[ip] = [req_time for req_time in storage[ip] if req_time > window_start]
        else:
            storage[ip] = []
        
        # Check limit (1500 requests per 5 minutes - configurable via env)
        rate_limit = int(os.environ.get('RATE_LIMIT_REQUESTS', '1500'))
        if len(storage[ip]) >= rate_limit:
            return False
        
        # Add current request
        storage[ip].append(now)
        return True
    
    def _is_blocked_ip(self) -> bool:
        """Check if IP is in block list."""
        # In production, this would check against a database or Redis
        blocked_ips = os.environ.get('BLOCKED_IPS', '').split(',')
        client_ip = self._get_client_ip()
        return client_ip in blocked_ips
    
    def _is_request_too_large(self) -> bool:
        """Check if request is too large."""
        content_length = request.content_length
        if content_length is None:
            return False
        
        # 16MB limit
        max_size = 16 * 1024 * 1024
        return content_length > max_size
    
    def _get_client_ip(self) -> str:
        """Get real client IP considering proxies."""
        # Check common proxy headers
        for header in ['X-Forwarded-For', 'X-Real-IP', 'X-Client-IP']:
            ip = request.headers.get(header)
            if ip:
                # Take first IP if comma-separated
                return ip.split(',')[0].strip()
        
        return request.remote_addr or 'unknown'
    
    def _add_security_headers(self, response):
        """Add comprehensive security headers."""
        
        # Content Security Policy
        csp = self._build_csp()
        response.headers['Content-Security-Policy'] = csp
        
        # XSS Protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Content Type Options
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Frame Options
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Feature Policy
        response.headers['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), '
            'payment=(), usb=(), magnetometer=(), gyroscope=()'
        )
        
        # HSTS (only over HTTPS)
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )
        
        # Additional headers
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
        
        # Cache control for sensitive pages
        if self._is_sensitive_page():
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
    
    def _build_csp(self) -> str:
        """Build Content Security Policy."""
        # Base CSP for the application
        csp_directives = {
            'default-src': ["'self'"],
            'script-src': [
                "'self'",
                "'unsafe-inline'",  # Needed for inline scripts (consider removing in production)
                'https://cdn.jsdelivr.net',
                'https://cdnjs.cloudflare.com',
                'https://code.jquery.com',
                'https://stackpath.bootstrapcdn.com'
            ],
            'style-src': [
                "'self'",
                "'unsafe-inline'",  # Needed for inline styles
                'https://fonts.googleapis.com',
                'https://cdn.jsdelivr.net',
                'https://cdnjs.cloudflare.com',
                'https://stackpath.bootstrapcdn.com'
            ],
            'font-src': [
                "'self'",
                'https://fonts.gstatic.com',
                'https://cdn.jsdelivr.net'
            ],
            'img-src': [
                "'self'",
                'data:',  # For base64 images (QR codes)
                'blob:',  # For image upload previews
                'https:'  # Allow HTTPS images
            ],
            'connect-src': [
                "'self'"
            ],
            'frame-src': [
                "'none'"
            ],
            'object-src': [
                "'none'"
            ],
            'media-src': [
                "'self'"
            ],
            'form-action': [
                "'self'"
            ],
            'base-uri': [
                "'self'"
            ],
            'manifest-src': [
                "'self'"
            ]
        }
        
        # Build CSP string
        csp_parts = []
        for directive, sources in csp_directives.items():
            csp_parts.append(f"{directive} {' '.join(sources)}")
        
        return '; '.join(csp_parts)
    
    def _is_sensitive_page(self) -> bool:
        """Check if current page contains sensitive information."""
        sensitive_paths = [
            '/login', '/password-reset', '/mfa', '/admin',
            '/auth', '/users', '/employees'
        ]
        
        path = request.path.lower()
        return any(sensitive_path in path for sensitive_path in sensitive_paths)
    
    def _log_request(self, response):
        """Log security-relevant requests."""
        # Log failed authentication attempts
        if (response.status_code == 401 or 
            (response.status_code == 200 and 'login' in request.path and request.method == 'POST')):
            
            current_app.logger.warning(
                f"Auth attempt: {request.method} {request.path} "
                f"from {g.client_ip} - Status: {response.status_code}"
            )
        
        # Log admin access
        if '/admin' in request.path and response.status_code == 200:
            current_app.logger.info(
                f"Admin access: {request.method} {request.path} "
                f"from {g.client_ip}"
            )
        
        # Log suspicious patterns
        suspicious_patterns = [
            r'\.\./', r'<script', r'union.*select', r'drop.*table',
            r'exec.*xp_', r'eval\(', r'javascript:', r'vbscript:'
        ]
        
        query_string = request.query_string.decode('utf-8', errors='ignore').lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, query_string, re.IGNORECASE):
                current_app.logger.warning(
                    f"Suspicious request: {request.method} {request.path}?{query_string} "
                    f"from {g.client_ip} - Pattern: {pattern}"
                )
                break

class AuditLogger:
    """Enhanced audit logging system."""
    
    @staticmethod
    def log_security_event(event_type: str, user_id: str = None, details: Dict = None):
        """Log security events with enhanced details."""
        from k9.utils.utils import log_audit
        
        # Get request context
        ip_address = getattr(g, 'client_ip', 'unknown')
        user_agent = getattr(g, 'user_agent', 'unknown')
        
        # Enhanced details
        enhanced_details = {
            'event_type': event_type,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': datetime.utcnow().isoformat(),
            'request_path': request.path if request else 'unknown',
            'request_method': request.method if request else 'unknown',
            'session_id': request.headers.get('X-Session-ID', 'unknown') if request else 'unknown',
            **(details or {})
        }
        
        # Log to audit system
        log_audit(
            user_id=user_id or 'system',
            action='SECURITY_EVENT',
            target_type='Security',
            target_id=event_type,
            details=enhanced_details
        )
        
        # Also log to application logger for immediate visibility
        log_level = current_app.logger.warning
        if event_type in ['FAILED_LOGIN', 'ACCOUNT_LOCKED', 'SUSPICIOUS_ACTIVITY']:
            log_level = current_app.logger.error
        elif event_type in ['SUCCESSFUL_LOGIN', 'PASSWORD_CHANGED']:
            log_level = current_app.logger.info
        
        log_level(f"Security Event: {event_type} - User: {user_id} - IP: {ip_address}")
    
    @staticmethod
    def log_admin_action(user_id: str, action: str, target: str, details: Dict = None):
        """Log administrative actions."""
        AuditLogger.log_security_event(
            event_type='ADMIN_ACTION',
            user_id=user_id,
            details={
                'admin_action': action,
                'target': target,
                **(details or {})
            }
        )
    
    @staticmethod
    def log_data_access(user_id: str, data_type: str, operation: str, details: Dict = None):
        """Log data access events."""
        AuditLogger.log_security_event(
            event_type='DATA_ACCESS',
            user_id=user_id,
            details={
                'data_type': data_type,
                'operation': operation,
                **(details or {})
            }
        )