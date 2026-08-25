"""Vues pour les exports (interface admin HTML)."""
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages

from patients.models import Patient
from .services import export_dossier_pdf, export_patients_csv, export_dossier_fhir


def _est_super_admin(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel is None or personnel.role == 'super_admin'


@login_required
def export_pdf(request, patient_pk):
    """Téléchargement PDF du dossier d'un patient."""
    patient = get_object_or_404(Patient, pk=patient_pk)
    pdf_bytes = export_dossier_pdf(patient)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="dossier_{patient.patient_id}.pdf"'
    )
    messages.info(request, f"PDF généré pour {patient}")
    return response


@login_required
def export_csv(request):
    """Export CSV agrégé (super_admin uniquement)."""
    if not _est_super_admin(request):
        return HttpResponse("Accès réservé super admin", status=403)
    csv_content = export_patients_csv()
    response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="patients_export.csv"'
    return response


@login_required
def export_fhir(request, patient_pk):
    """Export FHIR R4 (JSON) du dossier patient."""
    patient = get_object_or_404(Patient, pk=patient_pk)
    bundle = export_dossier_fhir(patient)
    response = JsonResponse(bundle, json_dumps_params={'indent': 2, 'ensure_ascii': False})
    response['Content-Disposition'] = (
        f'attachment; filename="fhir_{patient.patient_id}.json"'
    )
    return response
