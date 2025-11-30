# دليل نشر نظام إدارة عمليات الكلاب البوليسية K9
# K9 Operations Management System - Deployment Guide

هذا الدليل يشرح خطوة بخطوة كيفية نشر التطبيق على خادم Contabo VPS بدون Docker.

---

## المتطلبات الأساسية

### متطلبات الخادم
- **نظام التشغيل**: Ubuntu 22.04 LTS (موصى به) أو Debian 11+
- **الذاكرة (RAM)**: 2GB كحد أدنى (4GB موصى به)
- **المساحة**: 20GB كحد أدنى
- **Python**: 3.11 أو أحدث
- **PostgreSQL**: 14 أو أحدث

### ما ستحتاجه
- وصول SSH إلى الخادم (عادة root أو sudo)
- اسم نطاق (domain) يشير إلى عنوان IP الخادم
- عنوان بريد إلكتروني للحصول على شهادة SSL

---

## الخطوة 1: تحديث النظام وتثبيت الأساسيات

اتصل بالخادم عبر SSH:
```bash
ssh root@your_server_ip
```

قم بتحديث النظام:
```bash
apt update && apt upgrade -y
```

تثبيت الحزم الأساسية:
```bash
apt install -y python3.11 python3.11-venv python3-pip \
    postgresql postgresql-contrib \
    nginx certbot python3-certbot-nginx \
    git curl wget unzip
```

---

## الخطوة 2: إنشاء مستخدم للتطبيق

لأسباب أمنية، أنشئ مستخدم خاص للتطبيق:
```bash
adduser --system --group --home /home/k9app k9app
```

---

## الخطوة 3: إعداد PostgreSQL

ادخل إلى PostgreSQL:
```bash
sudo -u postgres psql
```

أنشئ قاعدة البيانات والمستخدم:
```sql
-- إنشاء قاعدة البيانات
CREATE DATABASE k9_operations ENCODING 'UTF8';

-- إنشاء المستخدم (غير كلمة المرور!)
CREATE USER k9user WITH PASSWORD 'YOUR_STRONG_PASSWORD_HERE';

-- منح الصلاحيات
GRANT ALL PRIVILEGES ON DATABASE k9_operations TO k9user;
\c k9_operations
GRANT ALL ON SCHEMA public TO k9user;

-- الخروج
\q
```

**مهم جداً**: استبدل `YOUR_STRONG_PASSWORD_HERE` بكلمة مرور قوية!

---

## الخطوة 4: تحميل الكود

انتقل إلى مجلد التطبيق:
```bash
cd /home/k9app
```

### الخيار أ: النسخ من Git
```bash
sudo -u k9app git clone YOUR_REPOSITORY_URL app
```

### الخيار ب: رفع الملفات يدوياً
ارفع الملفات باستخدام SCP أو SFTP:
```bash
# من جهازك المحلي:
scp -r ./your_project_folder root@your_server_ip:/home/k9app/app
chown -R k9app:k9app /home/k9app/app
```

---

## الخطوة 5: إعداد بيئة Python

```bash
cd /home/k9app/app

# إنشاء بيئة افتراضية
sudo -u k9app python3.11 -m venv venv

# تفعيل البيئة
source venv/bin/activate

# تثبيت المتطلبات
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

---

## الخطوة 6: إعداد متغيرات البيئة

أنشئ ملف البيئة:
```bash
sudo -u k9app nano /home/k9app/app/.env
```

أضف المحتوى التالي (عدل القيم!):
```bash
# إعداد الإنتاج
FLASK_ENV=production

# مفتاح الجلسة (أنشئ مفتاح قوي!)
# python -c "import secrets; print(secrets.token_urlsafe(32))"
SESSION_SECRET=YOUR_GENERATED_SECRET_KEY

# اتصال قاعدة البيانات
DATABASE_URL=postgresql://k9user:YOUR_PASSWORD@localhost:5432/k9_operations
PGHOST=localhost
PGPORT=5432
PGDATABASE=k9_operations
PGUSER=k9user
PGPASSWORD=YOUR_PASSWORD
```

لتوليد مفتاح الجلسة:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## الخطوة 7: إعداد قاعدة البيانات

تفعيل البيئة وتشغيل الترحيل:
```bash
cd /home/k9app/app
source venv/bin/activate

