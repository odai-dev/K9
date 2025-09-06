import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from flask import current_app, render_template_string
from typing import Optional

class EmailService:
    """Email service for sending notifications and alerts."""
    
    def __init__(self):
        self.sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        self.from_email = "noreply@k9system.local"
        self.from_name = "نظام إدارة عمليات K9"
    
    def _get_sendgrid_client(self):
        """Get SendGrid client if API key is available."""
        if not self.sendgrid_key:
            return None
        
        try:
            from sendgrid import SendGridAPIClient
            return SendGridAPIClient(self.sendgrid_key)
        except ImportError:
            current_app.logger.warning("SendGrid library not available")
            return None
    
    def send_password_reset_email(self, user_email: str, user_name: str, reset_token: str, reset_url: str) -> bool:
        """Send password reset email."""
        
        subject = "إعادة تعيين كلمة المرور - نظام إدارة عمليات K9"
        
        # HTML email template
        html_template = """
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>إعادة تعيين كلمة المرور</title>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; direction: rtl; background-color: #f8f9fa; margin: 0; padding: 20px; }
                .container { max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                .content { padding: 30px; }
                .button { display: inline-block; background-color: #007bff; color: white; text-decoration: none; padding: 12px 30px; border-radius: 5px; margin: 20px 0; font-weight: bold; }
                .button:hover { background-color: #0056b3; }
                .warning { background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .footer { background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; color: #6c757d; font-size: 14px; }
                .token-box { background-color: #f8f9fa; border: 2px dashed #dee2e6; padding: 15px; text-align: center; margin: 20px 0; border-radius: 5px; }
                .token { font-family: 'Courier New', monospace; font-size: 16px; font-weight: bold; color: #007bff; letter-spacing: 1px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 إعادة تعيين كلمة المرور</h1>
                    <p>نظام إدارة عمليات K9</p>
                </div>
                
                <div class="content">
                    <h2>مرحباً {{ user_name }}</h2>
                    <p>تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بحسابك في نظام إدارة عمليات K9.</p>
                    
                    <p>لإعادة تعيين كلمة المرور، انقر على الرابط أدناه أو انسخ الرمز المرفق:</p>
                    
                    <div style="text-align: center;">
                        <a href="{{ reset_url }}" class="button">إعادة تعيين كلمة المرور</a>
                    </div>
                    
                    <div class="token-box">
                        <p><strong>أو استخدم هذا الرمز:</strong></p>
                        <div class="token">{{ reset_token }}</div>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ تنبيه أمني:</strong>
                        <ul>
                            <li>هذا الرابط صالح لمدة 24 ساعة فقط</li>
                            <li>إذا لم تطلب إعادة تعيين كلمة المرور، تجاهل هذا الإيميل</li>
                            <li>لا تشارك هذا الرابط أو الرمز مع أي شخص آخر</li>
                            <li>إذا كنت تشك في اختراق حسابك، تواصل مع الإدارة فوراً</li>
                        </ul>
                    </div>
                    
                    <p>إذا لم تتمكن من النقر على الرابط، انسخ الرابط التالي والصقه في متصفحك:</p>
                    <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace;">
                        {{ reset_url }}
                    </p>
                </div>
                
                <div class="footer">
                    <p>هذا إيميل تلقائي، يرجى عدم الرد عليه</p>
                    <p>© 2025 نظام إدارة عمليات K9 - جميع الحقوق محفوظة</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Text email template (fallback)
        text_template = """
        إعادة تعيين كلمة المرور - نظام إدارة عمليات K9
        
        مرحباً {{ user_name }}
        
        تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بحسابك.
        
        لإعادة تعيين كلمة المرور، انسخ الرابط التالي والصقه في متصفحك:
        {{ reset_url }}
        
        أو استخدم الرمز التالي: {{ reset_token }}
        
        تنبيه أمني:
        - هذا الرابط صالح لمدة 24 ساعة فقط
        - إذا لم تطلب إعادة تعيين كلمة المرور، تجاهل هذا الإيميل
        - لا تشارك هذا الرابط أو الرمز مع أي شخص آخر
        
        نظام إدارة عمليات K9
        """
        
        # Render templates
        html_content = render_template_string(html_template, 
                                            user_name=user_name, 
                                            reset_token=reset_token, 
                                            reset_url=reset_url)
        text_content = render_template_string(text_template, 
                                            user_name=user_name, 
                                            reset_token=reset_token, 
                                            reset_url=reset_url)
        
        return self._send_email(user_email, subject, text_content, html_content)
    
    def send_security_alert_email(self, user_email: str, user_name: str, alert_type: str, details: dict) -> bool:
        """Send security alert email."""
        
        subject = f"تنبيه أمني - {alert_type} - نظام إدارة عمليات K9"
        
        alert_messages = {
            'password_changed': 'تم تغيير كلمة المرور',
            'mfa_enabled': 'تم تفعيل المصادقة الثنائية',
            'mfa_disabled': 'تم إلغاء المصادقة الثنائية',
            'account_locked': 'تم قفل الحساب',
            'suspicious_login': 'محاولة دخول مشبوهة',
            'admin_access': 'وصول المدير لحسابك'
        }
        
        alert_message = alert_messages.get(alert_type, 'نشاط أمني')
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; direction: rtl; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #dc3545; color: white; padding: 20px; text-align: center;">
                <h2>🚨 تنبيه أمني</h2>
            </div>
            <div style="padding: 20px; background-color: #f8f9fa;">
                <h3>مرحباً {user_name}</h3>
                <p><strong>حدث نشاط أمني على حسابك:</strong> {alert_message}</p>
                
                <div style="background-color: white; padding: 15px; border-left: 4px solid #dc3545; margin: 15px 0;">
                    <h4>تفاصيل النشاط:</h4>
                    <ul>
        """
        
        for key, value in details.items():
            html_content += f"<li><strong>{key}:</strong> {value}</li>"
        
        html_content += """
                    </ul>
                </div>
                
                <p>إذا لم تقم بهذا النشاط، يرجى:</p>
                <ul>
                    <li>تغيير كلمة المرور فوراً</li>
                    <li>تفعيل المصادقة الثنائية</li>
                    <li>التواصل مع الإدارة</li>
                </ul>
                
                <p style="color: #6c757d; font-size: 12px; margin-top: 30px;">
                    هذا إيميل تلقائي من نظام إدارة عمليات K9
                </p>
            </div>
        </div>
        """
        
        text_content = f"""
        تنبيه أمني - نظام إدارة عمليات K9
        
        مرحباً {user_name}
        
        حدث نشاط أمني على حسابك: {alert_message}
        
        تفاصيل النشاط:
        """
        
        for key, value in details.items():
            text_content += f"- {key}: {value}\n"
        
        text_content += """
        
        إذا لم تقم بهذا النشاط، يرجى:
        - تغيير كلمة المرور فوراً
        - تفعيل المصادقة الثنائية
        - التواصل مع الإدارة
        
        نظام إدارة عمليات K9
        """
        
        return self._send_email(user_email, subject, text_content, html_content)
    
    def _send_email(self, to_email: str, subject: str, text_content: str, html_content: str = None) -> bool:
        """Send email using available service."""
        
        # Try SendGrid first
        if self._send_via_sendgrid(to_email, subject, text_content, html_content):
            return True
        
        # Fallback to SMTP if configured
        if self._send_via_smtp(to_email, subject, text_content, html_content):
            return True
        
        # Log email content if no service available (development mode)
        current_app.logger.info(f"Email would be sent to {to_email}")
        current_app.logger.info(f"Subject: {subject}")
        current_app.logger.info(f"Content: {text_content[:200]}...")
        
        return False
    
    def _send_via_sendgrid(self, to_email: str, subject: str, text_content: str, html_content: str = None) -> bool:
        """Send email via SendGrid."""
        sg = self._get_sendgrid_client()
        if not sg:
            return False
        
        try:
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=subject
            )
            
            if html_content:
                message.content = [
                    Content("text/plain", text_content),
                    Content("text/html", html_content)
                ]
            else:
                message.content = Content("text/plain", text_content)
            
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                current_app.logger.info(f"Email sent successfully to {to_email} via SendGrid")
                return True
            else:
                current_app.logger.warning(f"SendGrid failed with status {response.status_code}")
                return False
                
        except Exception as e:
            current_app.logger.error(f"SendGrid error: {e}")
            return False
    
    def _send_via_smtp(self, to_email: str, subject: str, text_content: str, html_content: str = None) -> bool:
        """Send email via SMTP (if configured)."""
        # SMTP configuration would go here
        # For now, just log that SMTP is not configured
        current_app.logger.info("SMTP not configured, email not sent")
        return False