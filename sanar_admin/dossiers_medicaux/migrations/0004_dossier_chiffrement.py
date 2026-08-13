"""Migration pour chiffrer les champs sensibles du DossierMedical."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dossiers_medicaux', '0003_alter_dossiermedical_medecin_referent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dossiermedical',
            name='antecedents',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='dossiermedical',
            name='notes_medicales',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='dossiermedical',
            name='traitements_en_cours',
            field=models.TextField(blank=True, default=''),
        ),
    ]
