"""Migration pour ajouter LitHopital à l'app hopitaux."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hopitaux', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LitHopital',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service', models.CharField(choices=[('urgences', 'Urgences'), ('reanimation', 'Réanimation'), ('chirurgie', 'Chirurgie'), ('medecine', 'Médecine'), ('maternite', 'Maternité'), ('pediatrie', 'Pédiatrie'), ('soins_continus', 'Soins continus')], max_length=20)),
                ('total', models.IntegerField(default=0)),
                ('occupes', models.IntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('hopital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lits', to='hopitaux.hopital')),
            ],
            options={
                'verbose_name': 'Lit hôpital',
                'verbose_name_plural': 'Lits hôpital',
                'unique_together': {('hopital', 'service')},
            },
        ),
    ]
