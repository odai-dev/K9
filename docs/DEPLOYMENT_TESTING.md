# K9 Operations Management System - Deployment Testing Guide

## Testing the Level 2 – Part D2 Components

This guide explains how to test the multi-stage Dockerfile, Nginx reverse proxy configuration, and SSL/TLS setup created for the K9 Operations Management System.

## Prerequisites for Testing

### System Requirements
- Docker 20.10+ and Docker Compose 2.0+
- 4GB RAM minimum (8GB recommended)
- Linux/macOS/Windows with WSL2
- OpenSSL for certificate generation

### Environment Setup
```bash
# Verify Docker installation
docker --version
docker-compose --version

# Clone repository and navigate to project
git clone <repository-url>
cd k9-operations
```

## Testing Multi-Stage Dockerfile

### 1. Build Multi-Stage Docker Image

```bash
# Build the multi-stage image (optimized for production)
docker build -f Dockerfile.multistage --target runtime -t k9-ops:multistage .

# Compare image sizes
docker images | grep k9-ops

# Expected results:
# k9-ops:multistage should be significantly smaller than regular build
# Runtime image should not include build dependencies
```

### 2. Verify Build Stages

```bash
# Build just the builder stage
docker build -f Dockerfile.multistage --target builder -t k9-ops:builder .

# Check that builder stage includes development tools
docker run --rm k9-ops:builder which gcc python3-dev

# Check that runtime stage excludes development tools
docker run --rm k9-ops:multistage which gcc || echo "gcc not found (expected)"
```

### 3. Test Runtime Image

```bash
# Run the multi-stage image
docker run -d --name k9-test \
  -e DATABASE_URL="sqlite:///test.db" \
  -e SESSION_SECRET="test-secret" \
  -p 5000:5000 \
  k9-ops:multistage

# Check if application starts successfully
docker logs k9-test

# Test health check
curl -f http://localhost:5000/ || echo "App not ready yet"

# Cleanup
docker stop k9-test && docker rm k9-test
```

## Testing Nginx Configuration

### 1. Generate SSL Certificates

```bash
# Generate self-signed certificates for testing
./scripts/ssl/generate-self-signed.sh localhost 30

# Verify certificates were created
ls -la nginx/ssl/
openssl x509 -in nginx/ssl/server.crt -text -noout | head -20
```

### 2. Start Production Stack

```bash
# Start the complete production stack
docker-compose -f docker-compose.production.yml up -d

# Check all services are running
docker-compose -f docker-compose.production.yml ps

# Expected services: db, web, nginx, redis (optional)
```

### 3. Test Nginx Proxy

```bash
# Test HTTP to HTTPS redirect
curl -I http://localhost

# Test HTTPS endpoint
curl -k -I https://localhost

# Test static file serving
curl -k -I https://localhost/static/css/style.css

# Test API proxying
curl -k -I https://localhost/api/dogs
```

### 4. Verify Security Headers

```bash
# Check security headers
curl -k -I https://localhost | grep -E "(X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security)"

# Expected headers:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# Strict-Transport-Security: max-age=63072000
```

### 5. Test Rate Limiting

```bash
# Test API rate limiting (should be limited after 10 requests)
for i in {1..15}; do
  echo "Request $i:"
  curl -k -s -o /dev/null -w "%{http_code}\n" https://localhost/api/dogs
  sleep 1
done

# Expected: First 10 requests return 401 (auth required), 
# then 429 (rate limited) for subsequent requests
```

## SSL/TLS Configuration Testing

### 1. SSL Certificate Validation

```bash
# Test SSL connection
openssl s_client -connect localhost:443 -servername localhost

# Check certificate details
echo | openssl s_client -connect localhost:443 2>/dev/null | openssl x509 -noout -text

# Verify cipher suites
nmap --script ssl-enum-ciphers -p 443 localhost
```

### 2. SSL Security Test

```bash
# Test SSL configuration with testssl.sh (if available)
# docker run --rm -ti drwetter/testssl.sh https://localhost

# Or use online tools like SSL Labs for production domains
# https://www.ssllabs.com/ssltest/
```

### 3. Test Different SSL Scenarios

```bash
# Test with curl (verbose SSL info)
curl -kvI https://localhost 2>&1 | grep -E "(SSL|TLS|cipher)"

# Test HSTS header
curl -k -I https://localhost | grep Strict-Transport-Security

# Test HTTP/2 support
curl -k --http2 -I https://localhost
```

## Performance Testing

### 1. Load Testing with Apache Bench

```bash
# Test application performance
ab -n 1000 -c 10 -k http://localhost:5000/

# Test with SSL
ab -n 1000 -c 10 -k https://localhost/
```

### 2. Container Resource Usage

```bash
# Monitor container resource usage
docker stats

# Check container logs for performance issues
docker-compose -f docker-compose.production.yml logs -f web
docker-compose -f docker-compose.production.yml logs -f nginx
```

### 3. Database Performance

