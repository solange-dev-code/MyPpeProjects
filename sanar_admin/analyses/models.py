from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from patients.models import Patient


# ──────────────────────────────────────────────────────────────
# Catalogue des types d'analyses avec référentiel de normes
# ──────────────────────────────────────────────────────────────
class TypeAnalyse(models.Model):
    """Catalogue des types d'analyses avec valeurs normales par défaut.

    Exemples : glycémie (GLYC), NFS (NFS), kaliémie (K), créatinine (CREAT)...
    Les normes affinées par âge/sexe sont dans ReferenceAnalyse.
    """

    CATEGORIE_CHOICES = [
        ('biologie', 'Biologie'),
        ('hematologie', 'Hématologie'),
        ('biochimie', 'Biochimie'),
        ('immunologie', 'Immunologie'),
        ('coagulation', 'Coagulation'),
        ('microbiologie', 'Microbiologie'),
        ('bacteriologie', 'Bactériologie'),
        ('virologie', 'Virologie'),
        ('parasitologie', 'Parasitologie'),
        ('anatomopathologie', 'Anatomopathologie'),
        ('imagerie', 'Imagerie'),
        ('fonctionnelle', 'Exploration fonctionnelle'),
        ('autre', 'Autre'),
    ]

    code = models.CharField(
        max_length=20, unique=True,
        help_text="Code court normalisé, ex: GLYC, NFS, K, CREAT"
    )
    nom = models.CharField(max_length=200)
    categorie = models.CharField(max_length=50, choices=CATEGORIE_CHOICES)
    unite = models.CharField(max_length=20, help_text="Ex: g/L, mmol/L, UI/L")
    # Bornes normales par défaut (peuvent être affinées par ReferenceAnalyse)
    normale_basse_defaut = models.FloatField(
        null=True, blank=True, help_text="Borne basse de la normale"
    )
    normale_haute_defaut = models.FloatField(
        null=True, blank=True, help_text="Borne haute de la normale"
    )
    seuil_critique_basse = models.FloatField(
        null=True, blank=True,
        help_text="Sous ce seuil, déclenche une alerte critique immédiate"
    )
    seuil_critique_haute = models.FloatField(
        null=True, blank=True,
        help_text="Au-dessus de ce seuil, déclenche une alerte critique immédiate"
    )

    class Meta:
        verbose_name = "Type d'analyse"
        verbose_name_plural = "Types d'analyses"
        ordering = ['categorie', 'nom']

    def __str__(self):
        return f"{self.code} — {self.nom} ({self.unite})"


class ReferenceAnalyse(models.Model):
    """Normes affinées par âge et sexe.

    Plusieurs références peuvent exister pour un même TypeAnalyse :
    ex : hémoglobine → plage différente pour homme adulte, femme adulte,
    enfant, femme enceinte, personne âgée.
    """

    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
        ('U', 'Universel'),
    ]

    type_analyse = models.ForeignKey(
        TypeAnalyse, on_delete=models.CASCADE, related_name='references'
    )
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, default='U')
    age_min = models.IntegerField(default=0, help_text="En années")
    age_max = models.IntegerField(default=120)
    normale_basse = models.FloatField()
    normale_haute = models.FloatField()
    description = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        verbose_name = 'Référence analyse'
        verbose_name_plural = 'Références analyses'
        ordering = ['type_analyse', 'age_min']

    def __str__(self):
        return f"{self.type_analyse.code} [{self.sexe} {self.age_min}-{self.age_max}ans]"


