from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Hopital

@login_required
def liste_hopitaux(request):
    recherche = request.GET.get('q', '')
    hopitaux = Hopital.objects.all().order_by('nom')

    if recherche:
        hopitaux = hopitaux.filter(
            Q(nom__icontains=recherche) |
            Q(ville__icontains=recherche) |
            Q(adresse__icontains=recherche)
        )

    context = {
        'hopitaux': hopitaux,
        'total': Hopital.objects.count(),
        'actifs': Hopital.objects.filter(actif=True).count(),
        'recherche': recherche,
    }
    return render(request, 'hopitaux/liste.html', context)


@login_required
def ajouter_hopital(request):
    if request.method == 'POST':
        Hopital.objects.create(
            nom=request.POST.get('nom'),
            adresse=request.POST.get('adresse'),
            ville=request.POST.get('ville'),
            telephone=request.POST.get('telephone', ''),
            email=request.POST.get('email', ''),
            latitude=request.POST.get('latitude') or None,
            longitude=request.POST.get('longitude') or None,
            actif=request.POST.get('actif') == 'on',
        )
        return redirect('hopitaux:liste')
    return render(request, 'hopitaux/ajouter.html')


@login_required
def modifier_hopital(request, pk):
    hopital = get_object_or_404(Hopital, pk=pk)
    if request.method == 'POST':
        hopital.nom = request.POST.get('nom')
        hopital.adresse = request.POST.get('adresse')
        hopital.ville = request.POST.get('ville')
        hopital.telephone = request.POST.get('telephone', '')
        hopital.email = request.POST.get('email', '')
        hopital.latitude = request.POST.get('latitude') or None
        hopital.longitude = request.POST.get('longitude') or None
        hopital.actif = request.POST.get('actif') == 'on'
        hopital.save()
        return redirect('hopitaux:liste')
    return render(request, 'hopitaux/modifier.html', {'hopital': hopital})


@login_required
def supprimer_hopital(request, pk):
    hopital = get_object_or_404(Hopital, pk=pk)
    if request.method == 'POST':
        hopital.delete()
    return redirect('hopitaux:liste')