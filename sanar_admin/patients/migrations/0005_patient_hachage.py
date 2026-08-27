"""Migration pour ajouter hash_donnees et date_hachage au Patient."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0004_patient_urgence_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='hash_donnees',
            field=models.CharField(
                blank=True, default='',
                help_text='Hash SHA-256 des donnees sensibles (audit integrite)',
                max_length=64
            ),
        ),
        migrations.AddField(
            model_name='patient',
            name='date_hachage',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