# ──────────────────────────────────────────────────────────────
# Analyse principale (compatible avec le modèle existant)
# ──────────────────────────────────────────────────────────────
class Analyse(models.Model):
    """Analyse médicale prescrite à un patient.

    Compatible avec le modèle existant (champs originaux conservés),
    enrichi d'une relation optionnelle vers TypeAnalyse pour les analyses
    quantitatives structurées. Les résultats détaillés sont dans ResultatAnalyse.
    """

    TYPE_CHOICES = [
        ('sang', 'Analyse de sang'),
        ('radiographie', 'Radiographie'),
        ('covid', 'Test COVID-19'),
        ('urine', "Analyse d'urine"),
        ('autre', 'Autre'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('disponible', 'Disponible'),
        ('critique', 'Critique'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE,
                                related_name='analyses')
    type_analyse = models.CharField(max_length=50, choices=TYPE_CHOICES)
    # Lien optionnel vers le catalogue structuré (pour analyses quantitatives)
    type_catalogue = models.ForeignKey(
        TypeAnalyse, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='analyses', help_text="Type structuré (catalogue)"
    )
    laboratoire = models.CharField(max_length=200)
    date = models.DateField()
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='en_attente'
    )
    # Champs texte libre (compatibilité ascendante)
    resultat = models.TextField(blank=True, default='')
    conclusion = models.TextField(blank=True, default='')
    fichier_pdf = models.FileField(upload_to='analyses/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Alerte automatique si un résultat est critique
    est_critique = models.BooleanField(
        default=False, help_text="True si un résultat dépasse un seuil critique"
    )
    alerte_traitee = models.BooleanField(
        default=False, help_text="True si le médecin a accusé réception de l'alerte"
    )

    def __str__(self):
        return f"{self.patient} - {self.get_type_analyse_display()} - {self.date}"

    class Meta:
        ordering = ['-date']


class ResultatAnalyse(models.Model):
    """Une ligne de résultat au sein d'une analyse (NFS = 10 lignes).

    Le flag (H/L/N/C) est calculé automatiquement à la saisie en comparant
    la valeur aux bornes normales (référentiel par âge/sexe si disponible).
    """

    FLAG_CHOICES = [
        ('N', 'Normal'),
        ('H', 'Haut'),
        ('L', 'Bas'),
        ('C', 'Critique'),
    ]

    analyse = models.ForeignKey(
        Analyse, on_delete=models.CASCADE, related_name='resultats'
    )
    type_analyse = models.ForeignKey(
        TypeAnalyse, on_delete=models.PROTECT,
        help_text="Paramètre mesuré (ex: glycémie, hémoglobine)"
    )
    valeur = models.FloatField()
    unite = models.CharField(max_length=20)
    flag = models.CharField(
        max_length=1, choices=FLAG_CHOICES, default='N',
        help_text="Calculé automatiquement à la saisie"
    )
    valeur_normale_basse = models.FloatField(null=True, blank=True)
    valeur_normale_haute = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Résultat d\'analyse'
        verbose_name_plural = 'Résultats d\'analyse'
        ordering = ['analyse', 'type_analyse']

    def __str__(self):
        return f"{self.type_analyse.code}: {self.valeur} {self.unite} [{self.flag}]"

    def calculer_flag(self):
        """Calcule le flag (N/H/L/C) en fonction des seuils."""
        # Seuils critiques prioritaires
        if self.type_analyse.seuil_critique_haute is not None and \
           self.valeur >= self.type_analyse.seuil_critique_haute:
            return 'C'
        if self.type_analyse.seuil_critique_basse is not None and \
           self.valeur <= self.type_analyse.seuil_critique_basse:
            return 'C'
        # Bornes normales
        basse = self.valeur_normale_basse or self.type_analyse.normale_basse_defaut
        haute = self.valeur_normale_haute or self.type_analyse.normale_haute_defaut
        if basse is not None and self.valeur < basse:
            return 'L'
        if haute is not None and self.valeur > haute:
            return 'H'
        return 'N'

    def save(self, *args, **kwargs):
        """Recalcule le flag avant sauvegarde."""
        self.flag = self.calculer_flag()
        super().save(*args, **kwargs)
        # Si critique, marque l'analyse parente
        if self.flag == 'C' and not self.analyse.est_critique:
            self.analyse.est_critique = True
            self.analyse.statut = 'critique'
            self.analyse.save(update_fields=['est_critique', 'statut'])


# ──────────────────────────────────────────────────────────────
# Signal : alerte push au médecin quand une analyse devient critique
# ──────────────────────────────────────────────────────────────
@receiver(post_save, sender=ResultatAnalyse)
def alerter_medecin_valeur_critique(sender, instance, created, **kwargs):
    """Déclenche une notification push au médecin référent si une valeur
    critique est détectée. KPI : 100% détection valeurs critiques.
    """
    if not created:
        return
    if instance.flag != 'C':
        return

    try:
        from api.services import envoyer_push_fcm
        from api.models import DeviceToken
        from dossiers_medicaux.models import DossierMedical
        # Récupérer le médecin référent
        try:
            dossier = DossierMedical.objects.get(patient=instance.analyse.patient)
        except DossierMedical.DoesNotExist:
            return
        if not dossier.medecin_referent or not dossier.medecin_referent.user:
            return
        tokens = list(
            DeviceToken.objects.filter(
                user=dossier.medecin_referent.user
            ).values_list('token', flat=True)
        )
        if tokens:
            envoyer_push_fcm(
                tokens=tokens,
                titre="⚠️ Valeur critique détectée",
                corps=(f"{instance.type_analyse.code} = {instance.valeur} "
                       f"{instance.unite} pour {instance.analyse.patient}"),
                data={
                    'type': 'alerte_critique',
                    'analyse_id': instance.analyse_id,
                    'resultat_id': instance.id,
                }
            )
    except Exception:
        # Notification non bloquante
        pass
