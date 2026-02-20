FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Set working directory to Django project
WORKDIR /app/trading_system

# Collect static files (optional, if needed)
RUN python manage.py collectstatic --noinput 2>/dev/null || true

# Expose port (Railway sets PORT dynamically)
EXPOSE ${PORT:-8000}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/').read()" || exit 1

# Run migrations, create superuser, then start Daphne
CMD sh -c "python manage.py migrate && \
    python manage.py shell -c \"from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'falgund24@iitk.ac.in', 'admin123')\" && \
    daphne -b 0.0.0.0 -p ${PORT:-8000} trading_system.asgi:application"
