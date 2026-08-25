#!/bin/bash
# ─────────────────────────────────────────────────────────────
# Celery beat — Sanar backend (Railway service)
# ─────────────────────────────────────────────────────────────
# Déclenche les tâches planifiées :
# - Rappels RDV J-1 (daily 18h00)
# - Rappels RDV H-2 (hourly)
# - Recalcul file d'attente (5 min)
# - Re-notif urgences en attente (10 min)
# - Nettoyage audits RGPD > 1 an (mensuel)
# - Ré-entraînement ML (dimanche 02h00)
#
# Railway : créer un service séparé avec
# startCommand = "bash sanar_admin/start_beat.sh"
# ─────────────────────────────────────────────────────────────

set -e

echo "=== Sanar Celery beat startup ==="
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

# Lancer le beat scheduler (1 process suffit)
echo "=== Starting Celery beat ==="
exec celery -A sanar_admin beat \
    --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler 2>/dev/null \
    || exec celery -A sanar_admin beat --loglevel=info
