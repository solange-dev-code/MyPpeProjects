#!/bin/bash
# ─── start_simple.sh — Démarre uniquement gunicorn (mode démo rapide) ───
# Version simplifiée pour Railway : gunicorn uniquement
# Les autres services (Celery, Daphne) seront ajoutés après validation

set -e

echo "=== Sanar simple startup (gunicorn only) ==="
echo "PORT=${PORT:-8080}"
echo "DATABASE_URL=${DATABASE_URL:+set (hidden)}"
echo "REDIS_URL=${REDIS_URL:+set (hidden)}"

cd /app/sanar_admin 2>/dev/null || cd sanar_admin

# 1. Migrations
echo "=== Running migrations ==="
python manage.py migrate --noinput 2>&1 | tail -5

# 2. Collecte statiques
if [ ! -d "staticfiles" ] || [ -z "$(ls -A staticfiles 2>/dev/null)" ]; then
    echo "=== Collecting static files ==="
    python manage.py collectstatic --noinput 2>&1 | tail -3
fi

# 3. Super-user
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
" 2>&1 | tail -3
fi

# 4. Seed données démo
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

# 5. Lancer gunicorn en foreground
echo "=== Starting gunicorn on port ${PORT:-8080} ==="
exec gunicorn \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers 2 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    sanar_admin.wsgi:application
