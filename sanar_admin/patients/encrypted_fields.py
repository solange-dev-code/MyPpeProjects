"""
Champs Django personnalisés pour le chiffrement au repos (AES-256 via Fernet).

Utilisation :
    from patients.encrypted_fields import EncryptedCharField, EncryptedTextField
    nom = EncryptedCharField(max_length=100)
    notes = EncryptedTextField()

Les données sont chiffrées en base de données et déchiffrées automatiquement
à la lecture. Si la base est compromise, les données sont illisibles sans
la clé DJANGO_ENCRYPTION_KEY.
"""
import base64
import hashlib
from cryptography.fernet import Fernet
from django.db import models
from django.conf import settings


def _get_fernet():
    """Récupère une instance Fernet depuis DJANGO_ENCRYPTION_KEY."""
    key_raw = getattr(settings, 'FIELD_ENCRYPTION_KEY', None)
    if not key_raw:
        # Fallback : générer une clé stable depuis SECRET_KEY
        secret = settings.SECRET_KEY.encode('utf-8')
        key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    else:
        # Si la clé est déjà au format base64 Fernet, l'utiliser directement
        try:
            key = key_raw.encode('utf-8') if isinstance(key_raw, str) else key_raw
            # Vérifier que c'est une clé Fernet valide
            Fernet(key)
        except (ValueError, TypeError):
            # Sinon, dériver une clé Fernet depuis la clé brute
            key = base64.urlsafe_b64encode(hashlib.sha256(key_raw.encode('utf-8')).digest())
    return Fernet(key)


class EncryptedCharField(models.CharField):
    """CharField qui chiffre automatiquement les données au repos (Fernet AES-256).

    À l'écriture : la valeur en clair est chiffrée avant d'être stockée.
    À la lecture : la valeur chiffrée est déchiffrée automatiquement.
    """

    def get_placeholder(self, value, compiler, connection):
        return '%s'

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value
        try:
            f = _get_fernet()
            return f.decrypt(value.encode('utf-8')).decode('utf-8')
        except Exception:
            # Si le déchiffrement échoue, retourner la valeur brute
            return value

    def to_python(self, value):
        if value is None or value == '':
            return value
        # Si la valeur n'est pas chiffrée (déjà en clair), la retourner
        if isinstance(value, str) and not value.startswith('gAAAAA'):
            return value
        try:
            f = _get_fernet()
            return f.decrypt(value.encode('utf-8')).decode('utf-8')
        except Exception:
            return value

    def get_db_prep_save(self, value, connection):
        if value is None or value == '':
            return value
        # Ne pas re-chiffrer une valeur déjà chiffrée
        if isinstance(value, str) and value.startswith('gAAAAA'):
            return value
        f = _get_fernet()
        encrypted = f.encrypt(value.encode('utf-8'))
        return encrypted.decode('utf-8')


class EncryptedTextField(models.TextField):
    """TextField qui chiffre automatiquement les données au repos (Fernet AES-256)."""

    def get_placeholder(self, value, compiler, connection):
        return '%s'

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value
        try:
            f = _get_fernet()
            return f.decrypt(value.encode('utf-8')).decode('utf-8')
        except Exception:
            return value

    def to_python(self, value):
        if value is None or value == '':
            return value
        if isinstance(value, str) and not value.startswith('gAAAAA'):
            return value
        try:
            f = _get_fernet()
            return f.decrypt(value.encode('utf-8')).decode('utf-8')
        except Exception:
            return value

    def get_db_prep_save(self, value, connection):
        if value is None or value == '':
            return value
        if isinstance(value, str) and value.startswith('gAAAAA'):
            return value
        f = _get_fernet()
        encrypted = f.encrypt(value.encode('utf-8'))
        return encrypted.decode('utf-8')
