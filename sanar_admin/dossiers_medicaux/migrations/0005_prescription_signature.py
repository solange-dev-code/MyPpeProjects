"""Migration pour ajouter les champs de signature électronique à Prescription."""
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('dossiers_medicaux', '0004_dossier_chiffrement'),
        migrations.swappable_dependency('auth.User'),
    ]

    operations = [
        migrations.AddField(
            model_name='prescription',
            name='signature_hash',
            field=models.CharField(
                blank=True, default='',
                help_text='Hash SHA-256 du contenu signe (signature electronique)',
                max_length=64
            ),
        ),
        migrations.AddField(
            model_name='prescription',
            name='signe_par',
            field=models.ForeignKey(
                blank=True, null=True,
                help_text='Medecin ayant signe electroniquement',
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='prescriptions_signees',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='prescription',
            name='date_signature',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
