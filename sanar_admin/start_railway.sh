#!/bin/bash
# ─── start_railway.sh — Démarre gunicorn avec PORT Railway dynamique ───
# Railway injecte $PORT mais ne le résout pas dans railway.json startCommand
# Ce script shell résout $PORT correctement

set -e

echo "=== Sanar Railway startup ==="
echo "PORT=${PORT:-8080}"
echo "DATABASE_URL=${DATABASE_URL:+set}"
echo "REDIS_URL=${REDIS_URL:+set}"

cd /app 2>/dev/null || cd sanar_admin

# Lancer gunicorn sur le PORT Railway (résolu par bash)
exec gunicorn \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    sanar_admin.wsgi:application