# تصدير متغيرات البيئة
export $(cat .env | xargs)

# تشغيل ترحيل قاعدة البيانات
flask db upgrade
```

### إنشاء المستخدم الأول (مشرف عام)

أنشئ سكريبت لإضافة المستخدم:
```bash
nano /home/k9app/app/create_admin.py
```

```python
#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/home/k9app/app')

from app import app, db
from k9.models.models import User, UserRole
from werkzeug.security import generate_password_hash
import uuid

def create_admin():
    with app.app_context():
        # تحقق من وجود مستخدم
        existing = User.query.filter_by(username='admin').first()
        if existing:
            print("المستخدم 'admin' موجود بالفعل")
            return
        
        # إنشاء المستخدم
        admin = User()
        admin.id = str(uuid.uuid4())
        admin.username = 'admin'
        admin.email = 'admin@example.com'
        admin.password_hash = generate_password_hash('CHANGE_THIS_PASSWORD')
        admin.role = UserRole.GENERAL_ADMIN
        admin.is_active = True
        
        db.session.add(admin)
        db.session.commit()
        print("تم إنشاء المستخدم 'admin' بنجاح!")
        print("مهم: غير كلمة المرور فوراً بعد تسجيل الدخول!")

if __name__ == '__main__':
    create_admin()
```

شغل السكريبت:
```bash
source venv/bin/activate
export $(cat .env | xargs)
python create_admin.py
```

---

## الخطوة 8: إعداد Gunicorn

أنشئ ملف إعدادات Gunicorn:
```bash
nano /home/k9app/app/gunicorn.conf.py
```

```python
# Gunicorn configuration
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/home/k9app/logs/gunicorn-access.log"
errorlog = "/home/k9app/logs/gunicorn-error.log"
loglevel = "info"

# Process naming
proc_name = "k9-gunicorn"

# Daemon mode (when running with systemd, set to False)
daemon = False

# Environment variables
raw_env = [
    "FLASK_ENV=production",
]
```

أنشئ مجلد السجلات:
```bash
mkdir -p /home/k9app/logs
chown k9app:k9app /home/k9app/logs
```

---

## الخطوة 9: إعداد Systemd Service

أنشئ ملف الخدمة:
```bash
nano /etc/systemd/system/k9app.service
```

```ini
[Unit]
Description=K9 Operations Management System
After=network.target postgresql.service

[Service]
User=k9app
Group=k9app
WorkingDirectory=/home/k9app/app
EnvironmentFile=/home/k9app/app/.env
ExecStart=/home/k9app/app/venv/bin/gunicorn --config gunicorn.conf.py main:app
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

تفعيل وتشغيل الخدمة:
```bash
systemctl daemon-reload
systemctl enable k9app
systemctl start k9app

# التحقق من الحالة
systemctl status k9app
```

---

## الخطوة 10: إعداد Nginx

