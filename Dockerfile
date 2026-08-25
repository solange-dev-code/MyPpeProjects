# ─── Dockerfile Railway — backend Django (simplifié) ───
FROM python:3.12-slim

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    shared-mime-info \
    fonts-liberation \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements + install
COPY sanar_admin/requirements-railway.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Code backend
COPY sanar_admin/ /app/

# Migrations + collectstatic au build (pas au runtime)
RUN cd /app && python manage.py collectstatic --noinput 2>/dev/null || true

# Dossiers
RUN mkdir -p /app/staticfiles /app/media /app/logs

EXPOSE 8080

# CMD : gunicorn direct avec $PORT résolu par bash
CMD ["bash", "-c", "cd /app && gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 120 --access-logfile - --error-logfile - sanar_admin.wsgi:application"]
