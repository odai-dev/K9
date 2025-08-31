# K9 Operations Management System - Production Deployment Guide

This guide provides comprehensive instructions for deploying the K9 Operations Management System in production using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+ and Docker Compose 2.0+
- A server with at least 2GB RAM and 10GB disk space
- Domain name (for SSL configuration)
- Basic knowledge of Docker and Linux administration

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repository-url>
cd k9-operations-system

# Copy environment template
cp .env.example .env
```

### 2. Configure Environment

Edit the `.env` file with your production values:

```bash
# Generate a secure password for PostgreSQL
POSTGRES_PASSWORD=your_secure_database_password_here

# Generate a secure session secret (32+ characters)
# You can use: python -c "import secrets; print(secrets.token_urlsafe(32))"
SESSION_SECRET=your_secure_random_session_secret_here

# Optional: Customize other settings
POSTGRES_DB=k9operations
POSTGRES_USER=k9user
WEB_PORT=80
GUNICORN_WORKERS=4
```

### 3. Build and Deploy

```bash
# Build the application
docker-compose build

# Start the services
docker-compose up -d

# Check that services are running
docker-compose ps

# View logs
docker-compose logs web
```

### 4. Initialize the Database

The system will automatically run database migrations on startup. To manually run migrations:

```bash
# Run migrations
docker-compose exec web flask db upgrade

# Check database connection
docker-compose exec web flask shell
```

### 5. Create Admin User

Since production mode doesn't create a default admin user, create one manually:

```bash
# Connect to the container
docker-compose exec web flask shell

# In the Flask shell:
from models import User, UserRole
from werkzeug.security import generate_password_hash
from app import db

# Create admin user
admin = User()
admin.username = 'admin'
admin.email = 'admin@yourdomain.com'
admin.password_hash = generate_password_hash('your_secure_password')
admin.role = UserRole.GENERAL_ADMIN
admin.full_name = 'System Administrator'
admin.active = True

db.session.add(admin)
db.session.commit()
print("Admin user created successfully")
exit()
```

## Production Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes (auto-generated) | - |
| `SESSION_SECRET` | Secret key for sessions | Yes | - |
| `POSTGRES_DB` | Database name | Yes | k9operations |
| `POSTGRES_USER` | Database user | Yes | k9user |
| `POSTGRES_PASSWORD` | Database password | Yes | - |
| `WEB_PORT` | External port for web service | No | 80 |
| `GUNICORN_WORKERS` | Number of Gunicorn workers | No | 4 |

### Security Considerations

1. **Change Default Credentials**: The development admin account (admin/admin123) is disabled in production
2. **Strong Passwords**: Use strong, unique passwords for database and session secrets
3. **Firewall**: Configure firewall to only allow necessary ports (80, 443, SSH)
4. **SSL/TLS**: Use the provided Nginx configuration for SSL termination
5. **Regular Updates**: Keep Docker images and the host system updated

## Reverse Proxy and SSL Setup

### Using Nginx (Recommended)

1. Install Nginx on your host system:
```bash
sudo apt update && sudo apt install nginx
```

2. Copy the provided configuration:
```bash
sudo cp nginx.conf.example /etc/nginx/sites-available/k9-operations
sudo ln -s /etc/nginx/sites-available/k9-operations /etc/nginx/sites-enabled/
```

3. Edit the configuration file:
```bash
sudo nano /etc/nginx/sites-enabled/k9-operations
```

4. Update the following in the Nginx config:
   - Replace `your-domain.com` with your actual domain
   - Update SSL certificate paths
   - Adjust the Docker volume path for uploads

5. Obtain SSL certificates (using Let's Encrypt):
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

6. Test and reload Nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Management Commands

### Viewing Logs
```bash
# All services
docker-compose logs

# Web service only
docker-compose logs web

# Database service only
docker-compose logs db

# Follow logs in real-time
docker-compose logs -f web
```

### Database Operations
```bash
# Create a new migration
docker-compose exec web flask db migrate -m "Description of changes"

# Apply migrations
docker-compose exec web flask db upgrade

# Database backup
docker-compose exec db pg_dump -U k9user k9operations > backup.sql

# Database restore
docker-compose exec -T db psql -U k9user k9operations < backup.sql
```

### Scaling and Performance

#### Horizontal Scaling
```bash
# Scale web service to 3 instances
docker-compose up -d --scale web=3

# Update Nginx upstream configuration accordingly
```

#### Resource Limits
Add to `docker-compose.yml` under the web service:
```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
    reservations:
      memory: 512M
      cpus: '0.25'
```

### Monitoring

#### Health Checks
Both services include health checks. Monitor with:
```bash
docker-compose ps
```

#### Log Monitoring
Set up log rotation and monitoring:
```bash
# Configure Docker log rotation
sudo nano /etc/docker/daemon.json
```

Add:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

## Backup and Recovery

### Automated Backup Script
```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/var/backups/k9-operations"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
docker-compose exec -T db pg_dump -U k9user k9operations > $BACKUP_DIR/db_$DATE.sql

# Uploads backup
docker run --rm -v k9-operations_uploads_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/uploads_$DATE.tar.gz -C /data .

# Keep only last 7 backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### Recovery Process
```bash
# Stop services
docker-compose down

# Restore database
docker-compose up -d db
sleep 10
cat backup.sql | docker-compose exec -T db psql -U k9user k9operations

# Restore uploads
docker run --rm -v k9-operations_uploads_data:/data -v /path/to/backup:/backup alpine tar xzf /backup/uploads_backup.tar.gz -C /data

# Start all services
docker-compose up -d
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check database status
   docker-compose exec db pg_isready -U k9user
   
   # Check environment variables
   docker-compose exec web env | grep DATABASE_URL
   ```

2. **Permission Errors**
   ```bash
   # Fix upload directory permissions
   docker-compose exec web chown -R k9user:k9user /app/uploads
   ```

3. **Memory Issues**
   ```bash
   # Reduce Gunicorn workers
   echo "GUNICORN_WORKERS=2" >> .env
   docker-compose restart web
   ```

4. **SSL Certificate Issues**
   ```bash
   # Renew Let's Encrypt certificates
   sudo certbot renew --nginx
   ```

### Performance Tuning

1. **Database Performance**
   - Add database indices for frequently queried fields
   - Configure PostgreSQL memory settings
   - Enable query logging for slow queries

2. **Application Performance**
   - Adjust Gunicorn worker count based on CPU cores
   - Enable Nginx caching for static files
   - Consider Redis for session storage in multi-instance deployments

3. **Monitoring Setup**
   - Use Prometheus + Grafana for metrics
   - Set up log aggregation with ELK stack
   - Configure alerting for critical errors

## Maintenance

### Regular Tasks
- Weekly database backups
- Monthly security updates
- Quarterly certificate renewal checks
- Monitor disk space and logs

### Updates
```bash
# Pull latest images
docker-compose pull

# Recreate containers
docker-compose up -d --force-recreate

# Clean up old images
docker image prune -f
```

## Support

For deployment issues or questions:
1. Check the application logs: `docker-compose logs web`
2. Verify environment configuration
3. Ensure all prerequisites are met
4. Review the troubleshooting section above

## Security Checklist

- [ ] Changed default database password
- [ ] Generated secure SESSION_SECRET
- [ ] Configured firewall rules
- [ ] Set up SSL certificates
- [ ] Created admin user with strong password
- [ ] Configured automated backups
- [ ] Set up log monitoring
- [ ] Applied security headers in Nginx
- [ ] Restricted database access
- [ ] Enabled Docker security options