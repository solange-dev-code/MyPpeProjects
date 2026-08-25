"""Tests unitaires pour l'app teleconsultation."""
from django.test import TestCase
from django.contrib.auth.models import User
from patients.models import Patient
from medecins.models import Medecin
from hopitaux.models import Hopital
from .models import Teleconsultation, WebRTCSignaling
import uuid


class TeleconsultationModelTest(TestCase):
    """Tests du modèle Teleconsultation."""

    def setUp(self):
        self.user_patient = User.objects.create_user('p', 'p@e.com', 'Sup3rStr0ngPass!')
        self.user_medecin = User.objects.create_user('m', 'm@e.com', 'Sup3rStr0ngPass!')
        self.hopital = Hopital.objects.create(
            nom='CHU', adresse='L', ville='Lomé',
            latitude=6.0, longitude=1.0, actif=True
        )
        self.patient = Patient.objects.create(
            user=self.user_patient, nom='T', prenom='P',
            email='p@e.com', telephone='1',
            date_naissance='1990-01-01', adresse='L',
            patient_id='TEL001',
        )
        self.medecin = Medecin.objects.create(
            user=self.user_medecin,
            nom='Dr', prenom='Med', specialite='generaliste',
            telephone='2', hopital=self.hopital
        )

    def test_room_uuid_genere_auto(self):
        """Le room_uuid est généré automatiquement."""
        from django.utils import timezone
        tc = Teleconsultation.objects.create(
            patient=self.patient, medecin=self.medecin,
            initiateur=self.user_medecin,
            date_planifiee=timezone.now(),
        )
        self.assertIsNotNone(tc.room_uuid)
        self.assertIsInstance(tc.room_uuid, uuid.UUID)

    def test_statut_default_planifiee(self):
        """Le statut par défaut est 'planifiee'."""
        from django.utils import timezone
        tc = Teleconsultation.objects.create(
            patient=self.patient, medecin=self.medecin,
            date_planifiee=timezone.now(),
        )
        self.assertEqual(tc.statut, 'planifiee')

    def test_duree_reelle_calcule(self):
        """La durée réelle est calculée si date_debut + date_fin présentes."""
        from django.utils import timezone
        from datetime import timedelta
        tc = Teleconsultation.objects.create(
            patient=self.patient, medecin=self.medecin,
            date_planifiee=timezone.now(),
            date_debut=timezone.now() - timedelta(minutes=15),
            date_fin=timezone.now(),
        )
        # Environ 900 secondes (15 min)
        self.assertIsNotNone(tc.duree_reelle)
        self.assertGreater(tc.duree_reelle, 800)
        self.assertLess(tc.duree_reelle, 1000)


class WebRTCSignalingTest(TestCase):
    """Tests du modèle WebRTCSignaling."""

    def setUp(self):
        self.user = User.objects.create_user('u', 'u@e.com', 'Sup3rStr0ngPass!')
        self.user2 = User.objects.create_user('u2', 'u2@e.com', 'Sup3rStr0ngPass!')
        self.hopital = Hopital.objects.create(
            nom='H', adresse='L', ville='L',
            latitude=6.0, longitude=1.0, actif=True
        )
        self.patient = Patient.objects.create(
            user=self.user, nom='T', prenom='P',
            email='u@e.com', telephone='1',
            date_naissance='1990-01-01', adresse='L',
            patient_id='TEL002',
        )
        self.medecin = Medecin.objects.create(
            user=self.user2, nom='Dr', prenom='Med',
            specialite='generaliste', telephone='2',
            hopital=self.hopital
        )
        from django.utils import timezone
        self.tc = Teleconsultation.objects.create(
            patient=self.patient, medecin=self.medecin,
            date_planifiee=timezone.now(),
        )

    def test_log_signaling_cree(self):
        """Création d'une entrée de journalisation WebRTC."""
        log = WebRTCSignaling.objects.create(
            teleconsultation=self.tc,
            expediteur=self.user,
            type_message='offer',
            contenu='{"sdp": "v=0..."}',
        )
        self.assertEqual(log.type_message, 'offer')
        self.assertEqual(log.expediteur, self.user)
