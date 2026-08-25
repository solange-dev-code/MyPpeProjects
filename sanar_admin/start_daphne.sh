#!/bin/bash
# ─────────────────────────────────────────────────────────────
# Daphne ASGI — Sanar backend (Railway service)
# ─────────────────────────────────────────────────────────────
# Serveur ASGI pour WebSockets Django Channels :
# - Signalisation WebRTC (teleconsultation audio/vidéo)
# - Notifications temps réel (file d'attente, urgences)
# - Chat médecin-patient en direct
#
# Railway : créer un service séparé avec
# startCommand = "bash sanar_admin/start_daphne.sh"
# Le service Daphne doit exposer le même PORT que le backend
# ou un PORT différent avec reverse proxy Nginx en front.
#
# En production, Daphne remplace gunicorn pour supporter à la fois
# HTTP et WebSocket sur le même port.
# ─────────────────────────────────────────────────────────────

set -e

echo "=== Sanar Daphne ASGI startup ==="
echo "PORT=${PORT:-8080}"
echo "REDIS_URL=${REDIS_URL:+set (hidden)}"

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

# Lancer Daphne (ASGI) sur le PORT Railway
# - websockets : pour téléconsultation
# - http : pour API REST (peut coexister avec gunicorn en mode proxy)
echo "=== Starting Daphne on port ${PORT:-8080} ==="
exec daphne -b 0.0.0.0 -p "${PORT:-8080}" \
    --access-log - \
    --proxy-headers \
    sanar_admin.asgi:application
