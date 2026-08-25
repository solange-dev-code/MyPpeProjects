from django.db import models
from patients.models import Patient
from medecins.models import Medecin
from hopitaux.models import Hopital  # ← nouvel import

class RendezVous(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirme', 'Confirmé'),
        ('reporte', 'Reporté'),
        ('annule', 'Annulé'),
        ('termine', 'Terminé'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    hopital = models.ForeignKey(               # ← nouveau champ
        Hopital,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rendez_vous'
    )
    date = models.DateField()
    heure = models.TimeField()
    motif = models.CharField(max_length=200)
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='en_attente'
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # ── NOUVEAU : ID événement Google Calendar (sync bidirectionnelle) ──
    google_event_id = models.CharField(
        max_length=200, blank=True, default='',
        help_text="ID de l'événement correspondant dans Google Calendar"
    )

    def __str__(self):
        return f"{self.patient} - Dr. {self.medecin.nom} - {self.date}"

    class Meta:
        ordering = ['-date', '-heure']
        verbose_name = 'Rendez-vous'