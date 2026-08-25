#!/bin/bash
# ─── start_minimal.sh — Démarre gunicorn SANS migrations ni seed ───
# Version minimale absolue pour debug Railway
# Les migrations seront faites via railway shell manuellement

set -e

echo "=== Sanar minimal startup ==="
echo "PORT=${PORT:-8080}"

cd /app 2>/dev/null || cd sanar_admin

# Lancer gunicorn directement (sans migrate, sans collectstatic, sans seed)
exec gunicorn \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    sanar_admin.wsgi:application
