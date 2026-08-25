"""
Modèles pour l'API.

- DeviceToken : tokens FCM (Firebase Cloud Messaging) pour notifications push
"""
import uuid
from django.db import models
from django.contrib.auth.models import User


class DeviceToken(models.Model):
    """Token d'appareil pour notifications push (Firebase Cloud Messaging).

    Un utilisateur peut avoir plusieurs tokens (plusieurs devices).
    Le token est enregistré à l'ouverture de l'app Flutter via /api/device-token/.
    """

    PLATFORM_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='device_tokens')
    token = models.CharField(max_length=500, db_index=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, default='android')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Token appareil (FCM)'
        verbose_name_plural = 'Tokens appareils (FCM)'
        unique_together = ('user', 'token')

    def __str__(self):
        return f"{self.user.username} [{self.platform}] — {self.token[:20]}..."
