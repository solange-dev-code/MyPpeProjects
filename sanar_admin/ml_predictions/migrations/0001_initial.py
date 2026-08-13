"""Migration initiale pour ml_predictions."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('patients', '0004_patient_urgence_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='MLModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(default='random_forest_analyses', max_length=100)),
                ('version', models.CharField(max_length=20, unique=True)),
                ('date_entrainement', models.DateTimeField(auto_now_add=True)),
                ('precision', models.FloatField()),
                ('rappel', models.FloatField()),
                ('auc', models.FloatField()),
                ('hyperparametres', models.JSONField(default=dict)),
                ('fichier_modele', models.FileField(blank=True, null=True, upload_to='ml_models/')),
                ('est_actif', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Modèle ML',
                'verbose_name_plural': 'Modèles ML',
                'ordering': ['-date_entrainement'],
            },
        ),
        migrations.CreateModel(
            name='MLPrediction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score_risque', models.FloatField(help_text='Score de risque normalisé entre 0 (sain) et 1 (à risque élevé)')),
                ('niveau_risque', models.CharField(choices=[('faible', 'Faible (< 0.3)'), ('modere', 'Modéré (0.3 - 0.6)'), ('eleve', 'Élevé (0.6 - 0.8)'), ('critique', 'Critique (> 0.8)')], max_length=10)),
                ('features_importantes', models.JSONField(default=dict)),
                ('analyses_utilisees', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modele', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='predictions', to='ml_predictions.mlmodel')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='predictions_ml', to='patients.patient')),
            ],
            options={
                'verbose_name': 'Prédiction ML',
                'verbose_name_plural': 'Prédictions ML',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='mlprediction',
            index=models.Index(fields=['patient', '-created_at'], name='mlpred_patient_date_idx'),
        ),
        migrations.AddIndex(
            model_name='mlprediction',
            index=models.Index(fields=['niveau_risque'], name='mlpred_niveau_idx'),
        ),
    ]
