"""Vues Django (admin templates) pour le module urgences."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import DemandeUrgence, AccesUrgence


def _est_super_admin(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel is None or personnel.role == 'super_admin'


def _hopital_personnel(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel.hopital if personnel else None


@login_required
def liste_urgences(request):
    """Liste des demandes d'urgence (filtrée par hôpital pour admin_hopital)."""
    if _est_super_admin(request):
        urgences = DemandeUrgence.objects.select_related(
            'patient', 'hopital_destine', 'assigne_a'
        ).all()
    else:
        hopital = _hopital_personnel(request)
        urgences = DemandeUrgence.objects.filter(hopital_destine=hopital)

    statut_filtre = request.GET.get('statut', '')
    if statut_filtre:
        urgences = urgences.filter(statut=statut_filtre)

    context = {
        'urgences': urgences,
        'en_attente': urgences.filter(statut='en_attente').count(),
        'en_route': urgences.filter(statut='en_route').count(),
        'pris_en_charge': urgences.filter(statut='pris_en_charge').count(),
        'temps_moyen_reponse': _calculer_temps_moyen_reponse(urgences),
        'statut_filtre': statut_filtre,
    }
    return render(request, 'urgences/liste.html', context)


@login_required
def detail_urgence(request, uuid):
    """Détail d'une demande d'urgence + actions (assigner, prendre en charge)."""
    urgence = get_object_or_404(DemandeUrgence, uuid=uuid)

    if not _est_super_admin(request):
        hopital = _hopital_personnel(request)
        if urgence.hopital_destine != hopital:
            return render(request, 'patients/acces_refuse.html', status=403)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'prendre_en_charge':
            urgence.statut = 'pris_en_charge'
            urgence.pris_en_charge_at = timezone.now()
            urgence.assigne_a = request.user
            urgence.temps_reponse = urgence.duree_attente_seconds or 0
            urgence.save()
            messages.success(request, "Urgence marquée comme prise en charge.")
        elif action == 'en_route':
            urgence.statut = 'en_route'
            urgence.assigne_a = request.user
            urgence.save()
            messages.success(request, "Statut mis à jour : secours en route.")
        elif action == 'annuler':
            urgence.statut = 'annulee'
            urgence.save()
            messages.info(request, "Demande d'urgence annulée.")
        return redirect('urgences:detail', uuid=urgence.uuid)

    return render(request, 'urgences/detail.html', {'urgence': urgence})


@login_required
def audit_acces_urgence(request):
    """Journal d'audit RGPD des accès d'urgence par QR code."""
    if not _est_super_admin(request):
        hopital = _hopital_personnel(request)
        acces = AccesUrgence.objects.filter(
            patient__hopital=hopital
        ).select_related('patient')[:200]
    else:
        acces = AccesUrgence.objects.select_related('patient')[:200]

    context = {'acces': acces, 'total_24h': AccesUrgence.objects.filter(
        created_at__gte=timezone.now() - timezone.timedelta(hours=24)
    ).count()}
    return render(request, 'urgences/audit.html', context)


def _calculer_temps_moyen_reponse(urgences_qs):
    """KPI : temps moyen (secondes) déclenchement → prise en charge."""
    from django.db.models import Avg
    resultat = urgences_qs.filter(
        statut='pris_en_charge',
        temps_reponse__isnull=False
    ).aggregate(Avg('temps_reponse'))
    return int(resultat['temps_reponse__avg']) if resultat['temps_reponse__avg'] else 0
