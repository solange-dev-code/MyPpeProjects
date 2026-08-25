"""Vues Django pour la file d'attente (interface admin)."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import FileAttente
from .services import (
    ordre_passage, marquer_en_consultation, marquer_termine,
    marquer_abandonne, recalculer_estimations
)


def _est_super_admin(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel is None or personnel.role == 'super_admin'


def _hopital_personnel(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel.hopital if personnel else None


@login_required
def liste_file_attente(request):
    """Vue temps réel de la file d'attente de l'hôpital."""
    if _est_super_admin(request):
        hopital = None
        files = FileAttente.objects.filter(statut='en_attente').select_related(
            'patient', 'medecin', 'hopital'
        ).order_by('hopital', 'niveau_triage', 'arrivee_at')
    else:
        hopital = _hopital_personnel(request)
        files = FileAttente.objects.filter(
            hopital=hopital, statut='en_attente'
        ).select_related('patient', 'medecin').order_by(
            'niveau_triage', 'arrivee_at'
        )

    en_consultation = FileAttente.objects.filter(
        statut='en_consultation',
        **({'hopital': hopital} if hopital else {})
    ).select_related('patient', 'medecin')

    context = {
        'files': files,
        'en_consultation': en_consultation,
        'hopital': hopital,
        'total_en_attente': files.count(),
        'p1_count': files.filter(niveau_triage=1).count(),
        'p2_count': files.filter(niveau_triage=2).count(),
    }
    return render(request, 'file_attente/liste.html', context)


@login_required
def action_file(request, file_id, action):
    """Actions sur une entrée de file (consultation, terminer, abandonner)."""
    file_entry = get_object_or_404(FileAttente, pk=file_id)

    if not _est_super_admin(request):
        if file_entry.hopital != _hopital_personnel(request):
            return render(request, 'patients/acces_refuse.html', status=403)

    if action == 'consulter':
        marquer_en_consultation(file_id, medecin_id=None)
        messages.success(request, f"{file_entry.patient} en consultation.")
    elif action == 'terminer':
        marquer_termine(file_id)
        messages.success(request, f"Consultation de {file_entry.patient} terminée.")
    elif action == 'abandonner':
        marquer_abandonne(file_id)
        messages.info(request, f"{file_entry.patient} a abandonné la file.")

    return redirect('file_attente:liste')


@login_required
def recalculer(request):
    """Recalcule les temps estimés pour l'hôpital courant."""
    if _est_super_admin(request):
        messages.warning(request, "Le super admin doit spécifier un hôpital.")
        return redirect('file_attente:liste')
    hopital = _hopital_personnel(request)
    updated = recalculer_estimations(hopital.id)
    messages.success(request, f"{updated} estimations recalculées.")
    return redirect('file_attente:liste')
