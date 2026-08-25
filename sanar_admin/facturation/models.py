from django.db import models
from patients.models import Patient
from consultations.models import Consultation
from medecins.models import Medecin

class Facture(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('payee', 'Payée'),
        ('partiel', 'Partiel'),
        ('annulee', 'Annulée'),
    ]

    MOYEN_PAIEMENT_CHOICES = [
        ('moov', 'Moov Money (Flooz)'),
        ('mtn', 'MTN Mobile Money'),
        ('orange', 'Orange Money'),
        ('wave', 'Wave'),
        ('celtiis', 'Celtiis Cash'),
        ('carte', 'Carte bancaire'),
        ('especes', 'Espèces'),
        ('virement', 'Virement'),
        ('assurance', 'Assurance CNSS'),
    ]

    facture_id = models.CharField(max_length=20, unique=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin = models.ForeignKey(
        Medecin, on_delete=models.SET_NULL, null=True, blank=True
    )
    consultation = models.ForeignKey(
        Consultation, on_delete=models.SET_NULL, null=True, blank=True
    )
    description = models.CharField(max_length=200)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    part_patient = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    part_assurance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='en_attente'
    )
    moyen_paiement = models.CharField(
        max_length=20, choices=MOYEN_PAIEMENT_CHOICES, blank=True
    )
    date_facture = models.DateField(auto_now_add=True)
    date_paiement = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.facture_id:
            count = Facture.objects.count() + 1
            self.facture_id = f"FAC-2026-{count:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.facture_id} - {self.patient} - {self.montant_total} FCFA"

    class Meta:
        ordering = ['-date_facture']