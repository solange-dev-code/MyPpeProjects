#!/bin/bash
# ─────────────────────────────────────────────────────────────
# Celery worker — Sanar backend (Railway service)
# ─────────────────────────────────────────────────────────────
# Exécute les tâches asynchrones :
# - Envoi SMS Twilio + notifications push FCM
# - Génération exports PDF volumineux
# - Entraînement modèle ML
# - Notifications d'urgence à l'équipe d'astreinte
#
# Railway : créer un service séparé pointant vers le même repo
# avec startCommand = "bash sanar_admin/start_worker.sh"
# ─────────────────────────────────────────────────────────────

set -e

echo "=== Sanar Celery worker startup ==="
echo "REDIS_URL=${REDIS_URL:+set (hidden)}"
echo "DATABASE_URL=${DATABASE_URL:+set (hidden)}"

cd /app/sanar_admin 2>/dev/null || cd sanar_admin

# Attendre que PostgreSQL soit prêt
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for PostgreSQL..."
    for i in $(seq 1 30); do
        if python -c "
import dj_database_url, psycopg2
db = dj_database_url.parse('$DATABASE_URL')
conn = psycopg2.connect(host=db['HOST'], port=db['PORT'], user=db['USER'], password=db['PASSWORD'], dbname=db['NAME'])
conn.close()
" 2>/dev/null; then
            echo "PostgreSQL is ready."
            break
        fi
        echo "  Attempt $i/30 — waiting..."
        sleep 2
    done
fi

# Attendre que Redis soit prêt
if [ -n "$REDIS_URL" ]; then
    echo "Waiting for Redis..."
    for i in $(seq 1 30); do
        if python -c "
import redis, os
r = redis.Redis.from_url(os.environ['REDIS_URL'], socket_timeout=2)
r.ping()
" 2>/dev/null; then
            echo "Redis is ready."
            break
        fi
        echo "  Attempt $i/30 — waiting..."
        sleep 2
    done
fi

# Lancer le worker Celery (concurrency 2 = assez pour démo)
echo "=== Starting Celery worker ==="
exec celery -A sanar_admin worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=100 \
    --without-gossip \
    --without-mingle
