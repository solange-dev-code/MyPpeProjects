"""Tests unitaires basiques pour le module urgences."""
from django.test import TestCase
from django.contrib.auth.models import User
from patients.models import Patient
from hopitaux.models import Hopital
from urgences.models import DemandeUrgence, AccesUrgence
from urgences.services import haversine, hopital_optimal


class HaversineTest(TestCase):
    """Tests de la formule Haversine."""

    def test_distance_zero_quand_meme_point(self):
        self.assertEqual(haversine(6.17, 1.23, 6.17, 1.23), 0.0)

    def test_distance_lome_paris_positive(self):
        # Lomé ≈ (6.17, 1.23), Paris ≈ (48.85, 2.35)
        d = haversine(6.17, 1.23, 48.85, 2.35)
        # ~ 4700 km, à 10% près
        self.assertGreater(d, 4500)
        self.assertLess(d, 5000)


class HopitalOptimalTest(TestCase):
    """Tests de l'algorithme de sélection d'hôpital."""

    def setUp(self):
        self.h1 = Hopital.objects.create(
            nom='CHU Campus', adresse='Lomé', ville='Lomé',
            latitude=6.17, longitude=1.23, actif=True
        )
        self.h2 = Hopital.objects.create(
            nom='CHR Sokodé', adresse='Sokodé', ville='Sokodé',
            latitude=8.98, longitude=1.59, actif=True
        )

    def test_hopital_le_plus_proche(self):
        """Patient à Lomé → doit sélectionner CHU Campus."""
        hopital = hopital_optimal(6.17, 1.23, niveau='P2')
        self.assertEqual(hopital, self.h1)

    def test_aucun_hopital_actif_retourne_none(self):
        Hopital.objects.filter(actif=True).update(actif=False)
        self.assertIsNone(hopital_optimal(6.17, 1.23))

    def test_hopital_ignore_sans_gps(self):
        self.h1.latitude = None
        self.h1.longitude = None
        self.h1.save()
        hopital = hopital_optimal(6.17, 1.23)
        self.assertEqual(hopital, self.h2)


class AccesUrgenceAuditTest(TestCase):
    """Tests du journal d'audit RGPD."""

    def test_acces_urgence_est_journalise(self):
        user = User.objects.create_user('testuser', 't@t.com', 'password12345')
        patient = Patient.objects.create(
            user=user, nom='Test', prenom='Unit',
            email='t@t.com', telephone='12345678',
            date_naissance='1990-01-01', adresse='Lomé',
            patient_id='TEST001',
        )
        acces = AccesUrgence.objects.create(
            patient=patient, source_ip='127.0.0.1',
            user_agent='TestUA'
        )
        self.assertEqual(acces.patient, patient)
        self.assertEqual(acces.source_ip, '127.0.0.1')
