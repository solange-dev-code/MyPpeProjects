"""
Tests d'endpoints API REST avec DRF APIClient.

Couvre les cas :
- Authentification (login, register, JWT)
- 401 sans token
- 403 avec token mais permissions insuffisantes
- 404 ressources inexistantes
- Conflit RDV (double-booking)
- Endpoint public d'urgence (sans auth)
- Health check
- Signature électronique prescription
- Anonymisation RGPD
- Recherche floue patients
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from patients.models import Patient
from medecins.models import Medecin
from hopitaux.models import Hopital
from dossiers_medicaux.models import DossierMedical, Prescription
from appointments.models import RendezVous
from datetime import date, time


class APITestBase(TestCase):
    """Base class avec setup client API + users."""

    def setUp(self):
        self.client = APIClient()
        # User patient
        self.user_patient = User.objects.create_user(
            'patient_test', 'patient@test.com', 'Sup3rStr0ngPass!'
        )
        self.hopital = Hopital.objects.create(
            nom='CHU Test', adresse='Lomé', ville='Lomé',
            latitude=6.17, longitude=1.23, actif=True
        )
        self.patient = Patient.objects.create(
            user=self.user_patient, nom='Test', prenom='Patient',
            email='patient@test.com', telephone='+22890123456',
            date_naissance='1990-01-01', adresse='Lomé',
            patient_id='API001', hopital=self.hopital
        )
        # User médecin
        self.user_medecin = User.objects.create_user(
            'medecin_test', 'medecin@test.com', 'Sup3rStr0ngPass!'
        )
        self.medecin = Medecin.objects.create(
            user=self.user_medecin, nom='Dr', prenom='Medecin',
            specialite='generaliste', telephone='12345678',
            hopital=self.hopital
        )

    def auth_patient(self):
        """Authentifie le client en tant que patient."""
        refresh = RefreshToken.for_user(self.user_patient)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def auth_medecin(self):
        """Authentifie le client en tant que médecin."""
        refresh = RefreshToken.for_user(self.user_medecin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')


class AuthEndpointTest(APITestBase):
    """Tests des endpoints d'authentification."""

    def test_login_succes(self):
        """Login avec credentials valides retourne JWT."""
        response = self.client.post('/api/auth/login/', {
            'username': 'patient@test.com',
            'password': 'Sup3rStr0ngPass!'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_echec_mot_de_passe_faux(self):
        """Login avec mauvais mot de passe → 401."""
        response = self.client.post('/api/auth/login/', {
            'username': 'patient@test.com',
            'password': 'wrong'
        }, format='json')
        self.assertEqual(response.status_code, 401)

    def test_login_user_inexistant(self):
        """Login avec user inexistant → 401."""
        response = self.client.post('/api/auth/login/', {
            'username': 'nobody@test.com',
            'password': 'whatever'
        }, format='json')
        self.assertEqual(response.status_code, 401)


class UnauthorizedAccessTest(APITestBase):
    """Tests 401 sans authentification."""

    def test_profil_sans_token_retourne_401(self):
        """GET /api/patient/profile/ sans token → 401."""
        response = self.client.get('/api/patient/profile/')
        self.assertEqual(response.status_code, 401)

    def test_dossier_medical_sans_token_retourne_401(self):
        response = self.client.get('/api/dossier-medical/')
        self.assertEqual(response.status_code, 401)

    def test_rdv_sans_token_retourne_401(self):
        response = self.client.get('/api/rendez-vous/')
        self.assertEqual(response.status_code, 401)

    def test_creer_urgence_sans_token_retourne_401(self):
        """Le bouton SOS nécessite une authentification."""
        response = self.client.post('/api/urgences/', {
            'niveau': 'P2', 'latitude': 6.17, 'longitude': 1.23
        }, format='json')
        self.assertEqual(response.status_code, 401)


class AuthorizedAccessTest(APITestBase):
    """Tests avec authentification valide."""

    def test_profil_avec_token_retourne_200(self):
        self.auth_patient()
        response = self.client.get('/api/patient/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['nom'], 'Test')

    def test_dossier_medical_avec_token(self):
        self.auth_patient()
        response = self.client.get('/api/dossier-medical/')
        self.assertEqual(response.status_code, 200)

    def test_liste_medecins(self):
        self.auth_patient()
        response = self.client.get('/api/medecins/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_liste_hopitaux(self):
        self.auth_patient()
        response = self.client.get('/api/hopitaux/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['nom'], 'CHU Test')


class NotFoundTest(APITestBase):
    """Tests 404 ressources inexistantes."""

    def test_rdv_inexistant_retourne_404(self):
        self.auth_patient()
        response = self.client.delete('/api/rendez-vous/99999/')
        self.assertEqual(response.status_code, 404)

    def test_prescription_inexistante_signer_retourne_404(self):
        self.auth_medecin()
        response = self.client.post('/api/prescriptions/99999/signer/')
        self.assertEqual(response.status_code, 404)


class ConflitRDVTest(APITestBase):
    """Tests de détection de double-booking."""

    def test_double_booking_retourne_409(self):
        """Deux RDV au même créneau → 409 Conflict."""
        self.auth_patient()
        # 1er RDV
        response1 = self.client.post('/api/rendez-vous/', {
            'medecin_id': self.medecin.id,
            'date': '2026-09-15',
            'heure': '10:00',
            'motif': 'Test 1'
        }, format='json')
        self.assertEqual(response1.status_code, 201)

        # 2e RDV même créneau → conflit
        response2 = self.client.post('/api/rendez-vous/', {
            'medecin_id': self.medecin.id,
            'date': '2026-09-15',
            'heure': '10:00',
            'motif': 'Test 2'
        }, format='json')
        self.assertEqual(response2.status_code, 409)
        self.assertIn('déjà réservé', response2.data['error'])


class EndpointPublicUrgenceTest(APITestBase):
    """Tests de l'endpoint public d'urgence par QR code."""

    def test_acces_urgence_sans_auth_retourne_200(self):
        """L'endpoint /api/urgence/<token>/ est PUBLIC."""
        response = self.client.get(f'/api/urgence/{self.patient.token_urgence}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['nom'], 'Test')
        self.assertEqual(response.data['groupe_sanguin'], 'O+')

    def test_acces_urgence_token_invalide_retourne_404(self):
        """Token invalide → 404."""
        import uuid
        fake_uuid = uuid.uuid4()
        response = self.client.get(f'/api/urgence/{fake_uuid}/')
        self.assertEqual(response.status_code, 404)

    def test_acces_urgence_qr_desactive_retourne_404(self):
        """QR code désactivé → 404."""
        self.patient.urgence_qr_actif = False
        self.patient.save()
        response = self.client.get(f'/api/urgence/{self.patient.token_urgence}/')
        self.assertEqual(response.status_code, 404)


class HealthCheckTest(APITestBase):
    """Tests du health check."""

    def test_health_check_sans_auth(self):
        """Le health check est public."""
        response = self.client.get('/api/health/')
        # 200 si DB OK, 503 si DB down (en test, DB est OK)
        self.assertIn(response.status_code, [200, 503])
        self.assertIn('status', response.data)
        self.assertIn('services', response.data)


class SignatureElectroniqueTest(APITestBase):
    """Tests de la signature électronique des prescriptions."""

    def setUp(self):
        super().setUp()
        # Crée une prescription pour le patient
        self.dossier = DossierMedical.objects.get(patient=self.patient)
        self.prescription = Prescription.objects.create(
            dossier=self.dossier,
            medicament='Paracetamol',
            posologie='1g x 3/jour',
            duree='7 jours'
        )

    def test_signature_par_medecin_reussit(self):
        """Un médecin peut signer une prescription."""
        self.auth_medecin()
        response = self.client.post(
            f'/api/prescriptions/{self.prescription.id}/signer/'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('signature_hash', response.data)
        self.prescription.refresh_from_db()
        self.assertTrue(self.prescription.est_signee)

    def test_signature_par_patient_refuse_403(self):
        """Un patient ne peut pas signer une prescription → 403."""
        self.auth_patient()
        response = self.client.post(
            f'/api/prescriptions/{self.prescription.id}/signer/'
        )
        self.assertEqual(response.status_code, 403)

    def test_double_signature_refuse_400(self):
        """Une prescription déjà signée → 400."""
        self.auth_medecin()
        # 1ère signature
        self.client.post(f'/api/prescriptions/{self.prescription.id}/signer/')
        # 2e tentative
        response = self.client.post(
            f'/api/prescriptions/{self.prescription.id}/signer/'
        )
        self.assertEqual(response.status_code, 400)

    def test_verification_integrite_apres_signature(self):
        """Vérification d'intégrité OK après signature."""
        self.auth_medecin()
        self.client.post(f'/api/prescriptions/{self.prescription.id}/signer/')
        response = self.client.get(
            f'/api/prescriptions/{self.prescription.id}/verifier/'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['est_signee'])
        self.assertTrue(response.data['integrite_verifiee'])

    def test_integrite_modifiee_apres_changement(self):
        """Modification après signature → integrite_verifiee=False."""
        self.auth_medecin()
        self.client.post(f'/api/prescriptions/{self.prescription.id}/signer/')
        # Modification illégitime
        self.prescription.medicament = 'Ibuprofene'
        self.prescription.save()
        response = self.client.get(
            f'/api/prescriptions/{self.prescription.id}/verifier/'
        )
        self.assertTrue(response.data['est_signee'])
        self.assertFalse(response.data['integrite_verifiee'])


class RGPDAnonymisationTest(APITestBase):
    """Tests de l'anonymisation RGPD (droit à l'oubli)."""

    def test_anonymisation_sans_password_refuse_400(self):
        """Anonymisation sans mot de passe → 400."""
        self.auth_patient()
        response = self.client.delete('/api/rgpd/anonymiser/', {
            'confirmation': 'ANONYMISER DEFINITIVEMENT'
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_anonymisation_password_faux_refuse_403(self):
        """Mot de passe incorrect → 403."""
        self.auth_patient()
        response = self.client.delete('/api/rgpd/anonymiser/', {
            'password': 'wrong',
            'confirmation': 'ANONYMISER DEFINITIVEMENT'
        }, format='json')
        self.assertEqual(response.status_code, 403)

    def test_anonymisation_confirmation_manquante_400(self):
        """Confirmation manquante → 400."""
        self.auth_patient()
        response = self.client.delete('/api/rgpd/anonymiser/', {
            'password': 'Sup3rStr0ngPass!'
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_anonymisation_complete_reussit(self):
        """Anonymisation complète avec password + confirmation."""
        self.auth_patient()
        response = self.client.delete('/api/rgpd/anonymiser/', {
            'password': 'Sup3rStr0ngPass!',
            'confirmation': 'ANONYMISER DEFINITIVEMENT'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.nom, 'ANONYMISE')
        self.assertFalse(self.patient.urgence_qr_actif)
        self.user_patient.refresh_from_db()
        self.assertFalse(self.user_patient.is_active)


class PortabiliteRGPDTest(APITestBase):
    """Tests du droit à la portabilité (export JSON)."""

    def test_export_mes_donnees_retourne_json(self):
        """Export JSON de toutes les données patient."""
        self.auth_patient()
        response = self.client.get('/api/rgpd/exporter-mes-donnees/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('patient', response.json())
        self.assertEqual(response.json()['patient']['nom'], 'Test')


class RechercheFloueTest(APITestBase):
    """Tests de la recherche floue de patients."""

    def setUp(self):
        super().setUp()
        # Patients supplémentaires pour test flou
        user2 = User.objects.create_user('p2', 'p2@e.com', 'Sup3rStr0ngPass!')
        Patient.objects.create(
            user=user2, nom='Dupont', prenom='Jean',
            email='p2@e.com', telephone='2',
            date_naissance='1990-01-01', adresse='L',
            patient_id='API002', hopital=self.hopital
        )
        user3 = User.objects.create_user('p3', 'p3@e.com', 'Sup3rStr0ngPass!')
        Patient.objects.create(
            user=user3, nom='Dupon', prenom='Pierre',
            email='p3@e.com', telephone='3',
            date_naissance='1990-01-01', adresse='L',
            patient_id='API003', hopital=self.hopital
        )

    def test_recherche_exacte_medecin(self):
        """Recherche exacte par médecin → résultats."""
        self.auth_medecin()
        response = self.client.get('/api/patients/recherche-floue/?q=Dupont')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['count'], 1)

    def test_recherche_floue_trouve_proche(self):
        """Recherche 'Dupont' trouve aussi 'Dupon' (faute de frappe)."""
        self.auth_medecin()
        response = self.client.get('/api/patients/recherche-floue/?q=Dupont&limit=10')
        self.assertEqual(response.status_code, 200)
        noms = [r['nom'] for r in response.data['results']]
        self.assertIn('Dupont', noms)
        # 'Dupon' doit apparaître grâce à la similarité > 60%
        self.assertIn('Dupon', noms)

    def test_recherche_trop_courte_400(self):
        """Requête < 2 caractères → 400."""
        self.auth_medecin()
        response = self.client.get('/api/patients/recherche-floue/?q=D')
        self.assertEqual(response.status_code, 400)

    def test_recherche_par_patient_refuse_403(self):
        """Un patient ne peut pas faire de recherche → 403."""
        self.auth_patient()
        response = self.client.get('/api/patients/recherche-floue/?q=Dupont')
        self.assertEqual(response.status_code, 403)


class AssignationHopitalEndpointTest(APITestBase):
    """Tests de l'endpoint d'assignation multi-hôpitaux."""

    def test_assigner_patient_sans_specialite(self):
        """Assignation basique sans spécialité requise."""
        self.auth_patient()
        response = self.client.post('/api/assigner-patient/', {
            'latitude': 6.17, 'longitude': 1.23
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['hopital_nom'], 'CHU Test')

    def test_assigner_patient_avec_specialite_inexistante(self):
        """Spécialité non disponible → 404."""
        self.auth_patient()
        response = self.client.post('/api/assigner-patient/', {
            'latitude': 6.17, 'longitude': 1.23,
            'specialite': 'neurochirurgien'  # non disponible
        }, format='json')
        self.assertEqual(response.status_code, 404)
