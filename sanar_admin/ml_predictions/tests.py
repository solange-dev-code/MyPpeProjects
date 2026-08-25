"""Tests unitaires pour l'app ml_predictions."""
from django.test import TestCase
from django.contrib.auth.models import User
from patients.models import Patient
from .models import MLModel, MLPrediction
from .services import extraire_features_patient, predire_risque_patient


class MLPredictionModelTest(TestCase):
    """Tests du modèle MLPrediction."""

    def setUp(self):
        self.user = User.objects.create_user('t', 't@e.com', 'Sup3rStr0ngPass!')
        self.patient = Patient.objects.create(
            user=self.user, nom='ML', prenom='Test',
            email='t@e.com', telephone='1',
            date_naissance='1990-01-01', adresse='L',
            patient_id='ML001',
        )

    def test_niveau_risque_calcule_auto(self):
        """Le niveau_risque est calculé à partir du score."""
        pred = MLPrediction.objects.create(
            patient=self.patient,
            score_risque=0.85,
            features_importantes={},
            analyses_utilisees=[],
        )
        self.assertEqual(pred.niveau_risque, 'critique')

    def test_niveau_faible(self):
        pred = MLPrediction.objects.create(
            patient=self.patient, score_risque=0.15,
            features_importantes={}, analyses_utilisees=[],
        )
        self.assertEqual(pred.niveau_risque, 'faible')

    def test_niveau_modere(self):
        pred = MLPrediction.objects.create(
            patient=self.patient, score_risque=0.45,
            features_importantes={}, analyses_utilisees=[],
        )
        self.assertEqual(pred.niveau_risque, 'modere')

    def test_niveau_eleve(self):
        pred = MLPrediction.objects.create(
            patient=self.patient, score_risque=0.70,
            features_importantes={}, analyses_utilisees=[],
        )
        self.assertEqual(pred.niveau_risque, 'eleve')


class MLModelTest(TestCase):
    """Tests du modèle MLModel."""

    def test_creer_modele(self):
        modele = MLModel.objects.create(
            nom='random_forest_analyses',
            version='v1.0',
            precision=0.85,
            rappel=0.78,
            auc=0.91,
            hyperparametres={'n_estimators': 100},
            est_actif=True,
        )
        self.assertEqual(modele.version, 'v1.0')
        self.assertTrue(modele.est_actif)
        self.assertEqual(modele.hyperparametres['n_estimators'], 100)


class ServicePredictionFroidTest(TestCase):
    """Tests du service de prédiction (cas froid sans modèle)."""

    def setUp(self):
        self.user = User.objects.create_user('t', 't@e.com', 'Sup3rStr0ngPass!')
        self.patient = Patient.objects.create(
            user=self.user, nom='ML', prenom='Test',
            email='t@e.com', telephone='1',
            date_naissance='1990-01-01', adresse='L',
            patient_id='ML002',
        )

    def test_prediction_froide_sans_modele(self):
        """Sans modèle entraîné, retourne une prédiction froide."""
        pred = predire_risque_patient(self.patient.id)
        self.assertIsNotNone(pred)
        self.assertIsNone(pred.modele)
        self.assertIn('note', pred.features_importantes)
        self.assertEqual(pred.features_importantes['note'], 'modele_froid')

    def test_patient_critique_score_plus_eleve(self):
        """Un patient est_critique doit avoir un score plus élevé."""
        self.patient.est_critique = True
        self.patient.save()
        pred = predire_risque_patient(self.patient.id)
        self.assertGreater(pred.score_risque, 0.4)


class ExtraireFeaturesTest(TestCase):
    """Tests de l'extraction de features."""

    def setUp(self):
        self.user = User.objects.create_user('t', 't@e.com', 'Sup3rStr0ngPass!')
        self.patient = Patient.objects.create(
            user=self.user, nom='F', prenom='Test',
            email='t@e.com', telephone='1',
            date_naissance='1990-01-01', adresse='L',
            patient_id='ML003',
        )

    def test_sans_analyses_retourne_dict_vide(self):
        """Patient sans analyses → dict vide."""
        features = extraire_features_patient(self.patient.id)
        self.assertEqual(features, {})
