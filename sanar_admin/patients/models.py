from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from hopitaux.models import Hopital  # ← nouvel import

class Patient(models.Model):
    GROUPE_SANGUIN_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20)
    date_naissance = models.DateField()
    adresse = models.CharField(max_length=200)
    groupe_sanguin = models.CharField(max_length=3, choices=GROUPE_SANGUIN_CHOICES, default='O+')
    allergies = models.TextField(blank=True, default='Aucune')
    poids = models.FloatField(null=True, blank=True, default=0)
    taille = models.FloatField(null=True, blank=True, default=0)
    patient_id = models.CharField(max_length=20, unique=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    est_critique = models.BooleanField(default=False)
    hopital = models.ForeignKey(               # ← nouveau champ
        Hopital,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patients'
    )

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    class Meta:
        verbose_name = 'Patient'
        ordering = ['-date_inscription']

@receiver(post_save, sender=Patient)
def creer_dossier_medical(sender, instance, created, **kwargs):
    if created:
        from dossiers_medicaux.models import DossierMedical
        DossierMedical.objects.get_or_create(patient=instance)