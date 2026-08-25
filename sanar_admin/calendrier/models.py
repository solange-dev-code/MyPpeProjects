from django.db import models
from django.contrib.auth.models import User
from patients.models import Patient
from appointments.models import Medecin

class Evenement(models.Model):
    TYPE_CHOICES = [
        ('rendez_vous', 'Rendez-Vous'),
        ('consultation', 'Consultation'),
        ('reunion', 'Réunion'),
        ('autre', 'Autre'),
    ]

    COULEUR_CHOICES = [
        ('blue', '#2563EB'),
        ('green', '#16A34A'),
        ('orange', '#D97706'),
        ('red', '#DC2626'),
        ('purple', '#9333EA'),
    ]

    titre = models.CharField(max_length=200)
    type_evenement = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='rendez_vous'
    )
    couleur = models.CharField(
        max_length=10, choices=COULEUR_CHOICES, default='blue'
    )
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField(null=True, blank=True)
    patient = models.ForeignKey(
        Patient, on_delete=models.SET_NULL, null=True, blank=True
    )
    medecin = models.ForeignKey(
        Medecin, on_delete=models.SET_NULL, null=True, blank=True
    )
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titre} - {self.date_debut}"

    class Meta:
        ordering = ['date_debut']