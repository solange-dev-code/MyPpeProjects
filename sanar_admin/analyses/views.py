from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Analyse
from patients.models import Patient


def _est_super_admin(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel is None or personnel.role == 'super_admin'


def _hopital_personnel(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel.hopital if personnel else None


def _patients_visibles(request):
    if _est_super_admin(request):
        return Patient.objects.all()
    return Patient.objects.filter(hopital=_hopital_personnel(request))


@login_required
def liste_analyses(request):
    if _est_super_admin(request):
        analyses_qs = Analyse.objects.all()
    else:
        analyses_qs = Analyse.objects.filter(patient__hopital=_hopital_personnel(request))

    analyses = analyses_qs.select_related('patient')
    statut_filtre = request.GET.get('statut', '')
    if statut_filtre:
        analyses = analyses.filter(statut=statut_filtre)

    context = {
        'analyses': analyses,
        'total_aujourd_hui': analyses_qs.filter(
            date=timezone.now().date()
        ).count(),
        'patients_analyses': _patients_visibles(request).filter(
            analyse__isnull=False
        ).distinct().count(),
        'resultats_anormaux': analyses_qs.filter(statut='critique').count(),
        'en_attente': analyses_qs.filter(statut='en_attente').count(),
        'statut_filtre': statut_filtre,
    }
    return render(request, 'analyses/liste.html', context)


@login_required
def detail_analyse(request, pk):
    analyse = get_object_or_404(Analyse, pk=pk)

    if not _est_super_admin(request) and analyse.patient.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    return render(request, 'analyses/detail.html', {'analyse': analyse})


@login_required
def valider_analyse(request, pk):
    analyse = get_object_or_404(Analyse, pk=pk)

    if not _est_super_admin(request) and analyse.patient.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    if analyse.statut == 'disponible':
        from django.contrib import messages
        messages.error(request, 'Cette analyse a déjà un résultat.')
        return redirect('analyses:liste')

    from django.utils import timezone
    if analyse.date > timezone.now().date():
        from django.contrib import messages
        messages.error(
            request,
            f"Impossible d'ajouter un résultat : l'analyse est prévue "
            f"pour le {analyse.date.strftime('%d/%m/%Y')}."
        )
        return redirect('analyses:liste')

    if request.method == 'POST':
        analyse.statut = 'disponible'
        analyse.resultat = request.POST.get('resultat', '')
        analyse.conclusion = request.POST.get('conclusion', '')
        if request.FILES.get('fichier_pdf'):
            analyse.fichier_pdf = request.FILES['fichier_pdf']
        analyse.save()

        from django.contrib import messages
        messages.success(request, 'Résultat ajouté avec succès !')
        return redirect('analyses:liste')

    return render(request, 'analyses/valider.html', {'analyse': analyse})


@login_required
def resultats_analyse(request):
    patients = _patients_visibles(request)

    if _est_super_admin(request):
        analyses_base = Analyse.objects.all()
    else:
        analyses_base = Analyse.objects.filter(patient__hopital=_hopital_personnel(request))

    if request.method == 'POST':
        analyse_id = request.POST.get('analyse')
        if not analyse_id:
            from django.contrib import messages
            messages.error(request, 'Veuillez sélectionner une analyse.')
            analyses = analyses_base.filter(statut='en_attente')
            return render(request, 'analyses/resultats.html', {
                'patients': patients,
                'analyses': analyses,
            })

        analyse = get_object_or_404(Analyse, pk=analyse_id)

        if not _est_super_admin(request) and analyse.patient.hopital != _hopital_personnel(request):
            return render(request, 'patients/acces_refuse.html', status=403)

        from django.utils import timezone
        if analyse.date > timezone.now().date():
            from django.contrib import messages
            messages.error(
                request,
                f"Impossible d'ajouter un résultat : "
                f"l'analyse est prévue pour le "
                f"{analyse.date.strftime('%d/%m/%Y')}. "
                f"Elle n'a pas encore été effectuée."
            )
            analyses = analyses_base.filter(statut='en_attente')
            return render(request, 'analyses/resultats.html', {
                'patients': patients,
                'analyses': analyses,
            })

        if analyse.statut == 'disponible':
            from django.contrib import messages
            messages.error(request, 'Cette analyse a déjà un résultat.')
            analyses = analyses_base.filter(statut='en_attente')
            return render(request, 'analyses/resultats.html', {
                'patients': patients,
                'analyses': analyses,
            })

        analyse.statut = 'disponible'
        analyse.resultat = request.POST.get('resultat', '')
        analyse.conclusion = request.POST.get('conclusion', '')
        if request.FILES.get('fichier_pdf'):
            analyse.fichier_pdf = request.FILES['fichier_pdf']
        analyse.save()

        from django.contrib import messages
        messages.success(request,
            f'Résultat ajouté pour {analyse.patient.prenom} '
            f'{analyse.patient.nom} !')
        return redirect('analyses:liste')

    from django.utils import timezone
    analyses = analyses_base.filter(
        statut='en_attente',
        date__lte=timezone.now().date()
    )
    context = {
        'patients': patients,
        'analyses': analyses,
    }
    return render(request, 'analyses/resultats.html', context)


@login_required
def ajouter_analyse(request):
    patients = _patients_visibles(request)

    if request.method == 'POST':
        patient = get_object_or_404(Patient, pk=request.POST.get('patient'))

        if not _est_super_admin(request) and patient.hopital != _hopital_personnel(request):
            return render(request, 'patients/acces_refuse.html', status=403)

        analyse = Analyse.objects.create(
            patient=patient,
            type_analyse=request.POST.get('type_analyse'),
            laboratoire=request.POST.get('laboratoire'),
            date=request.POST.get('date'),
            statut='en_attente',
        )
        if request.FILES.get('fichier_pdf'):
            analyse.fichier_pdf = request.FILES['fichier_pdf']
            analyse.save()
        return redirect('analyses:liste')

    return render(request, 'analyses/ajouter.html', {'patients': patients})