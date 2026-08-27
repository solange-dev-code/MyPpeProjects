"""
Vues dossiers médicaux — Nouvelle logique d'accès :
- super_admin : voit tous les dossiers
- admin_hopital : voit UNIQUEMENT les dossiers des patients qui ont
  pris au moins un RDV dans SON hôpital
- médecin : voit les dossiers des patients dont il a confirmé un RDV
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Exists, OuterRef
from django.contrib import messages
from .models import DossierMedical, Prescription, Document
from patients.models import Patient
from appointments.models import RendezVous
from analyses.models import Analyse


def _est_super_admin(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel is None or personnel.role == 'super_admin'


def _est_admin_hopital(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel is not None and personnel.role == 'admin_hopital' and personnel.hopital is not None


def _est_medecin(request):
    return hasattr(request.user, 'medecin_profile')


def _hopital_personnel(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel.hopital if personnel else None


def _patient_a_rdv_dans_hopital(patient, hopital):
    """Vérifie qu'un patient a au moins un RDV dans l'hôpital donné."""
    return RendezVous.objects.filter(
        patient=patient, hopital=hopital
    ).exists()


@login_required
def liste_dossiers(request):
    """Liste des dossiers médicaux avec contrôle d'accès.

    - super_admin : tous les dossiers
    - admin_hopital : UNIQUEMENT les patients ayant pris RDV dans son hôpital
    - médecin : UNIQUEMENT les patients dont il a un RDV confirmé
    """
    recherche = request.GET.get('q', '')
    statut = request.GET.get('statut', '')

    if _est_super_admin(request):
        dossiers = DossierMedical.objects.all().select_related(
            'patient', 'medecin_referent'
        )
    elif _est_admin_hopital(request):
        hopital = _hopital_personnel(request)
        # Uniquement les patients qui ont pris au moins un RDV dans cet hôpital
        dossiers = DossierMedical.objects.filter(
            Exists(
                RendezVous.objects.filter(
                    patient=OuterRef('patient'),
                    hopital=hopital
                )
            )
        ).select_related('patient', 'medecin_referent')
    elif _est_medecin(request):
        medecin = request.user.medecin_profile
        # Uniquement les patients dont le médecin a un RDV
        dossiers = DossierMedical.objects.filter(
            Exists(
                RendezVous.objects.filter(
                    patient=OuterRef('patient'),
                    medecin=medecin
                )
            )
        ).select_related('patient', 'medecin_referent')
    else:
        return render(request, 'patients/acces_refuse.html', status=403)

    if recherche:
        dossiers = dossiers.filter(
            Q(patient__nom__icontains=recherche) |
            Q(patient__prenom__icontains=recherche)
        )
    if statut:
        dossiers = dossiers.filter(statut=statut)

    services = {}
    for dossier in dossiers:
        if dossier.medecin_referent:
            spec = dossier.medecin_referent.get_specialite_display()
            services[spec] = services.get(spec, 0) + 1

    context = {
        'dossiers': dossiers,
        'total': dossiers.count(),
        'actifs': dossiers.filter(statut='valide').count(),
        'urgents': dossiers.filter(statut='urgent').count(),
        'en_attente': dossiers.filter(statut='en_attente').count(),
        'services': services,
        'recherche': recherche,
        'statut_filtre': statut,
        'derniers_consultes': dossiers.order_by('-updated_at')[:5],
    }
    return render(request, 'dossiers_medicaux/liste.html', context)


@login_required
def detail_dossier(request, pk):
    """Détail d'un dossier médical avec contrôle d'accès strict.

    - super_admin : accès à tous
    - admin_hopital : accès SEULEMENT si le patient a un RDV dans son hôpital
    - médecin : accès SEULEMENT s'il a un RDV avec ce patient
    """
    dossier = get_object_or_404(DossierMedical, pk=pk)

    # Vérification d'accès
    if _est_super_admin(request):
        pass  # Accès total
    elif _est_admin_hopital(request):
        hopital = _hopital_personnel(request)
        if not _patient_a_rdv_dans_hopital(dossier.patient, hopital):
            messages.warning(request,
                "Ce patient n'a pas encore pris de rendez-vous dans votre hôpital. "
                "Vous n'avez pas accès à son dossier médical.")
            return render(request, 'patients/acces_refuse.html', status=403)
    elif _est_medecin(request):
        medecin = request.user.medecin_profile
        has_rdv = RendezVous.objects.filter(
            patient=dossier.patient, medecin=medecin
        ).exists()
        if not has_rdv:
            messages.warning(request,
                "Vous n'avez pas encore de rendez-vous avec ce patient. "
                "Vous n'avez pas accès à son dossier médical.")
            return render(request, 'patients/acces_refuse.html', status=403)
    else:
        return render(request, 'patients/acces_refuse.html', status=403)

    prescriptions = dossier.prescriptions.all()
    documents = dossier.documents.all()
    analyses = Analyse.objects.filter(
        patient=dossier.patient
    ).order_by('-date')
    
    # Récupérer les RDV du patient pour affichage
    rdvs_patient = RendezVous.objects.filter(
        patient=dossier.patient
    ).select_related('medecin', 'hopital').order_by('-date')[:10]
    
    context = {
        'dossier': dossier,
        'prescriptions': prescriptions,
        'documents': documents,
        'analyses': analyses,
        'rdvs_patient': rdvs_patient,
    }
    return render(request, 'dossiers_medicaux/detail.html', context)


@login_required
def nouveau_dossier(request):
    """Création manuelle d'un dossier — super_admin uniquement."""
    if not _est_super_admin(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    if request.method == 'POST':
        patient = get_object_or_404(Patient, pk=request.POST.get('patient'))
        from medecins.models import Medecin
        medecin = None
        if request.POST.get('medecin'):
            medecin = get_object_or_404(Medecin, pk=request.POST.get('medecin'))
        DossierMedical.objects.get_or_create(
            patient=patient,
            defaults={
                'medecin_referent': medecin,
                'antecedents': request.POST.get('antecedents', ''),
                'traitements_en_cours': request.POST.get('traitements', ''),
                'notes_medicales': request.POST.get('notes', ''),
                'statut': request.POST.get('statut', 'en_attente'),
            }
        )
        return redirect('dossiers_medicaux:liste')
    from medecins.models import Medecin
    context = {
        'patients': Patient.objects.filter(dossiermedical__isnull=True),
        'medecins': Medecin.objects.all(),
    }
    return render(request, 'dossiers_medicaux/nouveau.html', context)


@login_required
def modifier_dossier(request, pk):
    """Modifier un dossier — contrôle d'accès identique au détail."""
    dossier = get_object_or_404(DossierMedical, pk=pk)

    if _est_super_admin(request):
        pass
    elif _est_admin_hopital(request):
        hopital = _hopital_personnel(request)
        if not _patient_a_rdv_dans_hopital(dossier.patient, hopital):
            return render(request, 'patients/acces_refuse.html', status=403)
    elif _est_medecin(request):
        medecin = request.user.medecin_profile
        if not RendezVous.objects.filter(
            patient=dossier.patient, medecin=medecin
        ).exists():
            return render(request, 'patients/acces_refuse.html', status=403)
    else:
        return render(request, 'patients/acces_refuse.html', status=403)

    if request.method == 'POST':
        dossier.statut = request.POST.get('statut', dossier.statut)
        dossier.antecedents = request.POST.get('antecedents', '')
        dossier.traitements_en_cours = request.POST.get('traitements', '')
        dossier.notes_medicales = request.POST.get('notes', '')
        dossier.save()
        return redirect('dossiers_medicaux:detail', pk=pk)
    prescriptions = dossier.prescriptions.all()
    analyses = Analyse.objects.filter(patient=dossier.patient)
    context = {
        'dossier': dossier,
        'prescriptions': prescriptions,
        'analyses': analyses,
    }
    return render(request, 'dossiers_medicaux/modifier.html', context)


@login_required
def ajouter_prescription(request, pk):
    """Ajouter une prescription — contrôle d'accès identique."""
    dossier = get_object_or_404(DossierMedical, pk=pk)

    if _est_super_admin(request):
        pass
    elif _est_admin_hopital(request):
        hopital = _hopital_personnel(request)
        if not _patient_a_rdv_dans_hopital(dossier.patient, hopital):
            return render(request, 'patients/acces_refuse.html', status=403)
    elif _est_medecin(request):
        medecin = request.user.medecin_profile
        if not RendezVous.objects.filter(
            patient=dossier.patient, medecin=medecin
        ).exists():
            return render(request, 'patients/acces_refuse.html', status=403)
    else:
        return render(request, 'patients/acces_refuse.html', status=403)

    if request.method == 'POST':
        Prescription.objects.create(
            dossier=dossier,
            medicament=request.POST.get('medicament'),
            posologie=request.POST.get('posologie'),
            duree=request.POST.get('duree'),
            est_active=True,
        )
    return redirect('dossiers_medicaux:detail', pk=pk)


@login_required
def ajouter_document(request, pk):
    """Ajouter un document — contrôle d'accès identique."""
    dossier = get_object_or_404(DossierMedical, pk=pk)

    if _est_super_admin(request):
        pass
    elif _est_admin_hopital(request):
        hopital = _hopital_personnel(request)
        if not _patient_a_rdv_dans_hopital(dossier.patient, hopital):
            return render(request, 'patients/acces_refuse.html', status=403)
    elif _est_medecin(request):
        medecin = request.user.medecin_profile
        if not RendezVous.objects.filter(
            patient=dossier.patient, medecin=medecin
        ).exists():
            return render(request, 'patients/acces_refuse.html', status=403)
    else:
        return render(request, 'patients/acces_refuse.html', status=403)

    if request.method == 'POST':
        doc = Document.objects.create(
            dossier=dossier,
            titre=request.POST.get('titre'),
            type_document=request.POST.get('type_document'),
        )
        if request.FILES.get('fichier'):
            doc.fichier = request.FILES['fichier']
            doc.save()
    return redirect('dossiers_medicaux:detail', pk=pk)
