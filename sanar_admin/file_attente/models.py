"""
Modèles pour la file d'attente temps réel.

Niveaux de triage inspirés du système canadien CTAS (Canadian Triage and
Acuity Scale), adaptés à 5 niveaux.
"""
from django.db import models
from patients.models import Patient
from medecins.models import Medecin
from hopitaux.models import Hopital


class FileAttente(models.Model):
    """Entrée dans la file d'attente d'un hôpital.

    Le triage utilise 5 niveaux (1 = critique, 5 = non urgent).
    L'ordre de passage est calculé par (niveau_triage, arrivee_at) via
    un algorithme de file prioritaire (cf. services.ordre_passage).
    """

    NIVEAU_TRIAGE = [
        (1, 'P1 — Critique (réanimation immédiate)'),
        (2, 'P2 — Urgent (< 15 min)'),
        (3, 'P3 — Moins urgent (< 60 min)'),
        (4, 'P4 — Standard (< 2 h)'),
        (5, 'P5 — Non urgent (< 4 h)'),
    ]
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_consultation', 'En consultation'),
        ('termine', 'Terminé'),
        ('abandonne', 'Abandonné'),
    ]

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='file_attente'
    )
    hopital = models.ForeignKey(
        Hopital, on_delete=models.CASCADE, related_name='file_attente'
    )
    medecin = models.ForeignKey(
        Medecin, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='file_attente'
    )
    niveau_triage = models.IntegerField(
        choices=NIVEAU_TRIAGE, default=4,
        help_text="Niveau de triage CTAS (1=critique, 5=non urgent)"
    )
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='en_attente'
    )
    motif = models.CharField(max_length=200, blank=True, default='')

    # Horodatages pour calcul KPI
    arrivee_at = models.DateTimeField(auto_now_add=True, db_index=True)
    consultation_at = models.DateTimeField(null=True, blank=True)
    fin_at = models.DateTimeField(null=True, blank=True)

    # Estimation (mise à jour périodiquement via tâche Celery)
    temps_attente_estime = models.IntegerField(
        default=30, help_text="Estimation en minutes, recalculée régulièrement"
    )

    class Meta:
        ordering = ['niveau_triage', 'arrivee_at']
        verbose_name = "File d'attente"
        verbose_name_plural = "Files d'attente"
        indexes = [
            models.Index(fields=['hopital', 'statut', 'niveau_triage']),
        ]

    def __str__(self):
        return f"P{self.niveau_triage} — {self.patient} — {self.hopital}"

    @property
    def duree_attente_reelle(self):
        """Durée réelle d'attente (en secondes) si entré en consultation."""
        if self.consultation_at:
            return int((self.consultation_at - self.arrivee_at).total_seconds())
        return None
