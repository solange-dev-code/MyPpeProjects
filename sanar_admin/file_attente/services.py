"""
Services pour la file d'attente.

- ordre_passage() : tri par (niveau_triage, arrivee_at) — algorithme de file prioritaire
- estimer_temps_attente() : moyenne mobile sur les 20 dernières consultations
- marquer_en_consultation() : passe un patient en consultation et déclenche notif
- marrier_termine() : termine la consultation et met à jour les moyennes
"""
from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg
from typing import List

from .models import FileAttente


def ordre_passage(hopital_id: int) -> List[FileAttente]:
    """Retourne la file triée par (niveau_triage, arrivée).

    Algorithme : file prioritaire simple — les P1 passent en priorité absolue,
    puis P2, etc. Au sein d'un même niveau, FIFO (premier arrivé, premier servi).
    """
    return list(
        FileAttente.objects.filter(
            hopital_id=hopital_id, statut='en_attente'
        ).select_related('patient', 'medecin').order_by(
            'niveau_triage', 'arrivee_at'
        )
    )


def position_patient(file_entry: FileAttente) -> int:
    """Retourne la position (1-based) d'un patient dans la file de son hôpital."""
    ahead = FileAttente.objects.filter(
        hopital_id=file_entry.hopital_id,
        statut='en_attente',
        niveau_triage__lte=file_entry.niveau_triage,
        arrivee_at__lt=file_entry.arrivee_at,
    ).count()
    return ahead + 1


def estimer_temps_attente(hopital_id: int, niveau: int) -> int:
    """Estimation du temps d'attente en minutes.

    Calcul : moyenne mobile des 20 dernières consultations terminées de
    l'hôpital, multipliée par un coefficient dépendant du niveau de triage :
      P1 = 10% (passage quasi-immédiat)
      P2 = 30%
      P3 = 60%
      P4 = 100% (moyenne brute)
      P5 = 150% (attente prolongée)
    """
    coefficient = {1: 0.1, 2: 0.3, 3: 0.6, 4: 1.0, 5: 1.5}.get(niveau, 1.0)

    recentes = FileAttente.objects.filter(
        hopital_id=hopital_id,
        statut='termine',
        consultation_at__isnull=False,
    ).order_by('-fin_at')[:20]

    if not recentes.exists():
        # Valeur par défaut : 30 min
        return max(1, int(30 * coefficient))

    total = timedelta(0)
    count = 0
    for f in recentes:
        if f.consultation_at and f.arrivee_at:
            total += (f.consultation_at - f.arrivee_at)
            count += 1
    if count == 0:
        return max(1, int(30 * coefficient))

    moyenne = total.total_seconds() / count  # secondes
    minutes = (moyenne / 60.0) * coefficient
    return max(1, int(minutes))


def marquer_en_consultation(file_id: int, medecin_id: int = None) -> FileAttente:
    """Passe une entrée de file en consultation.

    Déclenche une notification push au patient (via api.services).
    """
    f = FileAttente.objects.get(pk=file_id)
    f.statut = 'en_consultation'
    f.consultation_at = timezone.now()
    if medecin_id:
        f.medecin_id = medecin_id
    f.save()

    # Notifier le patient
    try:
        from api.services import envoyer_push_fcm
        from api.models import DeviceToken
        tokens = list(
            DeviceToken.objects.filter(
                user=f.patient.user
            ).values_list('token', flat=True)
        )
        if tokens:
            envoyer_push_fcm(
                tokens=tokens,
                titre="Votre tour approche",
                corps=f"Présentez-vous en salle de consultation.",
                data={'type': 'tour_patient', 'file_id': f.id}
            )
    except Exception:
        # La notification est non bloquante
        pass

    return f


def marquer_termine(file_id: int) -> FileAttente:
    """Termine une consultation."""
    f = FileAttente.objects.get(pk=file_id)
    f.statut = 'termine'
    f.fin_at = timezone.now()
    f.save()
    return f


def marquer_abandonne(file_id: int) -> FileAttente:
    """Marque un patient comme ayant abandonné la file."""
    f = FileAttente.objects.get(pk=file_id)
    f.statut = 'abandonne'
    f.fin_at = timezone.now()
    f.save()
    return f


def recalculer_estimations(hopital_id: int) -> int:
    """Recalcule le temps estimé pour toutes les entrées en attente d'un hôpital.

    À appeler périodiquement (tâche Celery toutes les 5 min).
    Retourne le nombre d'entrées mises à jour.
    """
    en_attente = FileAttente.objects.filter(
        hopital_id=hopital_id, statut='en_attente'
    )
    count = 0
    for entry in en_attente:
        nouvel_estime = estimer_temps_attente(hopital_id, entry.niveau_triage)
        if nouvel_estime != entry.temps_attente_estime:
            entry.temps_attente_estime = nouvel_estime
            entry.save(update_fields=['temps_attente_estime'])
            count += 1
    return count
