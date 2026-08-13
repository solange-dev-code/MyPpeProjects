"""Migration pour GoogleCalendarLink (medecins)."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('medecins', '0003_medecin_enriched'),
    ]

    operations = [
        migrations.CreateModel(
            name='GoogleCalendarLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.TextField()),
                ('refresh_token', models.TextField()),
                ('token_expiry', models.DateTimeField()),
                ('calendar_id', models.CharField(default='primary', max_length=200)),
                ('sync_actif', models.BooleanField(default=True)),
                ('last_sync', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('medecin', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='google_calendar', to='medecins.medecin')),
            ],
            options={
                'verbose_name': 'Lien Google Calendar',
                'verbose_name_plural': 'Liens Google Calendar',
            },
        ),
    ]
