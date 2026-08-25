from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from django.utils import timezone
from .models import Consultation
from patients.models import Patient
from appointments.models import Medecin


def _est_super_admin(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel is None or personnel.role == 'super_admin'


def _hopital_personnel(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel.hopital if personnel else None


@login_required
def liste_consultations(request):
    today = timezone.now().date()
    recherche = request.GET.get('q', '')
    statut = request.GET.get('statut', '')

    if _est_super_admin(request):
        consultations_qs = Consultation.objects.all()
    else:
        consultations_qs = Consultation.objects.filter(
            patient__hopital=_hopital_personnel(request)
        )

    consultations = consultations_qs.select_related('patient', 'medecin')

    if recherche:
        consultations = consultations.filter(
            Q(patient__nom__icontains=recherche) |
            Q(patient__prenom__icontains=recherche) |
            Q(medecin__nom__icontains=recherche) |
            Q(consultation_id__icontains=recherche)
        )
    if statut:
        consultations = consultations.filter(statut=statut)

    context = {
        'consultations': consultations,
        'total': consultations_qs.count(),
        'en_attente': consultations_qs.filter(statut='en_attente').count(),
        'en_cours': consultations_qs.filter(
            statut='en_cours', date=today
        ).count(),
        'terminees': consultations_qs.filter(statut='terminee').count(),
        'reportees': consultations_qs.filter(statut='reportee').count(),
        'annulees': consultations_qs.filter(statut='annulee').count(),
        'recherche': recherche,
        'statut_filtre': statut,
    }
    return render(request, 'consultations/liste.html', context)


@login_required
def detail_consultation(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)

    if not _est_super_admin(request) and consultation.patient.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    return render(request, 'consultations/detail.html', {'consultation': consultation})


@login_required
def ajouter_consultation(request):
    if request.method == 'POST':
        Consultation.objects.create(
            patient=get_object_or_404(Patient, pk=request.POST.get('patient')),
            medecin=get_object_or_404(Medecin, pk=request.POST.get('medecin')),
            date=request.POST.get('date'),
            heure=request.POST.get('heure'),
            motif=request.POST.get('motif'),
            type_consultation=request.POST.get('type_consultation', ''),
            cout=request.POST.get('cout', 0),
            statut='en_attente',
        )
        return redirect('consultations:liste')

    if _est_super_admin(request):
        patients_qs = Patient.objects.all()
    else:
        patients_qs = Patient.objects.filter(hopital=_hopital_personnel(request))

    context = {
        'patients': patients_qs,
        'medecins': Medecin.objects.all(),
    }
    return render(request, 'consultations/ajouter.html', context)


@login_required
def modifier_statut(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)

    if not _est_super_admin(request) and consultation.patient.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    if request.method == 'POST':
        consultation.statut = request.POST.get('statut')
        consultation.diagnostic = request.POST.get('diagnostic', '')
        consultation.notes = request.POST.get('notes', '')
        consultation.save()
        return redirect('consultations:liste')
    return render(request, 'consultations/modifier.html', {'consultation': consultation})