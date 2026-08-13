"""
Tâches Celery pour Sanar.

Tâches automatisées :
- envoyer_rappels_rdv_j_minus_1 : rappel RDV la veille à 18h
- envoyer_rappels_rdv_h_minus_2 : rappel RDV 2h avant
- recalculer_estimations_file_attente : toutes les 5 min
- nettoyer_audits_anciens : mensuel (RGPD, > 1 an)
- reentrainer_modele_ml : hebdomadaire
"""
import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger('sanar.tasks')


@shared_task
def envoyer_rappels_rdv_j_minus_1():
    """Envoie un rappel J-1 à 18h pour tous les RDV du lendemain.

    Planification : Celery beat, tous les jours à 18h00.
    """
    from appointments.models import RendezVous
    from api.services import envoyer_rappel_rdv

    demain = (timezone.now() + timedelta(days=1)).date()
    rdvs = RendezVous.objects.filter(
        date=demain,
        statut__in=['en_attente', 'confirme']
    ).select_related('patient', 'medecin', 'hopital')

    count = 0
    for rdv in rdvs:
        try:
            envoyer_rappel_rdv(rdv)
            count += 1
        except Exception as e:
            logger.error("Rappel RDV %s échoué: %s", rdv.id, e)

    logger.info("Rappels J-1 envoyés à %d patients", count)
    return count


@shared_task
def envoyer_rappels_rdv_h_minus_2():
    """Envoie un rappel H-2 pour les RDV dans 2h."""
    from appointments.models import RendezVous
    from api.services import envoyer_rappel_rdv

    now = timezone.now()
    dans_2h = now + timedelta(hours=2)
    rdvs = RendezVous.objects.filter(
        date=now.date(),
        heure__hour=dans_2h.hour,
        statut__in=['en_attente', 'confirme']
    ).select_related('patient', 'medecin', 'hopital')

    count = 0
    for rdv in rdvs:
        try:
            envoyer_rappel_rdv(rdv)
            count += 1
        except Exception as e:
            logger.error("Rappel H-2 RDV %s échoué: %s", rdv.id, e)

    logger.info("Rappels H-2 envoyés à %d patients", count)
    return count


@shared_task
def recalculer_estimations_file_attente():
    """Recalcule les temps estimés pour toutes les files d'attente actives.

    Planification : toutes les 5 minutes.
    """
    from hopitaux.models import Hopital
    from file_attente.services import recalculer_estimations

    total = 0
    for hopital in Hopital.objects.filter(actif=True):
        n = recalculer_estimations(hopital.id)
        total += n

    logger.info("Estimations recalculées pour %d entrées", total)
    return total


@shared_task
def nettoyer_audits_anciens():
    """Nettoie les entrées d'audit de plus de 1 an (RGPD).

    Planification : mensuelle (1er du mois à 03h00).
    """
    from auditlog.models import LogEntry
    from urgences.models import AccesUrgence

    seuil = timezone.now() - timedelta(days=365)
    n1, _ = LogEntry.objects.filter(timestamp__lt=seuil).delete()
    n2, _ = AccesUrgence.objects.filter(created_at__lt=seuil).delete()

    logger.info("Audit nettoyé : %d LogEntry + %d AccesUrgence", n1, n2)
    return n1 + n2


@shared_task
def reentrainer_modele_ml():
    """Ré-entraîne le modèle ML hebdomadairement.

    Planification : tous les dimanches à 02h00.
    """
    from ml_predictions.services import entrainer_modele
    modele = entrainer_modele()
    if modele:
        logger.info("Modèle ML ré-entraîné : %s", modele.version)
        return modele.version
    logger.warning("Ré-entraînement ML échoué (données insuffisantes)")
    return None


@shared_task
def envoyer_notifications_urgences_en_attente():
    """Vérifie les urgences en attente > 5 min et notifie à nouveau.

    Planification : toutes les 10 minutes.
    """
    from urgences.models import DemandeUrgence
    from urgences.services import trigger_notifications_urgence

    seuil = timezone.now() - timedelta(minutes=5)
    urgences = DemandeUrgence.objects.filter(
        statut='en_attente',
        created_at__lt=seuil
    )

    count = 0
    for u in urgences:
        try:
            trigger_notifications_urgence(u)
            count += 1
        except Exception as e:
            logger.error("Re-notif urgence %s échouée: %s", u.uuid, e)

    logger.info("Re-notifications envoyées pour %d urgences", count)
    return count
