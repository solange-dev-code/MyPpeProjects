"""
Services d'export de dossiers médicaux.

Trois formats pris en charge :
- PDF (WeasyPrint) : compte-rendu lisible par un humain
- CSV : statistiques agrégées pour analyse
- FHIR R4 (JSON) : interopérabilité avec SIH tiers
"""
import csv
import io
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from django.template.loader import render_to_string

from patients.models import Patient
from dossiers_medicaux.models import DossierMedical
from consultations.models import Consultation
from analyses.models import Analyse, ResultatAnalyse
from facturation.models import Facture
from messagerie.models import Conversation

logger = logging.getLogger('sanar.exports')


# ──────────────────────────────────────────────────────────────
# 1. Export PDF du dossier complet (WeasyPrint)
# ──────────────────────────────────────────────────────────────
def export_dossier_pdf(patient: Patient) -> bytes:
    """Génère un PDF complet du dossier médical d'un patient.

    Structure :
    - Page de garde (identité, médecin référent, date d'édition)
    - Résumé clinique (ATCD, traitements, allergies)
    - Historique des consultations
    - Liste des prescriptions actives
    - Liste des analyses avec résultats
    - Liste des documents attachés

    Retourne les bytes du PDF.
    """
    dossier = DossierMedical.objects.get(patient=patient)
    consultations = Consultation.objects.filter(patient=patient).order_by('-date')
    prescriptions = dossier.prescriptions.all().order_by('-date_prescription')
    analyses = Analyse.objects.filter(patient=patient).order_by('-date')
    documents = dossier.documents.all().order_by('-created_at')
    factures = Facture.objects.filter(patient=patient).order_by('-date_facture')

    context = {
        'patient': patient,
        'dossier': dossier,
        'consultations': consultations,
        'prescriptions': prescriptions,
        'analyses': analyses,
        'documents': documents,
        'factures': factures,
        'date_edition': datetime.now(),
    }

    html = render_to_string('exports/dossier_pdf.html', context)

    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html).write_pdf()
        logger.info("PDF généré pour patient %s (%d octets)",
                    patient.patient_id, len(pdf_bytes))
        return pdf_bytes
    except ImportError:
        logger.warning("WeasyPrint non disponible, fallback reportlab")
        return _export_pdf_reportlab_fallback(html, context)
    except Exception as e:
        logger.error("Échec génération PDF WeasyPrint : %s", e)
        return _export_pdf_reportlab_fallback(html, context)


def _export_pdf_reportlab_fallback(html, context):
    """Fallback simple avec reportlab si WeasyPrint indisponible."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle)
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Police
    try:
        pdfmetrics.registerFont(TTFont(
            'NotoSerifSC',
            '/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-Regular.ttf'
        ))
        font = 'NotoSerifSC'
    except Exception:
        font = 'Helvetica'

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    styles['Title'].fontName = font
    styles['Normal'].fontName = font

    p = context['patient']
    story = [
        Paragraph(f"Dossier médical — {p.prenom} {p.nom}", styles['Title']),
        Spacer(1, 12),
        Paragraph(f"<b>Patient ID :</b> {p.patient_id}", styles['Normal']),
        Paragraph(f"<b>Date de naissance :</b> {p.date_naissance}", styles['Normal']),
        Paragraph(f"<b>Groupe sanguin :</b> {p.groupe_sanguin}", styles['Normal']),
        Paragraph(f"<b>Allergies :</b> {p.allergies}", styles['Normal']),
        Spacer(1, 8),
        Paragraph(f"<b>Antécédents :</b> {context['dossier'].antecedents}", styles['Normal']),
        Spacer(1, 8),
        Paragraph(f"<b>Traitements en cours :</b> {context['dossier'].traitements_en_cours}", styles['Normal']),
        Spacer(1, 12),
        Paragraph(f"<i>Document généré le {context['date_edition']:%d/%m/%Y %H:%M}</i>",
                  styles['Normal']),
    ]
    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# ──────────────────────────────────────────────────────────────
# 2. Export CSV pour statistiques
# ──────────────────────────────────────────────────────────────
def export_patients_csv() -> str:
    """Export CSV agrégé des patients pour statistiques.

    Réservé super_admin. Anonymise partiellement les données
    (pas de nom/prénom/email/téléphone — uniquement âge, sexe, stats).
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        'patient_id', 'age', 'groupe_sanguin', 'hopital',
        'nb_consultations', 'nb_analyses', 'est_critique',
        'date_inscription'
    ])

    from django.db.models import Count
    from datetime import date
    today = date.today()
    for p in Patient.objects.select_related('hopital').annotate(
        nb_consultations=Count('consultation'),
        nb_analyses=Count('analyses'),
    ):
        age = today.year - p.date_naissance.year - (
            (today.month, today.day) < (p.date_naissance.month, p.date_naissance.day)
        )
        writer.writerow([
            p.patient_id,
            age,
            p.groupe_sanguin,
            p.hopital.nom if p.hopital else '',
            p.nb_consultations,
            p.nb_analyses,
            int(p.est_critique),
            p.date_inscription.strftime('%Y-%m-%d'),
        ])

    logger.info("Export CSV de %d patients généré", Patient.objects.count())
    return output.getvalue()


