from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Patient
import random


def _est_super_admin(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel is None or personnel.role == 'super_admin'


def _hopital_personnel(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel.hopital if personnel else None


@login_required
def liste_patients(request):
    recherche = request.GET.get('q', '')
    statut = request.GET.get('statut', '')

    if _est_super_admin(request):
        patients_qs = Patient.objects.all()
    else:
        patients_qs = Patient.objects.filter(hopital=_hopital_personnel(request))

    patients = patients_qs

    if recherche:
        patients = patients.filter(
            Q(nom__icontains=recherche) |
            Q(prenom__icontains=recherche) |
            Q(email__icontains=recherche) |
            Q(patient_id__icontains=recherche)
        )
    if statut == 'critique':
        patients = patients.filter(est_critique=True)
    elif statut == 'stable':
        patients = patients.filter(est_critique=False)

    context = {
        'patients': patients,
        'total': patients_qs.count(),
        'stables': patients_qs.filter(est_critique=False).count(),
        'urgences': patients_qs.filter(est_critique=True).count(),
        'recherche': recherche,
        'statut': statut,
    }
    return render(request, 'patients/liste.html', context)


@login_required
def detail_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)

    # Sécurité : un admin d'hôpital ne peut pas voir un patient d'un autre hôpital
    if not _est_super_admin(request) and patient.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    try:
        from dossiers_medicaux.models import DossierMedical
        dossier = DossierMedical.objects.get(patient=patient)
    except:
        dossier = None
    return render(request, 'patients/detail.html', {
        'patient': patient,
        'dossier': dossier,
    })


@login_required
def voir_dossier_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)

    if not _est_super_admin(request) and patient.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    try:
        from dossiers_medicaux.models import DossierMedical
        dossier = DossierMedical.objects.get(patient=patient)
        return redirect('dossiers_medicaux:detail', pk=dossier.pk)
    except:
        from dossiers_medicaux.models import DossierMedical
        dossier = DossierMedical.objects.create(patient=patient)
        return redirect('dossiers_medicaux:detail', pk=dossier.pk)


@login_required
def ajouter_patient(request):
    if request.method == 'POST':
        patient_id = f"KM{random.randint(2026000, 2026999)}"

        # Si admin d'hôpital, le patient créé est automatiquement rattaché à son hôpital
        hopital = None if _est_super_admin(request) else _hopital_personnel(request)

        patient = Patient.objects.create(
            nom=request.POST.get('nom'),
            prenom=request.POST.get('prenom'),
            email=request.POST.get('email'),
            telephone=request.POST.get('telephone'),
            date_naissance=request.POST.get('date_naissance'),
            adresse=request.POST.get('adresse'),
            groupe_sanguin=request.POST.get('groupe_sanguin', 'O+'),
            allergies=request.POST.get('allergies', 'Aucune'),
            poids=request.POST.get('poids') or 0,
            taille=request.POST.get('taille') or 0,
            patient_id=patient_id,
            hopital=hopital,
        )
        return redirect('patients:liste')
    return render(request, 'patients/ajouter.html')


@login_required
def modifier_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)

    if not _est_super_admin(request) and patient.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    if request.method == 'POST':
        patient.nom = request.POST.get('nom', patient.nom)
        patient.prenom = request.POST.get('prenom', patient.prenom)
        patient.email = request.POST.get('email', patient.email)
        patient.telephone = request.POST.get('telephone', patient.telephone)
        patient.adresse = request.POST.get('adresse', patient.adresse)
        patient.groupe_sanguin = request.POST.get('groupe_sanguin', patient.groupe_sanguin)
        patient.allergies = request.POST.get('allergies', patient.allergies)
        patient.poids = request.POST.get('poids') or patient.poids
        patient.taille = request.POST.get('taille') or patient.taille
        patient.est_critique = request.POST.get('est_critique') == 'on'
        patient.save()
        return redirect('patients:liste')
    return render(request, 'patients/modifier.html', {'patient': patient})


@login_required
def supprimer_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)

    if not _est_super_admin(request) and patient.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    if request.method == 'POST':
        patient.delete()
    return redirect('patients:liste')