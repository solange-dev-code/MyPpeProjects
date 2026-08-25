"""
Modèles pour la téléconsultation WebRTC.

- Teleconsultation : session audio/vidéo chiffrée P2P
  Stocke l'UUID de salle, les participants, statut, horodatages
- WebRTCSignaling : messages de signalisation échangés (offre, réponse, ICE)
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from patients.models import Patient
from medecins.models import Medecin


class Teleconsultation(models.Model):
    """Session de téléconsultation WebRTC.

    Le protocole WebRTC établit une connexion P2P chiffrée (DTLS-SRTP) entre
    le médecin et le patient. Le serveur Django Channels sert uniquement de
    canal de signalisation (échange SDP offre/réponse + ICE candidates).
    Le média (audio/vidéo) ne transite PAS par le serveur.
    """

    STATUT_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
        ('echouee', 'Échouée (erreur technique)'),
    ]

    # UUID de salle — opaque, partagé entre médecin et patient
    room_uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='teleconsultations'
    )
    medecin = models.ForeignKey(
        Medecin, on_delete=models.CASCADE, related_name='teleconsultations'
    )
    initiateur = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='teleconsultations_initiees'
    )
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='planifiee'
    )
    # Chiffrement de bout en bout
    cle_e2e = models.CharField(
        max_length=64, blank=True, default='',
        help_text="Clé de chiffrement E2E partagée (générée côté client)"
    )
    # Horodatages pour KPI
    date_planifiee = models.DateTimeField()
    date_debut = models.DateTimeField(null=True, blank=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    # Qualité de service (feedback post-call)
    duree_secondes = models.IntegerField(null=True, blank=True)
    qualite_audio = models.IntegerField(null=True, blank=True,
                                         help_text="Note 1-5 (feedback patient)")
    qualite_video = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_planifiee']
        verbose_name = 'Téléconsultation'
        verbose_name_plural = 'Téléconsultations'
        indexes = [
            models.Index(fields=['medecin', '-date_planifiee']),
            models.Index(fields=['patient', '-date_planifiee']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return f"Teleconsult {self.room_uuid} — {self.patient} / Dr {self.medecin.nom}"

    @property
    def duree_reelle(self):
        """Durée réelle en secondes si terminée."""
        if self.date_debut and self.date_fin:
            return int((self.date_fin - self.date_debut).total_seconds())
        return None


class WebRTCSignaling(models.Model):
    """Journal des messages de signalisation WebRTC échangés.

    Utile pour debug et audit. Non indispensable au fonctionnement.
    """

    TYPE_CHOICES = [
        ('offer', 'SDP Offer'),
        ('answer', 'SDP Answer'),
        ('ice', 'ICE Candidate'),
        ('hangup', 'Hangup'),
    ]

    teleconsultation = models.ForeignKey(
        Teleconsultation, on_delete=models.CASCADE, related_name='signaling_logs'
    )
    expediteur = models.ForeignKey(User, on_delete=models.CASCADE)
    type_message = models.CharField(max_length=10, choices=TYPE_CHOICES)
    contenu = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Message signalisation WebRTC'
        verbose_name_plural = 'Messages signalisation WebRTC'

    def __str__(self):
        return f"{self.type_message} — {self.teleconsultation.room_uuid}"
