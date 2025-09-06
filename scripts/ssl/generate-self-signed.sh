#!/bin/bash
# Generate self-signed SSL certificates for development/testing
# For production, use certificates from a trusted CA like Let's Encrypt

set -e

CERT_DIR="nginx/ssl"
DOMAIN="${1:-localhost}"
DAYS="${2:-365}"

echo "Generating self-signed SSL certificate for domain: $DOMAIN"
echo "Valid for: $DAYS days"

# Create SSL directory if it doesn't exist
mkdir -p "$CERT_DIR"

# Generate private key
openssl genrsa -out "$CERT_DIR/server.key" 2048

# Generate certificate signing request
cat > "$CERT_DIR/server.conf" << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=SA
ST=Riyadh
L=Riyadh
O=K9 Operations
OU=IT Department
CN=$DOMAIN

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = *.$DOMAIN
DNS.3 = localhost
DNS.4 = 127.0.0.1
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# Generate certificate
openssl req -new -x509 -key "$CERT_DIR/server.key" -out "$CERT_DIR/server.crt" \
    -days "$DAYS" -config "$CERT_DIR/server.conf" -extensions v3_req

# Set proper permissions
chmod 600 "$CERT_DIR/server.key"
chmod 644 "$CERT_DIR/server.crt"

echo "SSL certificate generated successfully!"
echo "Certificate: $CERT_DIR/server.crt"
echo "Private key: $CERT_DIR/server.key"
echo ""
echo "To use with Docker Compose:"
echo "  docker-compose -f docker-compose.production.yml up -d"
echo ""
echo "WARNING: This is a self-signed certificate suitable only for development/testing."
echo "For production, use certificates from a trusted Certificate Authority."