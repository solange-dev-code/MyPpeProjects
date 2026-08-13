"""Tests unitaires pour l'app analyses (flag N/H/L/C, alertes critiques)."""
from django.test import TestCase
from django.contrib.auth.models import User
from patients.models import Patient
from .models import TypeAnalyse, ReferenceAnalyse, Analyse, ResultatAnalyse


class ResultatAnalyseFlagTest(TestCase):
    """Tests du calcul automatique du flag (N/H/L/C)."""

    def setUp(self):
        self.user = User.objects.create_user('t', 't@e.com', 'Sup3rStr0ngPass!')
        self.patient = Patient.objects.create(
            user=self.user, nom='T', prenom='U',
            email='t@e.com', telephone='1',
            date_naissance='1990-01-01', adresse='L',
            patient_id='ATEST001',
        )
        # Type avec bornes normales
        self.type_glyc = TypeAnalyse.objects.create(
            code='GLYC', nom='Glycemie', categorie='biochimie',
            unite='g/L',
            normale_basse_defaut=0.70,
            normale_haute_defaut=1.10,
            seuil_critique_basse=0.40,
            seuil_critique_haute=2.50,
        )
        self.analyse = Analyse.objects.create(
            patient=self.patient,
            type_analyse='sang',
            laboratoire='Labo Test',
            date='2026-01-01',
            statut='disponible',
        )

    def test_flag_normal(self):
        """Valeur dans la normale → flag N."""
        r = ResultatAnalyse.objects.create(
            analyse=self.analyse,
            type_analyse=self.type_glyc,
            valeur=0.90, unite='g/L'
        )
        self.assertEqual(r.flag, 'N')

    def test_flag_haut(self):
        """Valeur > normale_haute → flag H."""
        r = ResultatAnalyse.objects.create(
            analyse=self.analyse,
            type_analyse=self.type_glyc,
            valeur=1.50, unite='g/L'
        )
        self.assertEqual(r.flag, 'H')

    def test_flag_bas(self):
        """Valeur < normale_basse → flag L."""
        r = ResultatAnalyse.objects.create(
            analyse=self.analyse,
            type_analyse=self.type_glyc,
            valeur=0.50, unite='g/L'
        )
        self.assertEqual(r.flag, 'L')

    def test_flag_critique_haut(self):
        """Valeur >= seuil_critique_haute → flag C."""
        r = ResultatAnalyse.objects.create(
            analyse=self.analyse,
            type_analyse=self.type_glyc,
            valeur=3.00, unite='g/L'
        )
        self.assertEqual(r.flag, 'C')

    def test_flag_critique_bas(self):
        """Valeur <= seuil_critique_basse → flag C."""
        r = ResultatAnalyse.objects.create(
            analyse=self.analyse,
            type_analyse=self.type_glyc,
            valeur=0.30, unite='g/L'
        )
        self.assertEqual(r.flag, 'C')


class AlerteCritiqueTest(TestCase):
    """Tests de l'alerte automatique sur valeur critique."""

    def setUp(self):
        self.user = User.objects.create_user('t', 't@e.com', 'Sup3rStr0ngPass!')
        self.patient = Patient.objects.create(
            user=self.user, nom='T', prenom='U',
            email='t@e.com', telephone='1',
            date_naissance='1990-01-01', adresse='L',
            patient_id='ATEST002',
        )
        self.type_k = TypeAnalyse.objects.create(
            code='K', nom='Kaliemie', categorie='biochimie',
            unite='mmol/L',
            normale_basse_defaut=3.5,
            normale_haute_defaut=5.0,
            seuil_critique_haute=6.5,
        )
        self.analyse = Analyse.objects.create(
            patient=self.patient,
            type_analyse='sang',
            laboratoire='Labo',
            date='2026-01-01',
            statut='disponible',
        )

    def test_valeur_critique_marque_analyse(self):
        """Une valeur critique doit marquer l'analyse parente est_critique=True."""
        ResultatAnalyse.objects.create(
            analyse=self.analyse,
            type_analyse=self.type_k,
            valeur=7.0, unite='mmol/L'
        )
        self.analyse.refresh_from_db()
        self.assertTrue(self.analyse.est_critique)
        self.assertEqual(self.analyse.statut, 'critique')


class ReferenceAnalyseTest(TestCase):
    """Tests du référentiel de normes par âge/sexe."""

    def setUp(self):
        self.type_hb = TypeAnalyse.objects.create(
            code='HB', nom='Hemoglobine', categorie='hematologie',
            unite='g/dL',
            normale_basse_defaut=12.0,
            normale_haute_defaut=16.0,
        )
        # Normes affinées pour femme enceinte
        ReferenceAnalyse.objects.create(
            type_analyse=self.type_hb,
            sexe='F', age_min=18, age_max=45,
            normale_basse=10.5, normale_haute=14.0,
            description='Femme enceinte',
        )

    def test_reference_creee_correctement(self):
        ref = ReferenceAnalyse.objects.get(type_analyse=self.type_hb)
        self.assertEqual(ref.normale_basse, 10.5)
        self.assertEqual(ref.normale_haute, 14.0)
        self.assertEqual(ref.sexe, 'F')
