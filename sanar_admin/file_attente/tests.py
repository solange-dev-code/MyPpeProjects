from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from patients.models import Patient
from hopitaux.models import Hopital
from .models import FileAttente
from .services import (
    ordre_passage, estimer_temps_attente, marquer_en_consultation,
    marquer_termine, position_patient
)


class OrdePassageTest(TestCase):
    """Tests de l'algorithme de file prioritaire."""

    def setUp(self):
        self.user = User.objects.create_user('test', 't@t.com', 'password12345')
        self.hopital = Hopital.objects.create(
            nom='CHU', adresse='Lomé', ville='Lomé',
            latitude=6.17, longitude=1.23, actif=True
        )
        self.p1 = Patient.objects.create(
            user=self.user, nom='A', prenom='P1', email='a@t.com',
            telephone='1', date_naissance='1990-01-01', adresse='Lomé',
            patient_id='P1'
        )
        self.p2 = Patient.objects.create(
            user=self.user, nom='B', prenom='P2', email='b@t.com',
            telephone='2', date_naissance='1990-01-01', adresse='Lomé',
            patient_id='P2'
        )
        # Patient P4 arrivé en premier
        self.f_p4_first = FileAttente.objects.create(
            patient=self.p1, hopital=self.hopital, niveau_triage=4
        )
        # Patient P2 arrivé en second → doit passer avant P4
        self.f_p2 = FileAttente.objects.create(
            patient=self.p2, hopital=self.hopital, niveau_triage=2
        )

    def test_p2_passe_avant_p4(self):
        """Le P2 (arrivé 2e) doit passer avant le P4 (arrivé 1er)."""
        ordre = ordre_passage(self.hopital.id)
        self.assertEqual(ordre[0], self.f_p2)
        self.assertEqual(ordre[1], self.f_p4_first)

    def test_position_patient(self):
        """Le P2 doit être en position 1, le P4 en position 2."""
        self.assertEqual(position_patient(self.f_p2), 1)
        self.assertEqual(position_patient(self.f_p4_first), 2)


class EstimationTempsTest(TestCase):
    """Tests de l'estimation du temps d'attente."""

    def setUp(self):
        self.hopital = Hopital.objects.create(
            nom='CHU', adresse='Lomé', ville='Lomé',
            latitude=6.17, longitude=1.23, actif=True
        )
        self.user = User.objects.create_user('t', 't@t.com', 'password12345')
        self.patient = Patient.objects.create(
            user=self.user, nom='X', prenom='Y', email='x@t.com',
            telephone='1', date_naissance='1990-01-01', adresse='Lomé',
            patient_id='PX'
        )

    def test_valeur_par_defaut_sans_historique(self):
        """Sans historique, l'estimation par défaut est 30 × coefficient."""
        estime = estimer_temps_attente(self.hopital.id, niveau=4)
        self.assertEqual(estime, 30)  # coef P4 = 1.0
        estime_p1 = estimer_temps_attente(self.hopital.id, niveau=1)
        self.assertEqual(estime_p1, 3)  # 30 × 0.1 = 3

    def test_estimation_calculee_avec_historique(self):
        """Avec historique, l'estimation utilise la moyenne mobile."""
        now = timezone.now()
        for i in range(5):
            f = FileAttente.objects.create(
                patient=self.patient, hopital=self.hopital,
                niveau_triage=4, statut='termine'
            )
            # Simule une attente de 20 min
            f.arrivee_at = now - timedelta(minutes=40, hours=i)
            f.consultation_at = now - timedelta(minutes=20, hours=i)
            f.fin_at = now - timedelta(hours=i)
            f.save()
        estime = estimer_temps_attente(self.hopital.id, niveau=4)
        # Devrait être ~20 min
        self.assertGreater(estime, 10)
        self.assertLess(estime, 35)
