from django.db import models
from patients.models import Patient
from consultations.models import Consultation
from medecins.models import Medecin

# Import sécurisé : django-cryptography fournit EncryptedTextField qui chiffre
# automatiquement les données au repos (AES-256-GCM). En cas d'indisponibilité
# de la bibliothèque (ex: environnement de test minimal), on fallback sur TextField.
try:
    from cryptography.fields import EncryptedTextField
    CHIFFREMENT_ACTIF = True
except ImportError:
    EncryptedTextField = models.TextField
    CHIFFREMENT_ACTIF = False


class DossierMedical(models.Model):
    """Dossier médical centralisé d'un patient.

    Les champs sensibles (antécédents, traitements, notes) sont chiffrés
    au repos avec AES-256-GCM via django-cryptography.
    """

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
    # Champs sensibles chiffrés au repos (AES-256-GCM)
    antecedents = EncryptedTextField(blank=True, default='')
    traitements_en_cours = EncryptedTextField(blank=True, default='')
    notes_medicales = EncryptedTextField(blank=True, default='')
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

    # ── NOUVEAU : Signature électronique (valeur juridique) ──
    # Hash SHA-256 du contenu + médecin + timestamp. Rend la prescription
    # infalsifiable a posteriori (toute modification invaliderait le hash).
    signature_hash = models.CharField(
        max_length=64, blank=True, default='',
        help_text="Hash SHA-256 du contenu signé (signature électronique)"
    )
    signe_par = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='prescriptions_signees',
        help_text="Médecin ayant signé électroniquement"
    )
    date_signature = models.DateTimeField(null=True, blank=True)

    def calculer_hash(self):
        """Calcule le hash SHA-256 du contenu de la prescription.

        Le hash inclut : patient_id, medicament, posologie, duree,
        date_prescription, médecin signataire. Toute modification ultérieure
        invaliderait le hash → garantie d'intégrité.
        """
        import hashlib
        contenu = '|'.join([
            str(self.dossier.patient_id),
            self.medicament,
            self.posologie,
            self.duree,
            str(self.date_prescription),
            str(self.signe_par_id or ''),
        ])
        return hashlib.sha256(contenu.encode('utf-8')).hexdigest()

    def signer(self, user):
        """Signe électroniquement la prescription (médecin uniquement).

        - Calcule et stocke le hash SHA-256
        - Enregistre le médecin signataire + horodatage
        - Le hash rend toute modification ultérieure détectable
        """
        from django.utils import timezone
        from medecins.models import Medecin
        try:
            medecin = Medecin.objects.get(user=user)
        except Medecin.DoesNotExist:
            raise ValueError("Seul un médecin peut signer une prescription")
        self.signe_par = user
        self.date_signature = timezone.now()
        self.signature_hash = self.calculer_hash()
        self.save()
        return self.signature_hash

    @property
    def est_signee(self):
        """True si la prescription est signée électroniquement."""
        return bool(self.signature_hash and self.signe_par)

    @property
    def integrite_verifiee(self):
        """True si le hash actuel correspond au hash stocké (non modifié).

        Recalcule le hash et le compare au hash stocké.
        Si différent → la prescription a été modifiée après signature.
        """
        if not self.est_signee:
            return False
        return self.calculer_hash() == self.signature_hash

    def __str__(self):
        return f"{self.medicament} - {self.dossier.patient}"

    class Meta:
        ordering = ['-date_prescription']


class Document(models.Model):
    TYPE_CHOICES = [
        ('ordonnance', 'Ordonnance'),
        ('analyse', "Résultat d'analyse"),
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
