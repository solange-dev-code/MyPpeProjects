from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from hopitaux.models import Hopital
import uuid


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
    hopital = models.ForeignKey(
        Hopital,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patients'
    )

    # ── NOUVEAU : Token d'urgence pour QR code médical ──
    # UUID opaque encodé dans le QR code, permettant l'accès d'urgence au
    # dossier médical RESTREINT (groupe sanguin, allergies, médecin référent)
    # via l'endpoint public /api/urgence/<token>/ — voir app 'urgences'.
    # Le patient peut le révoquer / régénérer depuis son profil.
    token_urgence = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True,
        help_text="Token opaque pour l'accès d'urgence par QR code"
    )
    urgence_qr_actif = models.BooleanField(
        default=True,
        help_text="Si False, l'endpoint d'urgence refuse l'accès (révocation)"
    )

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    def regenerer_token_urgence(self):
        """Révoque l'ancien token et en génère un nouveau (en cas de fuite)."""
        import uuid as _uuid
        self.token_urgence = _uuid.uuid4()
        self.save()
        return self.token_urgence

    class Meta:
        verbose_name = 'Patient'
        ordering = ['-date_inscription']


@receiver(post_save, sender=Patient)
def creer_dossier_medical(sender, instance, created, **kwargs):
    if created:
        from dossiers_medicaux.models import DossierMedical
        DossierMedical.objects.get_or_create(patient=instance)
