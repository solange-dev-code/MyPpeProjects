"""
Configuration ASGI pour Django Channels (WebRTC signaling).

Permet la communication WebSocket temps réel pour :
- Signalisation WebRTC (offre/réponse/ICE candidates)
- Notifications temps réel (file d'attente, urgences)
- Chat médecin-patient en direct
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sanar_admin.settings')

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

from teleconsultation.consumers import TeleconsultationConsumer

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path('ws/teleconsultation/<uuid:room_uuid>/',
                 TeleconsultationConsumer.as_asgi()),
        ])
    ),
})
