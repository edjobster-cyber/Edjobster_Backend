# Use Python 3.11 slim image for better performance
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=edjobster.settings

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    postgresql-client \
    gcc \
    g++ \
    libpq-dev \
    python3-dev \
    build-essential \
    curl \
    libssl-dev \
    libffi-dev \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI from official Docker repository
RUN install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && chmod a+r /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# # Create non-root user for security
# RUN useradd --create-home --shell /bin/bash app \
#     && chown -R app:app /app

# # Add Docker socket for Docker commands
# RUN usermod -aG docker app || true

# USER app
# --chown=app:app 

# Copy and install Python dependencies
COPY new_requirement.txt /app/
RUN pip install --no-cache-dir -r new_requirement.txt

# Add user's pip binaries to PATH
ENV PATH="/home/app/.local/bin:${PATH}"

# Copy project files
COPY --chown=app:app . /app/

# Create necessary directories
RUN mkdir -p /app/media /app/staticroot /app/static && chmod -R 755 /app/media /app/staticroot /app/static

# Collect static files (this will be done during deployment, but prepare the structure)
RUN python manage.py collectstatic --noinput --clear || true

# Run database migrations
RUN python manage.py makemigrations || true
RUN python manage.py migrate || true

# Expose port
EXPOSE 8000

# Persist media directory across restarts/deployments
VOLUME ["/app/media"]

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/admin/login/ || exit 1

# Default command: start Celery worker, Celery beat, then Gunicorn
CMD ["sh", "-c", "celery -A edjobster worker -l info --concurrency=2 & celery -A edjobster beat -l info & exec gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 edjobster.wsgi:application"]
