"""
Planning Celery Beat — exécution planifiée des tâches automatisées.

Tâches planifiées :
- envoyer_rappels_rdv_j_minus_1 : tous les jours à 18h00
- envoyer_rappels_rdv_h_minus_2 : toutes les heures
- recalculer_estimations_file_attente : toutes les 5 minutes
- envoyer_notifications_urgences_en_attente : toutes les 10 minutes
- nettoyer_audits_anciens : 1er du mois à 03h00 (RGPD)
- reentrainer_modele_ml : tous les dimanches à 02h00
"""
from celery.schedules import crontab
from .celery import app

app.conf.beat_schedule = {
    # ─── Rappels RDV ───
    'rappels-rdv-j-minus-1': {
        'task': 'api.tasks.envoyer_rappels_rdv_j_minus_1',
        'schedule': crontab(hour=18, minute=0),
    },
    'rappels-rdv-h-minus-2': {
        'task': 'api.tasks.envoyer_rappels_rdv_h_minus_2',
        'schedule': crontab(minute=0),  # toutes les heures
    },

    # ─── File d'attente temps réel ───
    'recalculer-file-attente': {
        'task': 'api.tasks.recalculer_estimations_file_attente',
        'schedule': crontab(minute='*/5'),
    },

    # ─── Urgences ───
    'notifications-urgences-en-attente': {
        'task': 'api.tasks.envoyer_notifications_urgences_en_attente',
        'schedule': crontab(minute='*/10'),
    },

    # ─── RGPD — nettoyage audits > 1 an ───
    'nettoyer-audits-anciens': {
        'task': 'api.tasks.nettoyer_audits_anciens',
        'schedule': crontab(hour=3, minute=0, day_of_month=1),
    },

    # ─── ML — ré-entraînement hebdomadaire ───
    'reentrainer-modele-ml': {
        'task': 'api.tasks.reentrainer_modele_ml',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Dimanche
    },
}
