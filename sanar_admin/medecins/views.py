from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Medecin
from appointments.models import RendezVous
from consultations.models import Consultation


def _est_super_admin(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel is None or personnel.role == 'super_admin'


def _hopital_personnel(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel.hopital if personnel else None


@login_required
def liste_medecins(request):
    recherche = request.GET.get('q', '')
    specialite = request.GET.get('specialite', '')

    if _est_super_admin(request):
        medecins_qs = Medecin.objects.all()
    else:
        medecins_qs = Medecin.objects.filter(hopital=_hopital_personnel(request))

    medecins = medecins_qs

    if recherche:
        medecins = medecins.filter(
            Q(nom__icontains=recherche) |
            Q(prenom__icontains=recherche) |
            Q(specialite__icontains=recherche) |
            Q(cabinet__icontains=recherche)
        )
    if specialite:
        medecins = medecins.filter(specialite=specialite)

    context = {
        'medecins': medecins,
        'total': medecins_qs.count(),
        'actifs': medecins_qs.filter(est_actif=True).count(),
        'inactifs': medecins_qs.filter(est_actif=False).count(),
        'recherche': recherche,
        'specialite_filtre': specialite,
        'specialites': Medecin.SPECIALITE_CHOICES,
    }
    return render(request, 'medecins/liste.html', context)


@login_required
def detail_medecin(request, pk):
    medecin = get_object_or_404(Medecin, pk=pk)

    if not _est_super_admin(request) and medecin.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    rdvs = RendezVous.objects.filter(
        medecin=medecin
    ).order_by('-date')[:5]
    consultations = Consultation.objects.filter(
        medecin=medecin
    ).order_by('-date')[:5]
    context = {
        'medecin': medecin,
        'rdvs': rdvs,
        'consultations': consultations,
        'total_rdvs': RendezVous.objects.filter(medecin=medecin).count(),
        'total_consultations': Consultation.objects.filter(medecin=medecin).count(),
    }
    return render(request, 'medecins/detail.html', context)


@login_required
def ajouter_medecin(request):
    if request.method == 'POST':
        hopital = None if _est_super_admin(request) else _hopital_personnel(request)
        Medecin.objects.create(
            nom=request.POST.get('nom'),
            prenom=request.POST.get('prenom'),
            specialite=request.POST.get('specialite'),
            telephone=request.POST.get('telephone'),
            email=request.POST.get('email', ''),
            cabinet=request.POST.get('cabinet', ''),
            hopital=hopital,
        )
        return redirect('medecins:liste')
    return render(request, 'medecins/ajouter.html')


@login_required
def modifier_medecin(request, pk):
    medecin = get_object_or_404(Medecin, pk=pk)

    if not _est_super_admin(request) and medecin.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    if request.method == 'POST':
        medecin.nom = request.POST.get('nom')
        medecin.prenom = request.POST.get('prenom')
        medecin.specialite = request.POST.get('specialite')
        medecin.telephone = request.POST.get('telephone')
        medecin.email = request.POST.get('email', '')
        medecin.cabinet = request.POST.get('cabinet', '')
        medecin.est_actif = request.POST.get('est_actif') == 'on'
        medecin.save()
        return redirect('medecins:liste')
    return render(request, 'medecins/modifier.html', {'medecin': medecin})


@login_required
def supprimer_medecin(request, pk):
    medecin = get_object_or_404(Medecin, pk=pk)

    if not _est_super_admin(request) and medecin.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    if request.method == 'POST':
        medecin.delete()
    return redirect('medecins:liste')