# ──────────────────────────────────────────────────────────────
# 3. Export FHIR R4 (JSON) pour interopérabilité SIH
# ──────────────────────────────────────────────────────────────
def export_dossier_fhir(patient: Patient) -> Dict:
    """Génère un Bundle FHIR R4 contenant le dossier complet du patient.

    Resources FHIR générées :
    - Patient (identité)
    - Condition (antécédents)
    - MedicationRequest (prescriptions actives)
    - Observation (résultats d'analyses)
    - Encounter (consultations)

    Conforme au standard HL7 FHIR R4 (https://hl7.org/fhir/R4/).
    """
    bundle = {
        'resourceType': 'Bundle',
        'id': f'bundle-{patient.patient_id}',
        'type': 'collection',
        'meta': {
            'lastUpdated': datetime.now().isoformat() + 'Z',
            'profile': ['http://hl7.org/fhir/StructureDefinition/Bundle']
        },
        'entry': []
    }

    # 1. Patient
    bundle['entry'].append({
        'fullUrl': f'urn:uuid:patient-{patient.patient_id}',
        'resource': _patient_to_fhir(patient)
    })

    # 2. Conditions (antécédents)
    try:
        dossier = DossierMedical.objects.get(patient=patient)
        if dossier.antecedents:
            for antecedent in _split_lignes(dossier.antecedents):
                bundle['entry'].append({
                    'fullUrl': f'urn:uuid:condition-{patient.patient_id}-{hash(antecedent) & 0xFFFFFF}',
                    'resource': {
                        'resourceType': 'Condition',
                        'subject': {'reference': f'urn:uuid:patient-{patient.patient_id}'},
                        'clinicalStatus': {
                            'coding': [{
                                'system': 'http://terminology.hl7.org/CodeSystem/condition-clinical',
                                'code': 'active'
                            }]
                        },
                        'note': [{'text': antecedent}]
                    }
                })
    except DossierMedical.DoesNotExist:
        pass

    # 3. MedicationRequest (prescriptions actives)
    try:
        for prescription in dossier.prescriptions.filter(est_active=True):
            bundle['entry'].append({
                'fullUrl': f'urn:uuid:medication-{prescription.id}',
                'resource': {
                    'resourceType': 'MedicationRequest',
                    'status': 'active',
                    'intent': 'order',
                    'subject': {'reference': f'urn:uuid:patient-{patient.patient_id}'},
                    'medicationCodeableConcept': {'text': prescription.medicament},
                    'dosageInstruction': [{
                        'text': f"{prescription.posologie} pendant {prescription.duree}"
                    }],
                    'authoredOn': prescription.date_prescription.isoformat()
                }
            })
    except Exception:
        pass

    # 4. Observations (résultats d'analyses)
    for analyse in Analyse.objects.filter(patient=patient):
        for resultat in analyse.resultats.all():
            bundle['entry'].append({
                'fullUrl': f'urn:uuid:observation-{resultat.id}',
                'resource': {
                    'resourceType': 'Observation',
                    'status': 'final',
                    'subject': {'reference': f'urn:uuid:patient-{patient.patient_id}'},
                    'effectiveDateTime': analyse.date.isoformat(),
                    'code': {
                        'coding': [{
                            'system': 'http://loinc.org',
                            'display': resultat.type_analyse.nom
                        }]
                    },
                    'valueQuantity': {
                        'value': resultat.valeur,
                        'unit': resultat.unite,
                        'system': 'http://unitsofmeasure.org'
                    },
                    'interpretation': [{
                        'coding': [{
                            'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation',
                            'code': resultat.flag
                        }]
                    }]
                }
            })

    # 5. Encounters (consultations)
    for consultation in Consultation.objects.filter(patient=patient):
        bundle['entry'].append({
            'fullUrl': f'urn:uuid:encounter-{consultation.id}',
            'resource': {
                'resourceType': 'Encounter',
                'status': 'finished',
                'class': {
                    'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode',
                    'code': 'AMB'
                },
                'subject': {'reference': f'urn:uuid:patient-{patient.patient_id}'},
                'period': {'start': consultation.date.isoformat()},
                'reasonCode': [{'text': consultation.motif}],
                'diagnosis': [{
                    'condition': {'display': consultation.diagnostic}
                }] if consultation.diagnostic else []
            }
        })

    logger.info("Bundle FHIR généré pour patient %s (%d resources)",
                patient.patient_id, len(bundle['entry']))
    return bundle


def _patient_to_fhir(patient: Patient) -> Dict:
    """Convertit un Patient Django en resource FHIR Patient R4."""
    return {
        'resourceType': 'Patient',
        'identifier': [{
            'system': 'https://sanar.app/patient-id',
            'value': patient.patient_id
        }],
        'name': [{
            'use': 'official',
            'family': patient.nom,
            'given': [patient.prenom]
        }],
        'telecom': [
            {'system': 'phone', 'value': patient.telephone},
            {'system': 'email', 'value': patient.email},
        ],
        'gender': 'unknown',  # non stocké actuellement
        'birthDate': patient.date_naissance.isoformat(),
        'address': [{
            'line': [patient.adresse],
            'city': patient.hopital.ville if patient.hopital else ''
        }],
        'extension': [{
            'url': 'https://sanar.app/fhir/StructureDefinition/blood-type',
            'valueString': patient.groupe_sanguin
        }]
    }


def _split_lignes(texte: str) -> List[str]:
    """Découpe un texte en lignes non vides."""
    return [l.strip() for l in texte.splitlines() if l.strip()]
