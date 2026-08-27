"""Migration pour les champs chiffrés du Patient.
Note : les types de champs restent CharField/TextField en base (héritage),
donc cette migration ne change rien au schéma. Elle est juste pour tracer le changement.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0005_patient_hachage'),
    ]

    operations = [
        # Pas d'opération : les champs EncryptedCharField héritent de CharField
        # et ont le même type en base de données. Le chiffrement est géré
        # au niveau Python (from_db_value / get_db_prep_save), pas au niveau DB.
    ]
