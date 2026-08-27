from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from hopitaux.models import Hopital
from .encrypted_fields import EncryptedCharField, EncryptedTextField
import uuid
import hashlib


class Patient(models.Model):
    GROUPE_SANGUIN_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    # ── CHAMPS CHIFFRÉS au repos (AES-256 via Fernet) ──
    # Les données sensibles sont chiffrées en base de données.
    # L'admin d'hopital voit les données en clair (déchiffrées par Django),
    # mais si la base est compromise, les données sont illisibles sans la clé.
    nom = EncryptedCharField(max_length=100)
    prenom = EncryptedCharField(max_length=100)
    telephone = EncryptedCharField(max_length=20)
    adresse = EncryptedCharField(max_length=200, blank=True, default='')
    allergies = EncryptedTextField(blank=True, default='Aucune')

    # email reste en clair (pour login + recherche)
    email = models.EmailField(unique=True)
    date_naissance = models.DateField()
    groupe_sanguin = models.CharField(max_length=3, choices=GROUPE_SANGUIN_CHOICES, default='O+')
    poids = models.FloatField(null=True, blank=True, default=0)
    taille = models.FloatField(null=True, blank=True, default=0)
    patient_id = models.CharField(max_length=20, unique=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    est_critique = models.BooleanField(default=False)
    hopital = models.ForeignKey(
        Hopital,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='patients'
    )

    # ── HACHAGE pour audit d'intégrité ──
    hash_donnees = models.CharField(
        max_length=64, blank=True, default='',
        help_text="Hash SHA-256 des donnees sensibles (audit integrite)"
    )
    date_hachage = models.DateTimeField(null=True, blank=True)

    # ── Token d'urgence pour QR code médical ──
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

    def calculer_hash_donnees(self):
        """Hash SHA-256 des donnees sensibles pour audit d'integrite."""
        donnees = '|'.join([
            self.nom or '',
            self.prenom or '',
            self.email or '',
            self.telephone or '',
            self.date_naissance.isoformat() if self.date_naissance else '',
            self.groupe_sanguin or '',
            self.allergies or '',
        ])
        return hashlib.sha256(donnees.encode('utf-8')).hexdigest()

    def hacher_donnees(self):
        from django.utils import timezone
        self.hash_donnees = self.calculer_hash_donnees()
        self.date_hachage = timezone.now()
        self.save(update_fields=['hash_donnees', 'date_hachage'])
        return self.hash_donnees

    @property
    def integrite_verifiee(self):
        if not self.hash_donnees:
            return False
        return self.calculer_hash_donnees() == self.hash_donnees

    def regenerer_token_urgence(self):
        import uuid as _uuid
        self.token_urgence = _uuid.uuid4()
        self.save()
        return self.token_urgence

    def save(self, *args, **kwargs):
        self.hash_donnees = self.calculer_hash_donnees()
        from django.utils import timezone
        self.date_hachage = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Patient'
        ordering = ['-date_inscription']


@receiver(post_save, sender=Patient)
def creer_dossier_medical(sender, instance, created, **kwargs):
    if created:
        from dossiers_medicaux.models import DossierMedical
        DossierMedical.objects.get_or_create(patient=instance)
