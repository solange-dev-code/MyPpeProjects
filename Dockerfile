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

# Migrations + collectstatic au build (avec clés temporaires)
ENV DJANGO_SECRET_KEY=build-temp-secret-key-not-for-production
ENV DJANGO_ENCRYPTION_KEY=dGVzdC1rZXktZm9yLWNpLW9ubHktbm90LXByb2R1Y3Rpb24=
ENV DJANGO_DEBUG=True
ENV DJANGO_ALLOWED_HOSTS=*
RUN cd /app && python manage.py collectstatic --noinput 2>/dev/null || true

# Dossiers
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Script de démarrage avec migrations + seed
COPY sanar_admin/start_railway.sh /app/start_railway.sh
RUN chmod +x /app/start_railway.sh

EXPOSE 8080

# Démarre via script (migrations + seed + gunicorn)
CMD ["bash", "/app/start_railway.sh"]
