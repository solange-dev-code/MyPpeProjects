"""
Service de synchronisation Google Calendar pour les médecins.

Permet à un médecin de connecter son compte Google et de synchroniser
ses rendez-vous Sanar vers Google Calendar (export) et les événements
bloquants Google vers Sanar (import — marqués comme indisponibilités).

Prérequis :
- pip install google-api-python-client google-auth-oauthlib
- Créer un projet Google Cloud + OAuth2 credentials
- Définir GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET dans .env
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('sanar.calendar')

# Credentials OAuth2 (à configurer dans Google Cloud Console)
GOOGLE_CLIENT_ID = getattr(settings, 'GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = getattr(settings, 'GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = getattr(
    settings, 'GOOGLE_REDIRECT_URI', 'https://sanar.app/api/calendar/callback/'
)
SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_oauth_url(medecin_id: int) -> str:
    """Génère l'URL d'autorisation OAuth2 pour le médecin."""
    if not GOOGLE_CLIENT_ID:
        return ''
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config(
        {
            'web': {
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'redirect_uris': [GOOGLE_REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )
    url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        state=str(medecin_id),  # pour identifier le médecin au callback
    )
    return url


def exchange_code(code: str, medecin_id: int) -> bool:
    """Échange le code d'autorisation contre un token d'accès + refresh.

    Stocke le token dans GoogleCalendarLink pour le médecin.
    """
    if not GOOGLE_CLIENT_ID:
        return False
    try:
        from google_auth_oauthlib.flow import Flow
        flow = Flow.from_client_config(
            {
                'web': {
                    'client_id': GOOGLE_CLIENT_ID,
                    'client_secret': GOOGLE_CLIENT_SECRET,
                    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                    'token_uri': 'https://oauth2.googleapis.com/token',
                    'redirect_uris': [GOOGLE_REDIRECT_URI],
                }
            },
            scopes=SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI,
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials

        from .models import GoogleCalendarLink
        from medecins.models import Medecin
        medecin = Medecin.objects.get(pk=medecin_id)
        link, _ = GoogleCalendarLink.objects.update_or_create(
            medecin=medecin,
            defaults={
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_expiry': timezone.now() + timedelta(
                    seconds=credentials.expiry.total_seconds() if credentials.expiry else 3600
                ),
                'calendar_id': 'primary',
                'sync_actif': True,
            }
        )
        logger.info("Google Calendar connecté pour Dr. %s", medecin.nom)
        return True
    except Exception as e:
        logger.error("Exchange OAuth Google échoué: %s", e)
        return False


def sync_rdv_vers_google(medecin_id: int) -> int:
    """Synchronise les RDV Sanar du médecin vers Google Calendar.

    Retourne le nombre d'événements créés/mis à jour.
    """
    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        from .models import GoogleCalendarLink
        from appointments.models import RendezVous
    except ImportError:
        logger.warning("google-api-python-client non installé")
        return 0

    try:
        link = GoogleCalendarLink.objects.get(medecin_id=medecin_id, sync_actif=True)
    except GoogleCalendarLink.DoesNotExist:
        return 0

    creds = Credentials(
        token=link.access_token,
        refresh_token=link.refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
    )
    service = build('calendar', 'v3', credentials=creds)

    count = 0
    rdvs = RendezVous.objects.filter(
        medecin_id=medecin_id,
        statut__in=['en_attente', 'confirme'],
        date__gte=timezone.now().date(),
    )
    for rdv in rdvs:
        debut = datetime.combine(rdv.date, rdv.heure)
        fin = debut + timedelta(minutes=30)
        event = {
            'summary': f'RDV Sanar — {rdv.patient.prenom} {rdv.patient.nom}',
            'description': f'Motif: {rdv.motif}',
            'start': {'dateTime': debut.isoformat(), 'timeZone': 'Africa/Lome'},
            'end': {'dateTime': fin.isoformat(), 'timeZone': 'Africa/Lome'},
        }
        try:
            # Si déjà un event_id stocké, on met à jour, sinon on crée
            if hasattr(rdv, 'google_event_id') and rdv.google_event_id:
                service.events().update(
                    calendarId=link.calendar_id,
                    eventId=rdv.google_event_id,
                    body=event
                ).execute()
            else:
                created = service.events().insert(
                    calendarId=link.calendar_id,
                    body=event
                ).execute()
                rdv.google_event_id = created['id']
                rdv.save(update_fields=['google_event_id'])
            count += 1
        except Exception as e:
            logger.error("Sync RDV %s vers Google échoué: %s", rdv.id, e)

    logger.info("Sync Google Calendar: %d RDV synchronisés pour Dr. %s",
                count, link.medecin.nom)
    return count
