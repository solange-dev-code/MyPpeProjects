"""Tests unitaires pour l'app hopitaux (LitHopital, assignation)."""
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Hopital, LitHopital
from .services import haversine_km, assigner_hopital
from patients.models import Patient


class LitHopitalTest(TestCase):
    """Tests du modèle LitHopital."""

    def setUp(self):
        self.hopital = Hopital.objects.create(
            nom='CHU', adresse='L', ville='Lomé',
            latitude=6.17, longitude=1.23, actif=True
        )

    def test_lits_disponibles_calcule(self):
        """La propriété disponibles = total - occupes."""
        lit = LitHopital.objects.create(
            hopital=self.hopital, service='urgences',
            total=20, occupes=12
        )
        self.assertEqual(lit.disponibles, 8)

    def test_taux_occupation(self):
        """taux_occupation = occupes / total."""
        lit = LitHopital.objects.create(
            hopital=self.hopital, service='reanimation',
            total=10, occupes=7
        )
        self.assertEqual(lit.taux_occupation, 0.7)

    def test_disponibles_jamais_negatif(self):
        """disponibles ne descend jamais sous 0."""
        lit = LitHopital.objects.create(
            hopital=self.hopital, service='chirurgie',
            total=5, occupes=8  # erreur de saisie
        )
        self.assertEqual(lit.disponibles, 0)


class HaversineTest(TestCase):
    """Tests de la formule Haversine."""

    def test_distance_zero(self):
        """Distance entre 2 points identiques = 0."""
        self.assertEqual(haversine_km(6.17, 1.23, 6.17, 1.23), 0.0)

    def test_distance_positive(self):
        """Distance Lomé-Paris ≈ 4700 km."""
        d = haversine_km(6.17, 1.23, 48.85, 2.35)
        self.assertGreater(d, 4500)
        self.assertLess(d, 5000)


class AssignationHopitalTest(TestCase):
    """Tests de l'algorithme d'assignation multi-critères."""

    def setUp(self):
        self.user = User.objects.create_user('t', 't@e.com', 'Sup3rStr0ngPass!')
        self.patient = Patient.objects.create(
            user=self.user, nom='P', prenom='Test',
            email='t@e.com', telephone='1',
            date_naissance='1990-01-01', adresse='L',
            patient_id='HTEST001',
        )
        self.h1 = Hopital.objects.create(
            nom='CHU Lomé', adresse='Lomé', ville='Lomé',
            latitude=6.17, longitude=1.23, actif=True
        )
        self.h2 = Hopital.objects.create(
            nom='CHR Sokodé', adresse='Sokodé', ville='Sokodé',
            latitude=8.98, longitude=1.59, actif=True
        )

    def test_assigne_hopital_le_plus_proche(self):
        """Patient à Lomé → assigné à CHU Lomé."""
        h = assigner_hopital(
            self.patient,
            latitude=6.17, longitude=1.23,
            niveau_urgence='P3'
        )
        self.assertEqual(h, self.h1)

    def test_aucun_hopital_actif_retourne_none(self):
        """Si tous les hôpitaux inactifs → None."""
        Hopital.objects.filter(actif=True).update(actif=False)
        h = assigner_hopital(self.patient, latitude=6.0, longitude=1.0)
        self.assertIsNone(h)

    def test_filtre_par_specialite(self):
        """Si spécialité requise non disponible → None."""
        # Aucun médecin cardiologue dans aucun hôpital
        h = assigner_hopital(
            self.patient,
            specialite_requise='cardiologue',
            latitude=6.17, longitude=1.23
        )
        self.assertIsNone(h)
