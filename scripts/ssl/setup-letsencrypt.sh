#!/bin/bash
# Set up Let's Encrypt SSL certificates for production
# Requires certbot to be installed

set -e

DOMAIN="${1}"
EMAIL="${2}"
WEBROOT="${3:-/var/www/certbot}"

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Usage: $0 <domain> <email> [webroot_path]"
    echo "Example: $0 k9ops.example.com admin@example.com"
    exit 1
fi

echo "Setting up Let's Encrypt SSL for domain: $DOMAIN"
echo "Contact email: $EMAIL"

# Create webroot directory
mkdir -p "$WEBROOT"

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y certbot
    elif command -v yum &> /dev/null; then
        sudo yum install -y certbot
    else
        echo "Please install certbot manually"
        exit 1
    fi
fi

# Generate certificate using webroot method
echo "Generating Let's Encrypt certificate..."
certbot certonly \
    --webroot \
    --webroot-path="$WEBROOT" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --domains "$DOMAIN"

# Copy certificates to nginx directory
CERT_DIR="nginx/ssl"
mkdir -p "$CERT_DIR"

cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$CERT_DIR/server.crt"
cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$CERT_DIR/server.key"

# Set proper permissions
chmod 600 "$CERT_DIR/server.key"
chmod 644 "$CERT_DIR/server.crt"

echo "Let's Encrypt certificate installed successfully!"
echo "Certificate: $CERT_DIR/server.crt"
echo "Private key: $CERT_DIR/server.key"
echo ""
echo "Add this to your crontab for automatic renewal:"
echo "0 12 * * * /usr/bin/certbot renew --quiet && docker-compose -f /path/to/docker-compose.production.yml restart nginx"