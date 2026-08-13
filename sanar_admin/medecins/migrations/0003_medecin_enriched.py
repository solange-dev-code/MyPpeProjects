"""Migration pour ajouter DisponibiliteMedecin, CongeMedecin, user et nouvelles spécialités."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hopitaux', '0001_initial'),
        ('medecins', '0002_medecin_hopital'),
        migrations.swappable_dependency('auth.User'),
    ]

    operations = [
        # Ajout du champ user sur Medecin (pour login + 2FA)
        migrations.AddField(
            model_name='medecin',
            name='user',
            field=models.OneToOneField(
                blank=True, null=True,
                help_text='Lien vers le compte Django (pour login + 2FA)',
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='medecin_profile',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Modification du champ specialite pour ajouter les nouvelles spécialités
        migrations.AlterField(
            model_name='medecin',
            name='specialite',
            field=models.CharField(choices=[
                ('cardiologue', 'Cardiologue'),
                ('generaliste', 'Généraliste'),
                ('dermatologue', 'Dermatologue'),
                ('gynecologue', 'Gynécologue'),
                ('neurologue', 'Neurologue'),
                ('ophtalmologue', 'Ophtalmologue'),
                ('pediatre', 'Pédiatre'),
                ('radiologue', 'Radiologue'),
                ('anesthesiste', 'Anesthésiste'),
                ('chirurgien', 'Chirurgien'),
                ('urgentiste', 'Urgentiste'),
                ('psychiatre', 'Psychiatre'),
                ('endocrinologue', 'Endocrinologue'),
                ('gastro_enterologue', 'Gastro-entérologue'),
                ('pneumologue', 'Pneumologue'),
                ('rhumatologue', 'Rhumatologue'),
                ('urologue', 'Urologue'),
                ('ORL', 'ORL'),
            ], max_length=50),
        ),
        # Création DisponibiliteMedecin
        migrations.CreateModel(
            name='DisponibiliteMedecin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jour_semaine', models.IntegerField(choices=[(0, 'Lundi'), (1, 'Mardi'), (2, 'Mercredi'), (3, 'Jeudi'), (4, 'Vendredi'), (5, 'Samedi'), (6, 'Dimanche')])),
                ('heure_debut', models.TimeField()),
                ('heure_fin', models.TimeField()),
                ('duree_creneau', models.IntegerField(default=30)),
                ('actif', models.BooleanField(default=True)),
                ('validite_depuis', models.DateField()),
                ('validite_jusqua', models.DateField(blank=True, null=True)),
                ('hopital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='disponibilites', to='hopitaux.hopital')),
                ('medecin', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='disponibilites', to='medecins.medecin')),
            ],
            options={
                'verbose_name': 'Disponibilité médecin',
                'verbose_name_plural': 'Disponibilités médecin',
                'ordering': ['medecin', 'jour_semaine', 'heure_debut'],
            },
        ),
        # Création CongeMedecin
        migrations.CreateModel(
            name='CongeMedecin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_debut', models.DateField()),
                ('date_fin', models.DateField()),
                ('motif', models.CharField(blank=True, default='', max_length=200)),
                ('medecin', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conges', to='medecins.medecin')),
            ],
            options={
                'verbose_name': 'Congé médecin',
                'verbose_name_plural': 'Congés médecin',
                'ordering': ['-date_debut'],
            },
        ),
    ]
