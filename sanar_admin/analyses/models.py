from django.db import models
from patients.models import Patient
from medecins.models import Medecin

# Create your models here.
class Analyse(models.Model):
    TYPE_CHOICES = [
        ('sang', 'Analyse de sang'),
        ('radiographie', 'Radiographie'),
        ('covid', 'Test COVID-19'),
        ('urine', 'Analyse d\'urine'),
        ('autre', 'Autre'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('disponible', 'Disponible'),
        ('critique', 'Critique'),
    ]

  
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    type_analyse = models.CharField(max_length=50, choices=TYPE_CHOICES)
    laboratoire = models.CharField(max_length=200)
    date = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    resultat = models.TextField(blank=True)
    conclusion = models.TextField(blank=True)
    fichier_pdf = models.FileField(upload_to='analyses/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient} - {self.get_type_analyse_display()} - {self.date}"

    class Meta:
        ordering = ['-date']