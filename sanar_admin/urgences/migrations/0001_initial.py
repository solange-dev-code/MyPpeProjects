"""Migration initiale pour l'app urgences."""
from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('hopitaux', '0001_initial'),
        ('patients', '0003_patient_hopital'),
        migrations.swappable_dependency('auth.User'),
    ]

    operations = [
        migrations.CreateModel(
            name='DemandeUrgence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('niveau', models.CharField(choices=[('P1', 'Critique (arrêt cardiaque, traumatisme grave)'), ('P2', 'Urgent (douleur aiguë, fracture suspectée)'), ('P3', 'Modéré (consultation rapide requise)')], default='P2', max_length=2)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('description', models.TextField(blank=True, default='')),
                ('statut', models.CharField(choices=[('en_attente', 'En attente de prise en charge'), ('assignee', 'Ambulance/hôpital assigné'), ('en_route', 'Secours en route'), ('pris_en_charge', 'Patient pris en charge'), ('annulee', 'Annulée')], default='en_attente', max_length=20)),
                ('temps_reponse', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('pris_en_charge_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigne_a', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='urgences_assignees', to=settings.AUTH_USER_MODEL)),
                ('hopital_destine', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='urgences_recues', to='hopitaux.hopital')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='urgences', to='patients.patient')),
            ],
            options={
                'verbose_name': "Demande d'urgence",
                'verbose_name_plural': "Demandes d'urgence",
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AccesUrgence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_ip', models.GenericIPAddressField()),
                ('user_agent', models.CharField(blank=True, default='', max_length=500)),
                ('referer', models.URLField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='acces_urgence', to='patients.patient')),
            ],
            options={
                'verbose_name': "Accès d'urgence (audit)",
                'verbose_name_plural': "Accès d'urgence (audit)",
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='demandeurgence',
            index=models.Index(fields=['statut', '-created_at'], name='urgences_demande_statut_idx'),
        ),
        migrations.AddIndex(
            model_name='demandeurgence',
            index=models.Index(fields=['hopital_destine', 'statut'], name='urgences_demande_hopital_idx'),
        ),
    ]
