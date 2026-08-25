# ─── Backend Django (sanar_admin) ───
FROM python:3.12-slim AS backend

# Dépendances système pour WeasyPrint, psycopg2, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copie requirements et installation
COPY sanar_admin/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY sanar_admin/ .

# Collecte des statics
RUN mkdir -p /app/staticfiles /app/media /app/logs

EXPOSE 8080

# Commande par défaut : gunicorn en production
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "sanar_admin.wsgi:application"]


# ─── Celery worker ───
FROM backend AS celery-worker
CMD ["celery", "-A", "sanar_admin", "worker", "--loglevel=info", "--concurrency=2"]


# ─── Celery beat (scheduler) ───
FROM backend AS celery-beat
CMD ["celery", "-A", "sanar_admin", "beat", "--loglevel=info"]
