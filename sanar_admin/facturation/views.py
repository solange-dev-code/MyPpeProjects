from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.utils import timezone
from .models import Facture
from patients.models import Patient
from appointments.models import Medecin


def _est_super_admin(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel is None or personnel.role == 'super_admin'


def _hopital_personnel(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel.hopital if personnel else None


@login_required
def liste_factures(request):
    recherche = request.GET.get('q', '')
    statut = request.GET.get('statut', '')

    if _est_super_admin(request):
        factures_qs = Facture.objects.all()
    else:
        factures_qs = Facture.objects.filter(patient__hopital=_hopital_personnel(request))

    factures = factures_qs.select_related('patient', 'medecin')

    if recherche:
        factures = factures.filter(
            Q(patient__nom__icontains=recherche) |
            Q(patient__prenom__icontains=recherche) |
            Q(facture_id__icontains=recherche) |
            Q(description__icontains=recherche)
        )
    if statut:
        factures = factures.filter(statut=statut)

    total_facture = factures_qs.aggregate(t=Sum('montant_total'))['t'] or 0
    encaisse = factures_qs.filter(statut='payee').aggregate(t=Sum('part_patient'))['t'] or 0
    part_assurance = factures_qs.filter(statut='payee').aggregate(t=Sum('part_assurance'))['t'] or 0
    reste = total_facture - encaisse - part_assurance

    context = {
        'factures': factures,
        'total_facture': total_facture,
        'encaisse': encaisse,
        'part_assurance': part_assurance,
        'reste': reste,
        'recherche': recherche,
        'statut_filtre': statut,
        'derniers_paiements': factures_qs.filter(
            statut='payee'
        ).order_by('-date_paiement')[:5],
    }
    return render(request, 'facturation/liste.html', context)


@login_required
def detail_facture(request, pk):
    facture = get_object_or_404(Facture, pk=pk)

    if not _est_super_admin(request) and facture.patient.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    return render(request, 'facturation/detail.html', {'facture': facture})


@login_required
def ajouter_facture(request):
    if _est_super_admin(request):
        patients_qs = Patient.objects.all()
    else:
        patients_qs = Patient.objects.filter(hopital=_hopital_personnel(request))

    if request.method == 'POST':
        patient_id = request.POST.get('patient', '').strip()

        if not patient_id:
            from django.contrib import messages
            messages.error(request, 'Veuillez sélectionner un patient.')
            context = {'patients': patients_qs}
            return render(request, 'facturation/ajouter.html', context)

        patient = get_object_or_404(Patient, pk=patient_id)

        # Sécurité : un admin d'hôpital ne peut pas facturer un patient d'un autre hôpital
        if not _est_super_admin(request) and patient.hopital != _hopital_personnel(request):
            return render(request, 'patients/acces_refuse.html', status=403)

        montant_total = float(request.POST.get('montant_total', 0))
        part_assurance = float(request.POST.get('part_assurance', 0))
        part_patient = montant_total - part_assurance
        Facture.objects.create(
            patient=patient,
            description=request.POST.get('description'),
            montant_total=montant_total,
            part_patient=part_patient,
            part_assurance=part_assurance,
            statut='en_attente',
        )
        return redirect('facturation:liste')

    context = {'patients': patients_qs}
    return render(request, 'facturation/ajouter.html', context)


@login_required
def marquer_paye(request, pk):
    facture = get_object_or_404(Facture, pk=pk)

    if not _est_super_admin(request) and facture.patient.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    if request.method == 'POST':
        facture.statut = request.POST.get('statut', 'payee')
        facture.moyen_paiement = request.POST.get('moyen_paiement', '')
        facture.date_paiement = timezone.now().date()
        facture.save()
        return redirect('facturation:liste')
    return render(request, 'facturation/payer.html', {'facture': facture})


@login_required
def supprimer_facture(request, pk):
    facture = get_object_or_404(Facture, pk=pk)

    if not _est_super_admin(request) and facture.patient.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    if request.method == 'POST':
        facture.delete()
    return redirect('facturation:liste')