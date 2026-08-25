from django.db import models
from patients.models import Patient
from appointments.models import RendezVous
from medecins.models import Medecin

class Consultation(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('reportee', 'Reportée'),
        ('annulee', 'Annulée'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    rendez_vous = models.OneToOneField(
        RendezVous, on_delete=models.SET_NULL, null=True, blank=True
    )
    consultation_id = models.CharField(max_length=20, unique=True, blank=True)
    date = models.DateField()
    heure = models.TimeField()
    motif = models.CharField(max_length=200)
    type_consultation = models.CharField(max_length=100, blank=True)
    diagnostic = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    cout = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='en_attente'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.consultation_id:
            count = Consultation.objects.count() + 1
            self.consultation_id = f"CONS-2026-{count:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.consultation_id} - {self.patient}"

    class Meta:
        ordering = ['-date', '-heure']