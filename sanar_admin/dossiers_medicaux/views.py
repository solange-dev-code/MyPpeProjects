from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import DossierMedical, Prescription, Document
from patients.models import Patient
from appointments.models import RendezVous
from analyses.models import Analyse

@login_required
def liste_dossiers(request):
    recherche = request.GET.get('q', '')
    statut = request.GET.get('statut', '')
    dossiers = DossierMedical.objects.all().select_related(
        'patient', 'medecin_referent'
    )
    if recherche:
        dossiers = dossiers.filter(
            Q(patient__nom__icontains=recherche) |
            Q(patient__prenom__icontains=recherche)
        )
    if statut:
        dossiers = dossiers.filter(statut=statut)

    services = {}
    for dossier in DossierMedical.objects.select_related('medecin_referent'):
        if dossier.medecin_referent:
            spec = dossier.medecin_referent.get_specialite_display()
            services[spec] = services.get(spec, 0) + 1

    context = {
        'dossiers': dossiers,
        'total': DossierMedical.objects.count(),
        'actifs': DossierMedical.objects.filter(statut='valide').count(),
        'urgents': DossierMedical.objects.filter(statut='urgent').count(),
        'en_attente': DossierMedical.objects.filter(statut='en_attente').count(),
        'services': services,
        'recherche': recherche,
        'statut_filtre': statut,
        'derniers_consultes': DossierMedical.objects.order_by('-updated_at')[:5],
    }
    return render(request, 'dossiers_medicaux/liste.html', context)

@login_required
def detail_dossier(request, pk):
    dossier = get_object_or_404(DossierMedical, pk=pk)
    prescriptions = dossier.prescriptions.all()
    documents = dossier.documents.all()
    # Analyses du patient liées au dossier
    analyses = Analyse.objects.filter(
        patient=dossier.patient
    ).order_by('-date')
    context = {
        'dossier': dossier,
        'prescriptions': prescriptions,
        'documents': documents,
        'analyses': analyses,
    }
    return render(request, 'dossiers_medicaux/detail.html', context)

@login_required
def nouveau_dossier(request):
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
    dossier = get_object_or_404(DossierMedical, pk=pk)
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
    dossier = get_object_or_404(DossierMedical, pk=pk)
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
    dossier = get_object_or_404(DossierMedical, pk=pk)
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