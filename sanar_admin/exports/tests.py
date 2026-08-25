"""Tests unitaires pour l'app exports (PDF, CSV, FHIR)."""
from django.test import TestCase
from django.contrib.auth.models import User
from patients.models import Patient
from dossiers_medicaux.models import DossierMedical
from analyses.models import Analyse
from consultations.models import Consultation
from .services import (
    export_dossier_pdf, export_patients_csv, export_dossier_fhir,
    _patient_to_fhir
)


class ExportPDFTest(TestCase):
    """Tests de l'export PDF WeasyPrint (avec fallback reportlab)."""

    def setUp(self):
        self.user = User.objects.create_user('t', 't@e.com', 'Sup3rStr0ngPass!')
        self.patient = Patient.objects.create(
            user=self.user, nom='PDF', prenom='Test',
            email='t@e.com', telephone='1',
            date_naissance='1990-01-01', adresse='L',
            patient_id='PDF001',
        )

    def test_export_pdf_retourne_bytes(self):
        """L'export PDF retourne des bytes non vides."""
        pdf_bytes = export_dossier_pdf(self.patient)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)
        # Vérifie signature PDF
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))


class ExportCSVTest(TestCase):
    """Tests de l'export CSV."""

    def setUp(self):
        user = User.objects.create_user('t', 't@e.com', 'Sup3rStr0ngPass!')
        Patient.objects.create(
            user=user, nom='CSV', prenom='Test',
            email='t@e.com', telephone='1',
            date_naissance='1990-01-01', adresse='L',
            patient_id='CSV001',
        )

    def test_export_csv_retourne_string(self):
        """L'export CSV retourne une string avec header + données."""
        csv_content = export_patients_csv()
        self.assertIsInstance(csv_content, str)
        self.assertIn('patient_id', csv_content)
        self.assertIn('age', csv_content)
        self.assertIn('CSV001', csv_content)


class ExportFHIRTest(TestCase):
    """Tests de l'export FHIR R4."""

    def setUp(self):
        self.user = User.objects.create_user('t', 't@e.com', 'Sup3rStr0ngPass!')
        self.patient = Patient.objects.create(
            user=self.user, nom='FHIR', prenom='Test',
            email='t@e.com', telephone='1',
            date_naissance='1990-01-01', adresse='L',
            patient_id='FHIR001',
        )

    def test_patient_to_fhir_conforme(self):
        """La resource Patient FHIR a les champs requis."""
        fhir_patient = _patient_to_fhir(self.patient)
        self.assertEqual(fhir_patient['resourceType'], 'Patient')
        self.assertEqual(fhir_patient['name'][0]['family'], 'FHIR')
        self.assertEqual(fhir_patient['name'][0]['given'], ['Test'])
        self.assertEqual(fhir_patient['birthDate'], '1990-01-01')
        self.assertIn('blood-type', str(fhir_patient['extension']))

    def test_export_dossier_fhir_bundle(self):
        """L'export FHIR génère un Bundle avec au moins la resource Patient."""
        bundle = export_dossier_fhir(self.patient)
        self.assertEqual(bundle['resourceType'], 'Bundle')
        self.assertEqual(bundle['type'], 'collection')
        self.assertGreaterEqual(len(bundle['entry']), 1)
        self.assertEqual(bundle['entry'][0]['resource']['resourceType'], 'Patient')
