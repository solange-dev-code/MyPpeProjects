"""Migration initiale pour teleconsultation."""
from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('medecins', '0003_medecin_enriched'),
        ('patients', '0004_patient_urgence_fields'),
        migrations.swappable_dependency('auth.User'),
    ]

    operations = [
        migrations.CreateModel(
            name='Teleconsultation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('statut', models.CharField(choices=[('planifiee', 'Planifiée'), ('en_cours', 'En cours'), ('terminee', 'Terminée'), ('annulee', 'Annulée'), ('echouee', 'Échouée (erreur technique)')], default='planifiee', max_length=20)),
                ('cle_e2e', models.CharField(blank=True, default='', help_text='Clé de chiffrement E2E partagée (générée côté client)', max_length=64)),
                ('date_planifiee', models.DateTimeField()),
                ('date_debut', models.DateTimeField(blank=True, null=True)),
                ('date_fin', models.DateTimeField(blank=True, null=True)),
                ('duree_secondes', models.IntegerField(blank=True, null=True)),
                ('qualite_audio', models.IntegerField(blank=True, help_text='Note 1-5 (feedback patient)', null=True)),
                ('qualite_video', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('initiateur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='teleconsultations_initiees', to=settings.AUTH_USER_MODEL)),
                ('medecin', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teleconsultations', to='medecins.medecin')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teleconsultations', to='patients.patient')),
            ],
            options={
                'verbose_name': 'Téléconsultation',
                'verbose_name_plural': 'Téléconsultations',
                'ordering': ['-date_planifiee'],
            },
        ),
        migrations.CreateModel(
            name='WebRTCSignaling',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_message', models.CharField(choices=[('offer', 'SDP Offer'), ('answer', 'SDP Answer'), ('ice', 'ICE Candidate'), ('hangup', 'Hangup')], max_length=10)),
                ('contenu', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expediteur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('teleconsultation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='signaling_logs', to='teleconsultation.teleconsultation')),
            ],
            options={
                'verbose_name': 'Message signalisation WebRTC',
                'verbose_name_plural': 'Messages signalisation WebRTC',
                'ordering': ['created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='teleconsultation',
            index=models.Index(fields=['medecin', '-date_planifiee'], name='telecons_medecin_date_idx'),
        ),
        migrations.AddIndex(
            model_name='teleconsultation',
            index=models.Index(fields=['patient', '-date_planifiee'], name='telecons_patient_date_idx'),
        ),
        migrations.AddIndex(
            model_name='teleconsultation',
            index=models.Index(fields=['statut'], name='telecons_statut_idx'),
        ),
    ]
