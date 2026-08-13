"""Tests unitaires pour l'app patients."""
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Patient
import uuid


class PatientModelTest(TestCase):
    """Tests du modèle Patient (token urgence, régénération)."""

    def setUp(self):
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'Sup3rStr0ngPass!'
        )
        self.patient = Patient.objects.create(
            user=self.user,
            nom='Dupont', prenom='Jean',
            email='test@example.com',
            telephone='+22890123456',
            date_naissance='1990-05-15',
            adresse='Lomé, Togo',
            patient_id='TEST001',
        )

    def test_token_urgence_genere_auto(self):
        """Le token_urgence doit être généré automatiquement à la création."""
        self.assertIsNotNone(self.patient.token_urgence)
        self.assertIsInstance(self.patient.token_urgence, uuid.UUID)

    def test_urgence_qr_actif_default_true(self):
        """Le QR code d'urgence est actif par défaut."""
        self.assertTrue(self.patient.urgence_qr_actif)

    def test_regenerer_token_urgence(self):
        """La régénération crée un nouveau token (l'ancien est révoqué)."""
        old_token = self.patient.token_urgence
        new_token = self.patient.regenerer_token_urgence()
        self.assertNotEqual(old_token, new_token)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.token_urgence, new_token)

    def test_token_unique(self):
        """Chaque patient a un token unique."""
        user2 = User.objects.create_user('u2', 'u2@e.com', 'Sup3rStr0ngPass!')
        p2 = Patient.objects.create(
            user=user2, nom='X', prenom='Y', email='u2@e.com',
            telephone='2', date_naissance='2000-01-01', adresse='Y',
            patient_id='TEST002',
        )
        self.assertNotEqual(self.patient.token_urgence, p2.token_urgence)

    def test_str_representation(self):
        """__str__ retourne 'prenom nom'."""
        self.assertEqual(str(self.patient), 'Jean Dupont')


class PatientSignalTest(TestCase):
    """Tests du signal post_save créant le DossierMedical."""

    def test_dossier_medical_cree_automatiquement(self):
        """La création d'un Patient crée automatiquement son DossierMedical."""
        from dossiers_medicaux.models import DossierMedical
        user = User.objects.create_user('s', 's@e.com', 'Sup3rStr0ngPass!')
        patient = Patient.objects.create(
            user=user, nom='Signal', prenom='Test',
            email='s@e.com', telephone='3',
            date_naissance='2000-01-01', adresse='L', patient_id='SIG001',
        )
        self.assertTrue(DossierMedical.objects.filter(patient=patient).exists())