```bash
# Test database connection
docker-compose -f docker-compose.production.yml exec web python -c "
from app import app, db
with app.app_context():
    print('Database connection:', db.engine.execute('SELECT 1').scalar())
"

# Monitor database logs
docker-compose -f docker-compose.production.yml logs -f db
```

## Integration Testing

### 1. End-to-End Application Test

```bash
# Test complete application flow
curl -k -c cookies.txt -X POST https://localhost/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Test authenticated API access
curl -k -b cookies.txt https://localhost/api/dogs

# Test file upload
curl -k -b cookies.txt -F "file=@test-image.jpg" https://localhost/api/upload
```

### 2. Backup and Restore Testing

```bash
# Test database backup
docker-compose -f docker-compose.production.yml exec backup ./backup.sh

# Verify backup files
ls -la backups/

# Test restore process (in test environment)
# docker-compose -f docker-compose.production.yml exec db pg_restore -U k9user -d k9operations /backups/latest.custom
```

## Health Checks and Monitoring

### 1. Application Health Checks

```bash
# Test application health endpoint
curl -k https://localhost/health

# Check Docker health status
docker inspect --format='{{.State.Health.Status}}' $(docker-compose -f docker-compose.production.yml ps -q web)
```

### 2. Log Analysis

```bash
# Application logs
docker-compose -f docker-compose.production.yml logs web | tail -50

# Nginx access logs
docker-compose -f docker-compose.production.yml logs nginx | grep "GET\|POST"

# Security events
docker-compose -f docker-compose.production.yml logs web | grep -i "security\|auth\|error"
```

### 3. Database Health

```bash
# Check database connectivity
docker-compose -f docker-compose.production.yml exec db pg_isready -U k9user

# Monitor database activity
docker-compose -f docker-compose.production.yml exec db psql -U k9user -d k9operations -c "
SELECT application_name, state, query 
FROM pg_stat_activity 
WHERE state = 'active';
"
```

## Security Testing

### 1. Vulnerability Scanning

```bash
# Scan Docker images for vulnerabilities (if trivy is available)
# trivy image k9-ops:multistage

# Check for common security issues
docker run --rm -v $(pwd):/app clair/clair:latest scan k9-ops:multistage
```

### 2. Configuration Security

```bash
# Check file permissions
docker-compose -f docker-compose.production.yml exec web ls -la /app/

# Verify no secrets in environment
docker-compose -f docker-compose.production.yml exec web env | grep -v PASSWORD

# Check nginx configuration
docker-compose -f docker-compose.production.yml exec nginx nginx -t
```

## Cleanup and Troubleshooting

### Cleanup Commands

```bash
# Stop all services
docker-compose -f docker-compose.production.yml down

# Remove volumes (WARNING: deletes data)
docker-compose -f docker-compose.production.yml down -v

# Remove images
docker rmi k9-ops:multistage k9-ops:builder

# Clean up SSL certificates
rm -rf nginx/ssl/server.*
```

### Common Issues and Solutions

**Issue: SSL certificate errors**
```bash
# Regenerate certificates
./scripts/ssl/generate-self-signed.sh localhost 365
docker-compose -f docker-compose.production.yml restart nginx
```

**Issue: Database connection errors**
```bash
# Check database logs
docker-compose -f docker-compose.production.yml logs db

# Recreate database
docker-compose -f docker-compose.production.yml down
docker volume rm k9-operations_db_data
docker-compose -f docker-compose.production.yml up -d
```

**Issue: Nginx configuration errors**
```bash
# Test nginx configuration
docker-compose -f docker-compose.production.yml exec nginx nginx -t

# Reload nginx
docker-compose -f docker-compose.production.yml exec nginx nginx -s reload
```

## Expected Test Results

### Successful Multi-Stage Build
- ✅ Builder image: ~1.5GB (includes build tools)
- ✅ Runtime image: ~800MB (production optimized)
- ✅ Application starts without errors
- ✅ All dependencies available in runtime

### Successful Nginx Configuration
- ✅ HTTP redirects to HTTPS (301 status)
- ✅ HTTPS responds with valid SSL
- ✅ Security headers present
- ✅ Static files served efficiently
- ✅ API requests proxied correctly

### Successful SSL/TLS Setup
- ✅ SSL certificate valid for domain
- ✅ Modern cipher suites enabled
- ✅ HSTS header present
- ✅ HTTP/2 support (if available)
- ✅ Rate limiting functional

## Production Deployment Checklist

Before deploying to production:

- [ ] Replace self-signed certificates with trusted CA certificates
- [ ] Update domain names in Nginx configuration
- [ ] Set strong passwords and secrets
- [ ] Configure log rotation and monitoring
- [ ] Set up automated backups
- [ ] Configure firewall rules
- [ ] Enable log aggregation
- [ ] Set up health monitoring alerts
- [ ] Review security settings
- [ ] Test disaster recovery procedures

---

This testing guide ensures all Level 2 – Part D2 components work correctly together and are production-ready.