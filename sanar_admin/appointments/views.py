from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from .models import RendezVous, Medecin
from patients.models import Patient


def _est_super_admin(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel is None or personnel.role == 'super_admin'


def _hopital_personnel(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel.hopital if personnel else None


@login_required
def liste_appointments(request):
    today = timezone.now().date()
    recherche = request.GET.get('q', '')
    statut = request.GET.get('statut', '')
    date_filtre = request.GET.get('date', '')

    if _est_super_admin(request):
        rdvs_qs = RendezVous.objects.all()
    else:
        rdvs_qs = RendezVous.objects.filter(hopital=_hopital_personnel(request))

    rdvs = rdvs_qs.select_related('patient', 'medecin')

    if recherche:
        rdvs = rdvs.filter(
            Q(patient__nom__icontains=recherche) |
            Q(patient__prenom__icontains=recherche) |
            Q(medecin__nom__icontains=recherche)
        )
    if statut:
        rdvs = rdvs.filter(statut=statut)
    if date_filtre:
        rdvs = rdvs.filter(date=date_filtre)

    context = {
        'rdvs': rdvs,
        'total': rdvs_qs.count(),
        'en_attente': rdvs_qs.filter(statut='en_attente').count(),
        'reportes': rdvs_qs.filter(statut='reporte').count(),
        'annules': rdvs_qs.filter(statut='annule').count(),
        'confirmes': rdvs_qs.filter(statut='confirme').count(),
        'recherche': recherche,
        'statut_filtre': statut,
        'date_filtre': date_filtre,
    }
    return render(request, 'appointments/liste.html', context)


@login_required
def detail_appointment(request, pk):
    rdv = get_object_or_404(RendezVous, pk=pk)

    if not _est_super_admin(request) and rdv.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    return render(request, 'appointments/detail.html', {'rdv': rdv})


@login_required
def ajouter_appointment(request):
    if request.method == 'POST':
        medecin = Medecin.objects.first()
        hopital = None if _est_super_admin(request) else _hopital_personnel(request)
        RendezVous.objects.create(
            patient=get_object_or_404(Patient, pk=request.POST.get('patient')),
            medecin=medecin,
            hopital=hopital,
            date=request.POST.get('date'),
            heure=request.POST.get('heure'),
            motif=request.POST.get('motif'),
            note=request.POST.get('note', ''),
            statut='en_attente',
        )
        return redirect('appointments:liste')

    if _est_super_admin(request):
        patients_qs = Patient.objects.all()
    else:
        patients_qs = Patient.objects.filter(hopital=_hopital_personnel(request))

    context = {
        'patients': patients_qs,
    }
    return render(request, 'appointments/ajouter.html', context)


@login_required
def modifier_statut(request, pk):
    rdv = get_object_or_404(RendezVous, pk=pk)

    if not _est_super_admin(request) and rdv.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    if request.method == 'POST':
        rdv.statut = request.POST.get('statut')
        rdv.note = request.POST.get('note', '')
        rdv.save()
        return redirect('appointments:liste')
    return render(request, 'appointments/modifier.html', {'rdv': rdv})