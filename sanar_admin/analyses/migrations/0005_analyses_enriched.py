"""Migration pour enrichir l'app analyses : TypeAnalyse, ReferenceAnalyse, ResultatAnalyse."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analyses', '0004_remove_analyse_medecin'),
        ('patients', '0001_initial'),
    ]

    operations = [
        # Création TypeAnalyse (catalogue)
        migrations.CreateModel(
            name='TypeAnalyse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='Code court normalisé, ex: GLYC, NFS, K, CREAT', max_length=20, unique=True)),
                ('nom', models.CharField(max_length=200)),
                ('categorie', models.CharField(choices=[('biologie', 'Biologie'), ('hematologie', 'Hématologie'), ('biochimie', 'Biochimie'), ('immunologie', 'Immunologie'), ('coagulation', 'Coagulation'), ('microbiologie', 'Microbiologie'), ('bacteriologie', 'Bactériologie'), ('virologie', 'Virologie'), ('parasitologie', 'Parasitologie'), ('anatomopathologie', 'Anatomopathologie'), ('imagerie', 'Imagerie'), ('fonctionnelle', 'Exploration fonctionnelle'), ('autre', 'Autre')], max_length=50)),
                ('unite', models.CharField(help_text='Ex: g/L, mmol/L, UI/L', max_length=20)),
                ('normale_basse_defaut', models.FloatField(blank=True, help_text='Borne basse de la normale', null=True)),
                ('normale_haute_defaut', models.FloatField(blank=True, help_text='Borne haute de la normale', null=True)),
                ('seuil_critique_basse', models.FloatField(blank=True, help_text="Sous ce seuil, déclenche une alerte critique immédiate", null=True)),
                ('seuil_critique_haute', models.FloatField(blank=True, help_text="Au-dessus de ce seuil, déclenche une alerte critique immédiate", null=True)),
            ],
            options={
                'verbose_name': "Type d'analyse",
                'verbose_name_plural': "Types d'analyses",
                'ordering': ['categorie', 'nom'],
            },
        ),
        # Création ReferenceAnalyse
        migrations.CreateModel(
            name='ReferenceAnalyse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sexe', models.CharField(choices=[('M', 'Masculin'), ('F', 'Féminin'), ('U', 'Universel')], default='U', max_length=1)),
                ('age_min', models.IntegerField(default=0)),
                ('age_max', models.IntegerField(default=120)),
                ('normale_basse', models.FloatField()),
                ('normale_haute', models.FloatField()),
                ('description', models.CharField(blank=True, default='', max_length=200)),
                ('type_analyse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='references', to='analyses.typeanalyse')),
            ],
            options={
                'verbose_name': 'Référence analyse',
                'verbose_name_plural': 'Références analyses',
                'ordering': ['type_analyse', 'age_min'],
            },
        ),
        # Ajout champs sur Analyse
        migrations.AddField(
            model_name='analyse',
            name='est_critique',
            field=models.BooleanField(default=False, help_text='True si un résultat dépasse un seuil critique'),
        ),
        migrations.AddField(
            model_name='analyse',
            name='alerte_traitee',
            field=models.BooleanField(default=False, help_text="True si le médecin a accusé réception de l'alerte"),
        ),
        migrations.AddField(
            model_name='analyse',
            name='type_catalogue',
            field=models.ForeignKey(blank=True, help_text='Type structuré (catalogue)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='analyses', to='analyses.typeanalyse'),
        ),
        # Création ResultatAnalyse
        migrations.CreateModel(
            name='ResultatAnalyse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valeur', models.FloatField()),
                ('unite', models.CharField(max_length=20)),
                ('flag', models.CharField(choices=[('N', 'Normal'), ('H', 'Haut'), ('L', 'Bas'), ('C', 'Critique')], default='N', help_text='Calculé automatiquement à la saisie', max_length=1)),
                ('valeur_normale_basse', models.FloatField(blank=True, null=True)),
                ('valeur_normale_haute', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('analyse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resultats', to='analyses.analyse')),
                ('type_analyse', models.ForeignKey(help_text='Paramètre mesuré (ex: glycémie, hémoglobine)', on_delete=django.db.models.deletion.PROTECT, to='analyses.typeanalyse')),
            ],
            options={
                'verbose_name': "Résultat d'analyse",
                'verbose_name_plural': "Résultats d'analyse",
                'ordering': ['analyse', 'type_analyse'],
            },
        ),
    ]