أنشئ ملف إعدادات Nginx:
```bash
nano /etc/nginx/sites-available/k9app
```

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL certificates (will be configured by Certbot)
    # ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Max upload size
    client_max_body_size 20M;
    
    # Static files
    location /static {
        alias /home/k9app/app/k9/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Uploaded files
    location /uploads {
        alias /home/k9app/app/uploads;
        expires 1d;
    }
    
    # Application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

**مهم**: استبدل `your-domain.com` باسم نطاقك الفعلي!

فعّل الموقع:
```bash
ln -s /etc/nginx/sites-available/k9app /etc/nginx/sites-enabled/
nginx -t  # اختبار الإعدادات
systemctl reload nginx
```

---

## الخطوة 11: إعداد SSL (HTTPS)

### باستخدام Let's Encrypt (مجاني)
```bash
certbot --nginx -d your-domain.com -d www.your-domain.com
```

اتبع التعليمات وأدخل بريدك الإلكتروني.

### التجديد التلقائي
Certbot يضيف تلقائياً مهمة للتجديد. للتحقق:
```bash
certbot renew --dry-run
```

---

## الخطوة 12: إعداد جدار الحماية

```bash
# تفعيل UFW
ufw enable

# السماح بـ SSH
ufw allow ssh

# السماح بـ HTTP و HTTPS
ufw allow 'Nginx Full'

# التحقق
ufw status
```

---

## الخطوة 13: إعداد النسخ الاحتياطي

أنشئ سكريبت النسخ الاحتياطي:
```bash
nano /home/k9app/backup.sh
```

```bash
#!/bin/bash

# إعدادات
BACKUP_DIR="/home/k9app/backups"
DB_NAME="k9_operations"
DB_USER="k9user"
DAYS_TO_KEEP=7
DATE=$(date +%Y%m%d_%H%M%S)

# إنشاء المجلد إن لم يوجد
mkdir -p $BACKUP_DIR

# النسخ الاحتياطي
PGPASSWORD=$PGPASSWORD pg_dump -h localhost -U $DB_USER $DB_NAME > "$BACKUP_DIR/db_$DATE.sql"

# ضغط الملف
gzip "$BACKUP_DIR/db_$DATE.sql"

# حذف النسخ القديمة
find $BACKUP_DIR -name "*.sql.gz" -mtime +$DAYS_TO_KEEP -delete

echo "Backup completed: db_$DATE.sql.gz"
```

```bash
chmod +x /home/k9app/backup.sh
```

إضافة مهمة cron:
```bash
crontab -e
```

أضف:
```
# نسخة احتياطية يومية الساعة 2 صباحاً
0 2 * * * /home/k9app/backup.sh >> /home/k9app/logs/backup.log 2>&1
```

---

## الخطوة 14: تدوير السجلات (Log Rotation)

```bash
nano /etc/logrotate.d/k9app
```

```
/home/k9app/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 k9app k9app
    sharedscripts
    postrotate
        systemctl reload k9app
    endscript
}
```

---

## الأوامر المفيدة

### إدارة الخدمة
```bash
# تشغيل/إيقاف/إعادة تشغيل
systemctl start k9app
systemctl stop k9app
systemctl restart k9app

# عرض الحالة
systemctl status k9app

# عرض السجلات
journalctl -u k9app -f
```

### تحديث التطبيق
```bash
cd /home/k9app/app
git pull origin main  # أو نسخ الملفات الجديدة
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
systemctl restart k9app
```

### السجلات
```bash
# سجلات Gunicorn
tail -f /home/k9app/logs/gunicorn-error.log
tail -f /home/k9app/logs/gunicorn-access.log

# سجلات Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

---

## استكشاف الأخطاء

### التطبيق لا يعمل
```bash
# تحقق من الخدمة
systemctl status k9app

# تحقق من السجلات
journalctl -u k9app -n 50

# تحقق من Nginx
nginx -t
systemctl status nginx
```

### مشاكل قاعدة البيانات
```bash
# تحقق من PostgreSQL
systemctl status postgresql

# اختبار الاتصال
sudo -u postgres psql -c "SELECT 1"
```

### مشاكل الصلاحيات
```bash
# إصلاح صلاحيات الملفات
chown -R k9app:k9app /home/k9app/app
chmod -R 755 /home/k9app/app
```

---

## قائمة التحقق النهائية

- [ ] تغيير كلمة مرور PostgreSQL
- [ ] توليد SESSION_SECRET قوي
- [ ] تغيير كلمة مرور المستخدم admin
- [ ] إعداد SSL/HTTPS
- [ ] تفعيل جدار الحماية
- [ ] إعداد النسخ الاحتياطي
- [ ] اختبار تسجيل الدخول
- [ ] اختبار جميع الوظائف الرئيسية
- [ ] مراقبة السجلات للأخطاء

---

## الدعم والمساعدة

إذا واجهت أي مشاكل:
1. تحقق من السجلات أولاً
2. تأكد من صحة متغيرات البيئة
3. تأكد من تشغيل جميع الخدمات

بالتوفيق في نشر التطبيق! 🎉
