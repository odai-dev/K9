# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        gcc \
        python3-dev \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

# Create non-root user for security
RUN groupadd -r k9user && useradd -r -g k9user k9user \
    && chown -R k9user:k9user /app
USER k9user

# Expose port
EXPOSE 5000

# Copy and make entrypoint script executable
COPY --chown=k9user:k9user docker-entrypoint.sh /app/
USER root
RUN chmod +x /app/docker-entrypoint.sh
USER k9user

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]