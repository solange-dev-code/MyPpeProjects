"""Migration pour ajouter token_urgence et urgence_qr_actif au Patient."""
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0003_patient_hopital'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='token_urgence',
            field=models.UUIDField(
                db_index=True, default=uuid.uuid4, editable=False,
                help_text="Token opaque pour l'accès d'urgence par QR code",
                unique=True
            ),
        ),
        migrations.AddField(
            model_name='patient',
            name='urgence_qr_actif',
            field=models.BooleanField(
                default=True,
                help_text="Si False, l'endpoint d'urgence refuse l'accès (révocation)"
            ),
        ),
    ]
