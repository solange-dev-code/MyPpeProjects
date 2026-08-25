# ─── Procfile (compatibilité Heroku/Railway buildpack) ───
# Nixpacks.toml a priorité sur Procfile dans Railway, mais ce fichier
# assure la compatibilité avec Heroku et les autres PaaS.

web: cd sanar_admin && bash start.sh
worker: cd sanar_admin && celery -A sanar_admin worker --loglevel=info --concurrency=2
beat: cd sanar_admin && celery -A sanar_admin beat --loglevel=info
daphne: cd sanar_admin && daphne -b 0.0.0.0 -p $PORT sanar_admin.asgi:application
release: cd sanar_admin && python manage.py migrate --noinput && python manage.py collectstatic --noinput
