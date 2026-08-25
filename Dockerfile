# ─── Dockerfile Railway — backend Django all-in-one ───
# Build optimisé pour Debian Trixie (python:3.12-slim)
# Lance gunicorn + daphne + celery worker + celery beat via supervisord

FROM python:3.12-slim

# Dépendances système minimales (paquets stables sur Debian Trixie)
# WeasyPrint nécessite pango + cairo + gdk-pixbuf
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
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copie requirements et installation (version allégée pour Railway)
COPY sanar_admin/requirements-railway.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copie du code backend
COPY sanar_admin/ /app/

# Scripts de démarrage — rendre exécutables
RUN chmod +x /app/start.sh /app/start_simple.sh /app/start_all.sh \
              /app/start_worker.sh /app/start_beat.sh /app/start_daphne.sh 2>/dev/null || true

# Préparation des dossiers
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Railway attribue dynamiquement le port via $PORT
ENV PORT=${PORT:-8080}
ENV PORT_WS=${PORT_WS:-8001}
EXPOSE 8080

# Pas de HEALTHCHECK Docker — Railway gère le healthcheck via railway.json
# (évite les faux négatifs pendant les migrations au démarrage)

# Démarre gunicorn (mode simple pour Railway)
CMD ["bash", "/app/start_simple.sh"]
