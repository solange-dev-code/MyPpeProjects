from django.db import models
from patients.models import Patient
from consultations.models import Consultation
from medecins.models import Medecin

class DossierMedical(models.Model):
    STATUT_CHOICES = [
        ('valide', 'Validé'),
        ('en_attente', 'En attente'),
        ('urgent', 'Urgent'),
    ]

    patient = models.OneToOneField(Patient, on_delete=models.CASCADE)
    medecin_referent = models.ForeignKey(
        Medecin, on_delete=models.SET_NULL, null=True, blank=True
    )
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='en_attente'
    )
    antecedents = models.TextField(blank=True)
    traitements_en_cours = models.TextField(blank=True)
    notes_medicales = models.TextField(blank=True)
    nb_documents = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dossier - {self.patient}"

    class Meta:
        ordering = ['-updated_at']

class Prescription(models.Model):
    dossier = models.ForeignKey(
        DossierMedical, on_delete=models.CASCADE, related_name='prescriptions'
    )
    consultation = models.ForeignKey(
        Consultation, on_delete=models.SET_NULL, null=True, blank=True
    )
    medicament = models.CharField(max_length=200)
    posologie = models.CharField(max_length=200)
    duree = models.CharField(max_length=100)
    date_prescription = models.DateField(auto_now_add=True)
    est_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.medicament} - {self.dossier.patient}"

class Document(models.Model):
    TYPE_CHOICES = [
        ('ordonnance', 'Ordonnance'),
        ('analyse', 'Résultat d\'analyse'),
        ('imagerie', 'Imagerie (Radio/IRM)'),
        ('compte_rendu', 'Compte-rendu'),
        ('autre', 'Autre'),
    ]

    dossier = models.ForeignKey(
        DossierMedical, on_delete=models.CASCADE, related_name='documents'
    )
    titre = models.CharField(max_length=200)
    type_document = models.CharField(max_length=20, choices=TYPE_CHOICES)
    fichier = models.FileField(upload_to='dossiers/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titre} - {self.dossier.patient}"