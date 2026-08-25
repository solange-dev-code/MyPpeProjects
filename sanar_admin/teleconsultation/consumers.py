"""
Consumer Django Channels pour la signalisation WebRTC.

Protocole de signalisation :
1. Le médecin ou patient initie une session → POST /api/teleconsultation/
2. Les deux parties se connectent au WebSocket ws://host/ws/teleconsultation/<room_uuid>/
3. Messages échangés (JSON) :
   - {'type': 'offer', 'sdp': '...'} — appelant envoie l'offre
   - {'type': 'answer', 'sdp': '...'} — appelé répond
   - {'type': 'ice', 'candidate': '...'} — échange ICE candidates
   - {'type': 'hangup'} — fin d'appel
4. Une fois la connexion P2P établie, le média audio/vidéo transite directement
   entre les deux clients (chiffré DTLS-SRTP), sans passer par le serveur.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

logger = logging.getLogger('sanar.teleconsultation')


class TeleconsultationConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket pour signalisation WebRTC.

    Groupe par room_uuid — chaque room a 2 participants max (médecin + patient).
    """

    async def connect(self):
        self.room_uuid = self.scope['url_route']['kwargs']['room_uuid']
        self.room_group_name = f'teleconsult_{self.room_uuid}'

        # Vérifier que la room existe et que l'user est participant
        valid = await self._validate_participant()
        if not valid:
            await self.close(code=4001)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        logger.info("WebSocket connecté room=%s user=%s",
                    self.room_uuid, self.scope.get('user'))

        # Notifier le groupe qu'un participant a rejoint
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'participant_joined',
            'user_id': self.scope['user'].id if self.scope.get('user') else None,
        })

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'participant_left',
                'user_id': self.scope.get('user').id if self.scope.get('user') else None,
            })
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data):
        """Réception d'un message de signalisation WebRTC — broadcast au groupe."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'JSON invalide'
            }))
            return

        msg_type = data.get('type')
        if msg_type not in ('offer', 'answer', 'ice', 'hangup'):
            await self.send(text_data=json.dumps({
                'error': f'Type message inconnu: {msg_type}'
            }))
            return

        # Broadcast à tous les participants du groupe sauf l'expéditeur
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'webrtc_message',
            'message': data,
            'sender_channel': self.channel_name,
        })

        # Journalisation (async)
        await self._log_signaling(msg_type, data)

        # Si hangup → marquer téléconsultation terminée
        if msg_type == 'hangup':
            await self._terminate_teleconsultation()

    async def webrtc_message(self, event):
        """Handler pour les messages broadcastés par le groupe."""
        # Ne pas renvoyer à l'expéditeur
        if event['sender_channel'] == self.channel_name:
            return
        await self.send(text_data=json.dumps(event['message']))

    async def participant_joined(self, event):
        """Handler : un participant a rejoint."""
        await self.send(text_data=json.dumps({
            'type': 'participant_joined',
            'user_id': event['user_id'],
        }))

    async def participant_left(self, event):
        """Handler : un participant a quitté."""
        await self.send(text_data=json.dumps({
            'type': 'participant_left',
            'user_id': event['user_id'],
        }))

    # ─── Helpers DB (async) ───
    @database_sync_to_async
    def _validate_participant(self):
        """Vérifie que la room existe et que l'user est bien participant."""
        from .models import Teleconsultation
        from django.contrib.auth.models import User
        try:
            tc = Teleconsultation.objects.get(room_uuid=self.room_uuid)
        except (Teleconsultation.DoesNotExist, ValueError):
            return False
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            return False
        # Vérifier que l'user est soit le médecin, soit le patient
        if hasattr(user, 'medecin_profile') and user.medecin_profile == tc.medecin:
            return True
        try:
            if user.patient == tc.patient:
                return True
        except Exception:
            pass
        return False

    @database_sync_to_async
    def _log_signaling(self, msg_type, data):
        """Journalise le message de signalisation (audit/debug)."""
        from .models import Teleconsultation, WebRTCSignaling
        try:
            tc = Teleconsultation.objects.get(room_uuid=self.room_uuid)
            WebRTCSignaling.objects.create(
                teleconsultation=tc,
                expediteur=self.scope['user'],
                type_message=msg_type,
                contenu=json.dumps(data)[:1000],  # truncate
            )
        except Exception as e:
            logger.warning("Log signaling échec: %s", e)

    @database_sync_to_async
    def _terminate_teleconsultation(self):
        """Marque la téléconsultation comme terminée."""
        from .models import Teleconsultation
        try:
            tc = Teleconsultation.objects.get(room_uuid=self.room_uuid)
            if tc.statut == 'en_cours':
                tc.statut = 'terminee'
                tc.date_fin = timezone.now()
                if tc.date_debut:
                    tc.duree_secondes = int(
                        (tc.date_fin - tc.date_debut).total_seconds()
                    )
                tc.save()
        except Exception as e:
            logger.warning("Terminate teleconsult échec: %s", e)
