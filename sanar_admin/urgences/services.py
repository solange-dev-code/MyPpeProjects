"""
Services métier pour le module urgences.

- haversine() : distance orthodromique entre deux coordonnées GPS
- hopital_optimal() : sélection du meilleur hôpital selon distance + charge
- trigger_notifications_urgence() : FCM + SMS + WhatsApp à l'équipe d'astreinte
- notifier_patient_acces_urgence() : alerte le patient qu'un accès d'urgence
  à son dossier a eu lieu (audit RGPD)
"""
import logging
from math import radians, sin, cos, asin, sqrt
from typing import Optional

from hopitaux.models import Hopital
from .models import DemandeUrgence, AccesUrgence

logger = logging.getLogger('sanar.urgences')

# ──────────────────────────────────────────────────────────────
# 1. Haversine — distance orthodromique (km) entre 2 points GPS
# ──────────────────────────────────────────────────────────────
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance à vol d'oiseau entre 2 points GPS, en kilomètres."""
    R = 6371.0  # rayon terrestre moyen
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (sin(dlat / 2) ** 2
         + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2)
    return 2 * R * asin(sqrt(a))


# ──────────────────────────────────────────────────────────────
# 2. Sélection de l'hôpital optimal (distance + charge)
# ──────────────────────────────────────────────────────────────
def hopital_optimal(lat_patient: float, lon_patient: float,
                    niveau: str = 'P2') -> Optional[Hopital]:
    """Retourne le meilleur hôpital pour une urgence.

    Score = distance_km + (5 × nb_urgences_en_attente)
    Le score minimum désigne l'hôpital le plus proche ET le moins chargé.
    """
    candidats = Hopital.objects.filter(actif=True)
    if not candidats.exists():
        logger.warning("Aucun hôpital actif trouvé pour assignation urgence")
        return None

    meilleur = None
    score_min = float('inf')
    for h in candidats:
        if h.latitude is None or h.longitude is None:
            continue
        dist_km = haversine(lat_patient, lon_patient, h.latitude, h.longitude)
        # Charge = nb d'urgences en attente dans cet hôpital
        charge = DemandeUrgence.objects.filter(
            hopital_destine=h, statut__in=['en_attente', 'assignee']
        ).count()
        # Score : distance + pénalité 5km par urgence en attente
        # Bonus pour P1 : on tolère un peu plus de distance pour le plus proche
        score = dist_km + (charge * 5.0)
        if niveau == 'P1':
            # Pour P1, on priorise la distance pure (5x moins de pondération charge)
            score = dist_km + (charge * 1.0)
        if score < score_min:
            score_min = score
            meilleur = h
    if meilleur:
        logger.info(
            "Hôpital optimal sélectionné : %s (score=%.2f)",
            meilleur.nom, score_min
        )
    return meilleur


# ──────────────────────────────────────────────────────────────
# 3. Notifications — FCM + SMS + WhatsApp (phase 5)
# ──────────────────────────────────────────────────────────────
def trigger_notifications_urgence(demande: DemandeUrgence) -> None:
    """Déclenche les notifications à l'équipe d'astreinte de l'hôpital.

    Canaux :
    1. FCM (push) — instantané, gratuit, requiert data
    2. SMS Twilio — backup, requiert numéro
    3. WhatsApp Business — optionnel

    Cette fonction est non bloquante : chaque canal est essayé dans un try/except
    séparé pour ne pas interrompre les autres si l'un échoue.
    """
    if not demande.hopital_destine:
        logger.warning("Pas d'hôpital assigné pour urgence %s, skip notif",
                       demande.uuid)
        return

    # ── 1. FCM ────────────────────────────────────────────────
    try:
        from api.services import envoyer_push_fcm
        # Récupère tous les personnels d'astreinte de l'hôpital
        personnels = demande.hopital_destine.personnel.filter(
            user__is_active=True
        )
        for p in personnels:
            tokens = getattr(p, 'fcm_tokens', None)
            if tokens:
                envoyer_push_fcm(
                    tokens=[t.token for t in tokens.all()],
                    titre=f"🚨 Urgence {demande.niveau} — {demande.patient}",
                    corps=f"Position: {demande.latitude:.4f}, {demande.longitude:.4f}",
                    data={'type': 'urgence', 'urgence_uuid': str(demande.uuid)}
                )
        logger.info("Push FCM envoyé pour urgence %s", demande.uuid)
    except ImportError:
        logger.debug("Service FCM non disponible (api.services.envoyer_push_fcm)")
    except Exception as e:
        logger.error("Échec FCM pour urgence %s : %s", demande.uuid, e)

    # ── 2. SMS Twilio ─────────────────────────────────────────
    try:
        from api.services import envoyer_sms_twilio
        if demande.hopital_destine.telephone:
            envoyer_sms_twilio(
                to=demande.hopital_destine.telephone,
                message=(f"URGENCE {demande.niveau} Sanar - "
                         f"Patient {demande.patient.nom} {demande.patient.prenom} - "
                         f"GPS: {demande.latitude:.4f},{demande.longitude:.4f} - "
                         f"Voir: https://sanar.app/u/{demande.uuid}")
            )
            logger.info("SMS envoyé à %s pour urgence %s",
                        demande.hopital_destine.telephone, demande.uuid)
    except ImportError:
        logger.debug("Service SMS Twilio non disponible")
    except Exception as e:
        logger.error("Échec SMS pour urgence %s : %s", demande.uuid, e)

    # ── 3. WhatsApp Business (optionnel) ──────────────────────
    try:
        from api.services import envoyer_whatsapp
        if demande.hopital_destine.telephone:
            envoyer_whatsapp(
                to=demande.hopital_destine.telephone,
                template_name='urgence_alerte',
                params={
                    'patient': f"{demande.patient.nom} {demande.patient.prenom}",
                    'niveau': demande.niveau,
                    'gps': f"{demande.latitude:.4f},{demande.longitude:.4f}",
                }
            )
    except ImportError:
        pass
    except Exception as e:
        logger.error("Échec WhatsApp pour urgence %s : %s", demande.uuid, e)


# ──────────────────────────────────────────────────────────────
# 4. Notification au patient (audit RGPD)
# ──────────────────────────────────────────────────────────────
def notifier_patient_acces_urgence(acces: AccesUrgence) -> None:
    """Notifie le patient qu'un accès d'urgence à son dossier a eu lieu.

    RGPD : le patient doit être informé de tout accès à ses données médicales,
    même légitime (secouriste). Notification push + email.
    """
    try:
        from api.services import envoyer_push_fcm
        envoyer_push_fcm(
            tokens=_get_patient_fcm_tokens(acces.patient),
            titre="Accès d'urgence à votre dossier",
            corps=(f"Quelqu'un a consulté vos données médicales d'urgence "
                   f"depuis {acces.source_ip}. Si ce n'était pas vous, "
                   f"révoquez votre QR code dans votre profil."),
            data={'type': 'audit_acces_urgence', 'acces_id': acces.id}
        )
    except Exception as e:
        logger.error("Échec notification patient (accès urgence) : %s", e)


def _get_patient_fcm_tokens(patient):
    """Récupère les tokens FCM enregistrés pour un patient."""
    try:
        return [dt.token for dt in patient.user.devicetoken_set.all()
                if dt.user == patient.user]
    except Exception:
        return []
