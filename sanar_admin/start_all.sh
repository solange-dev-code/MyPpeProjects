#!/bin/bash
# ─────────────────────────────────────────────────────────────
# start_all.sh — Démarre tous les services Sanar dans un seul
# conteneur Railway via supervisord (plan gratuit)
# ─────────────────────────────────────────────────────────────
# Lance : gunicorn + daphne + celery worker + celery beat
# Idéal pour : démo PPE, plan Railway gratuit, staging
# ─────────────────────────────────────────────────────────────

set -e

echo "=== Sanar all-in-one startup (supervisord) ==="
echo "PORT=${PORT:-8080} (API REST + admin)"
echo "PORT_WS=${PORT_WS:-8001} (WebSockets WebRTC)"
echo "DATABASE_URL=${DATABASE_URL:+set (hidden)}"
echo "REDIS_URL=${REDIS_URL:+set (hidden)}"

cd /app/sanar_admin 2>/dev/null || cd sanar_admin

# Définir PORT_WS si non défini (port Daphne pour WebSockets)
export PORT_WS=${PORT_WS:-8001}

# 1. Attendre que PostgreSQL soit prêt
if [ -n "$DATABASE_URL" ] && [[ "$DATABASE_URL" == postgres* ]]; then
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

# 2. Attendre que Redis soit prêt
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

# 3. Migrations (une seule fois, par le service principal)
echo "=== Running migrations ==="
python manage.py migrate --noinput

# 4. Collecte des fichiers statiques
if [ ! -d "staticfiles" ] || [ -z "$(ls -A staticfiles 2>/dev/null)" ]; then
    echo "=== Collecting static files ==="
    python manage.py collectstatic --noinput
fi

# 5. Création du super-user (optionnel)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "=== Creating superuser ==="
    python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sanar_admin.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
u = os.environ['DJANGO_SUPERUSER_USERNAME']
e = os.environ['DJANGO_SUPERUSER_EMAIL']
p = os.environ['DJANGO_SUPERUSER_PASSWORD']
if not User.objects.filter(username=u).exists():
    User.objects.create_superuser(username=u, email=e, password=p)
    print(f'Superuser {u} created.')
else:
    print(f'Superuser {u} already exists.')
"
fi

# 6. Seed données de démo (optionnel)
if [ "${DJANGO_SEED_DEMO:-False}" = "True" ]; then
    echo "=== Seeding demo data ==="
    python manage.py shell << 'PYEOF'
from patients.models import Patient
from medecins.models import Medecin
from hopitaux.models import Hopital
from django.contrib.auth.models import User
from datetime import date
if not Hopital.objects.exists():
    h = Hopital.objects.create(
        nom='CHU Demo', adresse='Lome', ville='Lome',
        latitude=6.17, longitude=1.23, actif=True, telephone='+22890000000'
    )
    u_m = User.objects.create_user('dr_demo', 'dr@demo.app', 'Medecin2026!')
    Medecin.objects.create(user=u_m, nom='Demo', prenom='Dr', specialite='generaliste', telephone='+22891000000', hopital=h)
    for i, (n, p) in enumerate([('Kossi', 'Afi'), ('Mansour', 'Bou'), ('Adjovi', 'Claire')]):
        u = User.objects.create_user(f'patient_{i}', f'p{i}@demo.app', 'Patient2026!')
        Patient.objects.create(user=u, nom=n, prenom=p, email=f'p{i}@demo.app', telephone=f'+22890{i}00000', date_naissance=date(1990+i, 1, 15), adresse='Lome', patient_id=f'DEMO{i:04d}', hopital=h)
    print('Demo data seeded.')
PYEOF
fi

# 7. Installer supervisord si absent
if ! command -v supervisord &> /dev/null; then
    echo "=== Installing supervisord ==="
    pip install supervisor
fi

# 8. Lancer supervisord (foreground, garde le conteneur en vie)
echo "=== Starting supervisord (4 processes) ==="
exec supervisord -c supervisord.conf
