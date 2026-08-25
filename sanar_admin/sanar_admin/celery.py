"""
Configuration Celery pour Sanar.

Celery est utilisé pour :
- Rappels de RDV automatiques (J-1 18h, H-2)
- Recalcul périodique des temps d'attente (toutes les 5 min)
- Envoi bulk de SMS/notifications push
- Génération asynchrone d'exports PDF volumineux
- Nettoyage des audits anciens (> 1 an, RGPD)
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sanar_admin.settings')

app = Celery('sanar_admin')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Chargement du beat schedule (planning des tâches automatisées)
# Le module celery_beat_schedule.py configure app.conf.beat_schedule directement
from . import celery_beat_schedule  # noqa: E402,F401


@app.task(bind=True)
def debug_task(self):
    """Tâche de test — affiche la requête."""
    print(f'Request: {self.request!r}')
