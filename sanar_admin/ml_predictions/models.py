"""
Modèles pour les prédictions ML.

- MLPrediction : prédiction de risque pour un patient (score 0-1)
- MLModel : version du modèle + métriques (précision, rappel)
"""
from django.db import models
from patients.models import Patient


class MLModel(models.Model):
    """Version d'un modèle ML entraîné.

    Permet de tracer l'évolution des performances et de faire du A/B testing
    entre versions.
    """

    nom = models.CharField(max_length=100, default='random_forest_analyses')
    version = models.CharField(max_length=20, unique=True)
    date_entrainement = models.DateTimeField(auto_now_add=True)
    # Métriques
    precision = models.FloatField()
    rappel = models.FloatField()
    auc = models.FloatField()
    # Hyperparamètres (JSON)
    hyperparametres = models.JSONField(default=dict)
    # Chemin vers le modèle pickle
    fichier_modele = models.FileField(upload_to='ml_models/', null=True, blank=True)
    est_actif = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Modèle ML'
        verbose_name_plural = 'Modèles ML'
        ordering = ['-date_entrainement']

    def __str__(self):
        return f"{self.nom} v{self.version} (AUC={self.auc:.3f})"


class MLPrediction(models.Model):
    """Prédiction de risque clinique pour un patient.

    Le score (0.0 à 1.0) indique la probabilité que le patient développe
    une complication dans les 30 prochains jours, basée sur l'historique
    de ses analyses.
    """

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='predictions_ml'
    )
    modele = models.ForeignKey(
        MLModel, on_delete=models.SET_NULL, null=True, related_name='predictions'
    )
    score_risque = models.FloatField(
        help_text="Score de risque normalisé entre 0 (sain) et 1 (à risque élevé)"
    )
    niveau_risque = models.CharField(
        max_length=10,
        choices=[
            ('faible', 'Faible (< 0.3)'),
            ('modere', 'Modéré (0.3 - 0.6)'),
            ('eleve', 'Élevé (0.6 - 0.8)'),
            ('critique', 'Critique (> 0.8)'),
        ]
    )
    # Top features (variables qui ont le plus contribué au score)
    features_importantes = models.JSONField(default=dict)
    # Référence aux analyses utilisées
    analyses_utilisees = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Prédiction ML'
        verbose_name_plural = 'Prédictions ML'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', '-created_at']),
            models.Index(fields=['niveau_risque']),
        ]

    def __str__(self):
        return f"{self.patient} — risque={self.score_risque:.2f} ({self.niveau_risque})"

    def calculer_niveau(self):
        """Calcule le niveau de risque à partir du score."""
        if self.score_risque < 0.3:
            return 'faible'
        elif self.score_risque < 0.6:
            return 'modere'
        elif self.score_risque < 0.8:
            return 'eleve'
        else:
            return 'critique'

    def save(self, *args, **kwargs):
        self.niveau_risque = self.calculer_niveau()
        super().save(*args, **kwargs)
