#!/bin/bash
# ─────────────────────────────────────────────────────────────
# Script de démarrage Railway pour Sanar backend
# ─────────────────────────────────────────────────────────────
# Railway fournit :
#   - $PORT (port HTTP à écouter, attribué dynamiquement)
#   - $DATABASE_URL (PostgreSQL managé Railway)
#   - $REDIS_URL (Redis managé Railway)
#
# Ce script :
#   1. Affiche les variables d'environnement critiques (sans valeurs secrètes)
#   2. Attend que PostgreSQL soit prêt (tcp wait)
#   3. Applique les migrations
#   4. Collecte les fichiers statiques
#   5. Crée un super-utilisateur automatique si DJANGO_SUPERUSER_* défini
#   6. Lance gunicorn en production (4 workers, bind sur $PORT)
# ─────────────────────────────────────────────────────────────

set -e

echo "=== Sanar Railway startup ==="
echo "PORT=$PORT"
echo "DJANGO_DEBUG=${DJANGO_DEBUG:-False}"
echo "DATABASE_URL=${DATABASE_URL:+set (hidden)}"
echo "REDIS_URL=${REDIS_URL:+set (hidden)}"

cd /app/sanar_admin 2>/dev/null || cd sanar_admin

# 1. Attendre que PostgreSQL soit prêt (utile au premier déploiement)
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

# 2. Migrations
echo "=== Running migrations ==="
python manage.py migrate --noinput

# 3. Collecte des fichiers statiques (si pas déjà fait au build)
if [ ! -d "staticfiles" ] || [ -z "$(ls -A staticfiles 2>/dev/null)" ]; then
    echo "=== Collecting static files ==="
    python manage.py collectstatic --noinput
fi

# 4. Création automatique d'un super-user (optionnel)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "=== Creating superuser ==="
    python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sanar_admin.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ['DJANGO_SUPERUSER_USERNAME']
email = os.environ['DJANGO_SUPERUSER_EMAIL']
password = os.environ['DJANGO_SUPERUSER_PASSWORD']
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser {username} created.')
else:
    print(f'Superuser {username} already exists.')
"
fi

# 5. Seed données de démo (optionnel, via DJANGO_SEED_DEMO=True)
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
        latitude=6.17, longitude=1.23, actif=True,
        telephone='+22890000000'
    )
    # Medecin
    u_m = User.objects.create_user('dr_demo', 'dr@demo.app', 'Medecin2026!')
    Medecin.objects.create(
        user=u_m, nom='Demo', prenom='Dr', specialite='generaliste',
        telephone='+22891000000', hopital=h
    )
    # Patients
    for i, (n, p) in enumerate([('Kossi', 'Afi'), ('Mansour', 'Bou'), ('Adjovi', 'Claire')]):
        u = User.objects.create_user(f'patient_{i}', f'p{i}@demo.app', 'Patient2026!')
        Patient.objects.create(
            user=u, nom=n, prenom=p, email=f'p{i}@demo.app',
            telephone=f'+22890{i}00000', date_naissance=date(1990+i, 1, 15),
            adresse='Lome', patient_id=f'DEMO{i:04d}', hopital=h
        )
    print('Demo data seeded successfully.')
PYEOF
fi

# 6. Lancement de gunicorn
echo "=== Starting gunicorn on port $PORT ==="
exec gunicorn \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    sanar_admin.wsgi:application
