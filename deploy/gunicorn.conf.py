# Gunicorn configuration for K9 Operations Management System
# Copy this file to /home/k9app/app/gunicorn.conf.py on your server

import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
# Rule of thumb: 2-4 workers per CPU core
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Restart workers after this many requests (prevents memory leaks)
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
