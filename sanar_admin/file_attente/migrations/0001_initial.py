"""Migration initiale pour l'app file_attente."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('hopitaux', '0001_initial'),
        ('medecins', '0001_initial'),
        ('patients', '0003_patient_hopital'),
    ]

    operations = [
        migrations.CreateModel(
            name='FileAttente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('niveau_triage', models.IntegerField(choices=[(1, 'P1 — Critique (réanimation immédiate)'), (2, 'P2 — Urgent (< 15 min)'), (3, 'P3 — Moins urgent (< 60 min)'), (4, 'P4 — Standard (< 2 h)'), (5, 'P5 — Non urgent (< 4 h)')], default=4)),
                ('statut', models.CharField(choices=[('en_attente', 'En attente'), ('en_consultation', 'En consultation'), ('termine', 'Terminé'), ('abandonne', 'Abandonné')], default='en_attente', max_length=20)),
                ('motif', models.CharField(blank=True, default='', max_length=200)),
                ('arrivee_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('consultation_at', models.DateTimeField(blank=True, null=True)),
                ('fin_at', models.DateTimeField(blank=True, null=True)),
                ('temps_attente_estime', models.IntegerField(default=30)),
                ('hopital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='file_attente', to='hopitaux.hopital')),
                ('medecin', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='file_attente', to='medecins.medecin')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='file_attente', to='patients.patient')),
            ],
            options={
                'verbose_name': "File d'attente",
                'verbose_name_plural': "Files d'attente",
                'ordering': ['niveau_triage', 'arrivee_at'],
            },
        ),
        migrations.AddIndex(
            model_name='fileattente',
            index=models.Index(fields=['hopital', 'statut', 'niveau_triage'], name='file_attente_triage_idx'),
        ),
    ]
