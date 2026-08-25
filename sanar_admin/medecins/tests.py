"""Tests unitaires pour l'app medecins (disponibilités, créneaux)."""
from django.test import TestCase
from datetime import date, time
from .models import Medecin, DisponibiliteMedecin, CongeMedecin, GoogleCalendarLink
from .services import creneaux_disponibles, verifier_conflit
from hopitaux.models import Hopital


class DisponibiliteMedecinTest(TestCase):
    """Tests du modèle DisponibiliteMedecin."""

    def setUp(self):
        self.hopital = Hopital.objects.create(
            nom='CHU Test', adresse='Lomé', ville='Lomé',
            latitude=6.17, longitude=1.23, actif=True
        )
        self.medecin = Medecin.objects.create(
            nom='Test', prenom='Dr', specialite='generaliste',
            telephone='12345678', hopital=self.hopital
        )

    def test_creer_disponibilite(self):
        """Création d'une disponibilité récurrente."""
        dispo = DisponibiliteMedecin.objects.create(
            medecin=self.medecin, hopital=self.hopital,
            jour_semaine=0,  # Lundi
            heure_debut=time(9, 0), heure_fin=time(12, 0),
            duree_creneau=30, validite_depuis='2026-01-01'
        )
        self.assertEqual(dispo.duree_creneau, 30)
        self.assertEqual(dispo.jour_semaine, 0)


class CreneauxDisponiblesTest(TestCase):
    """Tests de l'algorithme creneaux_disponibles."""

    def setUp(self):
        self.hopital = Hopital.objects.create(
            nom='CHU', adresse='L', ville='L',
            latitude=6.0, longitude=1.0, actif=True
        )
        self.medecin = Medecin.objects.create(
            nom='X', prenom='Dr', specialite='generaliste',
            telephone='1', hopital=self.hopital
        )
        # Dispo le lundi 9h-12h, créneaux de 30 min
        DisponibiliteMedecin.objects.create(
            medecin=self.medecin, hopital=self.hopital,
            jour_semaine=0,  # Lundi
            heure_debut=time(9, 0), heure_fin=time(12, 0),
            duree_creneau=30, validite_depuis='2026-01-01'
        )

    def test_genere_6_creneaux_pour_3h(self):
        """3h / 30min = 6 créneaux."""
        # Lundi 5 janvier 2026
        lundi = date(2026, 1, 5)
        creneaux = creneaux_disponibles(self.medecin.id, lundi)
        self.assertEqual(len(creneaux), 6)
        self.assertEqual(creneaux[0]['heure'], '09:00')
        self.assertEqual(creneaux[-1]['heure'], '11:30')

    def test_aucun_creneau_si_conge(self):
        """Médecin en congé → aucun créneau."""
        lundi = date(2026, 1, 5)
        CongeMedecin.objects.create(
            medecin=self.medecin,
            date_debut=lundi, date_fin=lundi,
            motif='Formation'
        )
        creneaux = creneaux_disponibles(self.medecin.id, lundi)
        self.assertEqual(len(creneaux), 0)

    def test_aucun_creneau_si_pas_dispo_ce_jour(self):
        """Médecin sans dispo le dimanche → aucun créneau."""
        dimanche = date(2026, 1, 4)  # Dimanche
        creneaux = creneaux_disponibles(self.medecin.id, dimanche)
        self.assertEqual(len(creneaux), 0)


class GoogleCalendarLinkTest(TestCase):
    """Tests du modèle GoogleCalendarLink."""

    def setUp(self):
        self.hopital = Hopital.objects.create(
            nom='H', adresse='L', ville='L',
            latitude=6.0, longitude=1.0, actif=True
        )
        self.medecin = Medecin.objects.create(
            nom='G', prenom='Dr', specialite='cardiologue',
            telephone='1', hopital=self.hopital
        )

    def test_lien_google_cree(self):
        """Création d'un lien Google Calendar."""
        from django.utils import timezone
        from datetime import timedelta
        link = GoogleCalendarLink.objects.create(
            medecin=self.medecin,
            access_token='token123',
            refresh_token='refresh456',
            token_expiry=timezone.now() + timedelta(hours=1),
            calendar_id='primary',
        )
        self.assertTrue(link.token_valide)
        self.assertEqual(link.calendar_id, 'primary')
