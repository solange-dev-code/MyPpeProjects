"""Migration pour ajouter google_event_id à RendezVous (ref google calendar)."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0004_rendezvous_hopital'),
    ]

    operations = [
        migrations.AddField(
            model_name='rendezvous',
            name='google_event_id',
            field=models.CharField(
                blank=True, default='',
                help_text="ID de l'événement correspondant dans Google Calendar",
                max_length=200
            ),
        ),
    ]
