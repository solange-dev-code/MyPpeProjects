"""
Services pour l'API REST.

- envoyer_push_fcm() : notifications push via Firebase Cloud Messaging
- envoyer_sms_twilio() : SMS via Twilio (backup des push)
- envoyer_whatsapp() : WhatsApp Business API (optionnel)
- envoyer_sms_rappel_rdv() : rappel automatique J-1 d'un rendez-vous
"""
import logging
import requests
from typing import List, Optional
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('sanar.api.services')


# ──────────────────────────────────────────────────────────────
# 1. Firebase Cloud Messaging (push notifications)
# ──────────────────────────────────────────────────────────────
def envoyer_push_fcm(tokens: List[str], titre: str, corps: str,
                     data: dict = None) -> dict:
    """Envoie une notification push à une liste de tokens FCM.

    Utilise l'API HTTP v1 de Firebase via firebase-admin (préféré) ou
    l'ancienne API legacy (FCM_SERVER_KEY) en fallback.

    Retourne {'success': int, 'failure': int}.
    """
    if not tokens:
        return {'success': 0, 'failure': 0}

    # ── Tentative 1 : firebase-admin (préféré, plus moderne) ───
    try:
        import firebase_admin
        from firebase_admin import messaging

        # Initialise si pas déjà fait
        try:
            app = firebase_admin.get_app()
        except ValueError:
            if settings.FCM_PROJECT_ID:
                firebase_admin.initialize_app(options={
                    'projectId': settings.FCM_PROJECT_ID
                })
                app = firebase_admin.get_app()
            else:
                raise ImportError("FCM_PROJECT_ID not configured")

        message = messaging.MulticastMessage(
            tokens=tokens,
            notification=messaging.Notification(title=titre, body=corps),
            data=data or {}
        )
        response = messaging.send_each_for_multicast(message)
        logger.info("FCM (admin SDK) envoyé : %d succès / %d échecs",
                    response.success_count, response.failure_count)
        return {
            'success': response.success_count,
            'failure': response.failure_count
        }
    except ImportError:
        logger.debug("firebase-admin non installé, fallback HTTP legacy")
    except Exception as e:
        logger.warning("Échec firebase-admin : %s, fallback HTTP legacy", e)

    # ── Tentative 2 : HTTP legacy (FCM_SERVER_KEY) ─────────────
    if not settings.FCM_SERVER_KEY:
        logger.warning("FCM_SERVER_KEY non configuré, push impossible")
        return {'success': 0, 'failure': len(tokens)}

    try:
        url = 'https://fcm.googleapis.com/fcm/send'
        headers = {
            'Authorization': f'key={settings.FCM_SERVER_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'registration_ids': tokens,
            'notification': {'title': titre, 'body': corps},
            'data': data or {}
        }
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        result = response.json()
        success = result.get('success', 0)
        failure = result.get('failure', 0)
        logger.info("FCM (legacy) envoyé : %d succès / %d échecs",
                    success, failure)
        return {'success': success, 'failure': failure}
    except Exception as e:
        logger.error("Échec FCM legacy : %s", e)
        return {'success': 0, 'failure': len(tokens)}


# ──────────────────────────────────────────────────────────────
# 2. SMS via Twilio
# ──────────────────────────────────────────────────────────────
def envoyer_sms_twilio(to: str, message: str) -> bool:
    """Envoie un SMS via Twilio.

    Args:
        to: numéro au format international (ex: +22890123456)
        message: texte du SMS (max 160 chars pour 1 SMS)

    Returns True si envoyé, False sinon.
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.warning("Twilio non configuré, SMS non envoyé à %s", to)
        return False

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=message,
            from_=settings.TWILIO_FROM_NUMBER,
            to=to
        )
        logger.info("SMS envoyé à %s (SID: %s)", to, message.sid)
        return True
    except ImportError:
        logger.debug("twilio non installé")
        return False
    except Exception as e:
        logger.error("Échec SMS Twilio à %s : %s", to, e)
        return False


# ──────────────────────────────────────────────────────────────
# 3. WhatsApp Business API (optionnel)
# ──────────────────────────────────────────────────────────────
def envoyer_whatsapp(to: str, template_name: str, params: dict) -> bool:
    """Envoie un message WhatsApp Business via template.

    Nécessite une configuration préalable du template dans WhatsApp Business.
    """
    if not settings.WHATSAPP_API_TOKEN:
        logger.debug("WhatsApp non configuré")
        return False

    try:
        url = f"https://graph.facebook.com/v17.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            'Authorization': f'Bearer {settings.WHATSAPP_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        # Formatage des paramètres selon le template
        components = []
        if params:
            components.append({
                'type': 'body',
                'parameters': [
                    {'type': 'text', 'text': str(v)} for v in params.values()
                ]
            })
        payload = {
            'messaging_product': 'whatsapp',
            'to': to,
            'type': 'template',
            'template': {
                'name': template_name,
                'language': {'code': 'fr'},
                'components': components
            }
        }
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            logger.info("WhatsApp envoyé à %s", to)
            return True
        else:
            logger.error("Échec WhatsApp : %s", response.text)
            return False
    except Exception as e:
        logger.error("Échec WhatsApp : %s", e)
        return False


# ──────────────────────────────────────────────────────────────
# 4. Notifications métier automatisées
# ──────────────────────────────────────────────────────────────
def envoyer_rappel_rdv(rdv) -> bool:
    """Envoie un rappel de RDV au patient (push + SMS backup).

    À planifier via Celery (J-1 à 18h, H-2).
    """
    from api.models import DeviceToken
    from patients.models import Patient

    try:
        patient = rdv.patient
        message = (
            f"Rappel Sanar : RDV le {rdv.date.strftime('%d/%m')} a "
            f"{rdv.heure.strftime('%H:%M')} avec Dr. {rdv.medecin.nom} "
            f"a {rdv.hopital.nom if rdv.hopital else 'hopital'}."
        )

        # Push FCM (principal)
        tokens = list(
            DeviceToken.objects.filter(
                user=patient.user, is_active=True
            ).values_list('token', flat=True)
        )
        if tokens:
            envoyer_push_fcm(
                tokens=tokens,
                titre="Rappel de rendez-vous",
                corps=message,
                data={'type': 'rappel_rdv', 'rdv_id': rdv.id}
            )

        # SMS (backup) — si pas de tokens ou toujours
        if patient.telephone:
            envoyer_sms_twilio(patient.telephone, message)

        return True
    except Exception as e:
        logger.error("Échec rappel RDV %s : %s", rdv.id, e)
        return False
