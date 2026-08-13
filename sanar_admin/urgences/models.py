"""
Modèles du module urgences.

- DemandeUrgence : alerte déclenchée par le bouton SOS Flutter.
  Calcule automatiquement l'hôpital destinataire via le service Haversine.
- AccesUrgence : journal d'audit RGPD obligatoire pour tout accès au dossier
  médical d'urgence (endpoint public par QR code).
"""
import uuid

from django.db import models
from django.contrib.auth.models import User
from patients.models import Patient
from hopitaux.models import Hopital


class DemandeUrgence(models.Model):
    """Demande d'urgence déclenchée par le bouton SOS de l'app Flutter.

    Le patient saisit un niveau (P1/P2/P3) et sa position GPS est captée
    automatiquement. Le backend assigne l'hôpital optimal via la formule
    Haversine + charge en cours.
    """

    NIVEAU_CHOICES = [
        ('P1', 'Critique (arrêt cardiaque, traumatisme grave)'),
        ('P2', 'Urgent (douleur aiguë, fracture suspectée)'),
        ('P3', 'Modéré (consultation rapide requise)'),
    ]
    STATUT_CHOICES = [
        ('en_attente', 'En attente de prise en charge'),
        ('assignee', 'Ambulance/hôpital assigné'),
        ('en_route', 'Secours en route'),
        ('pris_en_charge', 'Patient pris en charge'),
        ('annulee', 'Annulée'),
    ]

    # Identifiant opaque exposé à l'API (jamais l'ID Django)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True,
                            db_index=True)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='urgences'
    )
    hopital_destine = models.ForeignKey(
        Hopital, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='urgences_recues'
    )
    niveau = models.CharField(max_length=2, choices=NIVEAU_CHOICES, default='P2')
    # Position GPS au déclenchement
    latitude = models.FloatField()
    longitude = models.FloatField()
    description = models.TextField(blank=True, default='')
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='en_attente'
    )
    assigne_a = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='urgences_assignees'
    )
    # Mesure de performance (KPI : < 30s déclenchement → prise en charge)
    temps_reponse = models.IntegerField(null=True, blank=True)  # secondes
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    pris_en_charge_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Demande d'urgence"
        verbose_name_plural = "Demandes d'urgence"
        indexes = [
            models.Index(fields=['statut', '-created_at']),
            models.Index(fields=['hopital_destine', 'statut']),
        ]

    def __str__(self):
        return f"Urgence {self.uuid} — {self.patient} — {self.niveau}"

    @property
    def duree_attente_seconds(self):
        """Durée entre déclenchement et prise en charge (None si non pris en charge)."""
        if self.pris_en_charge_at:
            return int((self.pris_en_charge_at - self.created_at).total_seconds())
        return None


class AccesUrgence(models.Model):
    """Journal d'audit RGPD obligatoire de tout accès au dossier d'urgence.

    Chaque appel à l'endpoint public /api/urgence/<token>/ crée une entrée
    ici, permettant au patient d'être notifié et au DPO d'auditer les accès.
    """

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='acces_urgence'
    )
    source_ip = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=500, blank=True, default='')
    referer = models.URLField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Accès d'urgence (audit)"
        verbose_name_plural = "Accès d'urgence (audit)"

    def __str__(self):
        return f"Accès urgence — {self.patient} — {self.created_at:%Y-%m-%d %H:%M} — {self.source_ip}"
