from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import Evenement
from patients.models import Patient
from appointments.models import Medecin, RendezVous
import json

@login_required
def calendrier(request):
    evenements = Evenement.objects.all()
    rdvs = RendezVous.objects.all().select_related('patient', 'medecin')

    evenements_json = []
    for e in evenements:
        evenements_json.append({
            'id': e.pk,
            'title': e.titre,
            'start': e.date_debut.isoformat(),
            'end': e.date_fin.isoformat() if e.date_fin else None,
            'color': dict(Evenement.COULEUR_CHOICES).get(e.couleur, '#2563EB'),
            'type': e.get_type_evenement_display(),
        })

    for rdv in rdvs:
        couleur = '#16A34A' if rdv.statut == 'confirme' else '#D97706'
        evenements_json.append({
            'id': f'rdv-{rdv.pk}',
            'title': f'RDV - {rdv.patient.prenom} {rdv.patient.nom}',
            'start': f'{rdv.date}T{rdv.heure}',
            'color': couleur,
            'type': 'Rendez-Vous',
        })

    context = {
        'evenements_json': json.dumps(evenements_json),
        'patients': Patient.objects.all(),
        'medecins': Medecin.objects.all(),
        'total_events': evenements.count(),
        'total_rdvs': rdvs.count(),
    }
    return render(request, 'calendrier/calendrier.html', context)

@login_required
def ajouter_evenement(request):
    if request.method == 'POST':
        Evenement.objects.create(
            titre=request.POST.get('titre'),
            type_evenement=request.POST.get('type_evenement'),
            couleur=request.POST.get('couleur', 'blue'),
            date_debut=request.POST.get('date_debut'),
            date_fin=request.POST.get('date_fin') or None,
            description=request.POST.get('description', ''),
            created_by=request.user,
        )
        return redirect('calendrier:calendrier')
    return render(request, 'calendrier/ajouter.html')

@login_required
def get_evenements(request):
    evenements = Evenement.objects.all()
    data = []
    for e in evenements:
        data.append({
            'id': e.pk,
            'title': e.titre,
            'start': e.date_debut.isoformat(),
            'color': dict(Evenement.COULEUR_CHOICES).get(e.couleur, '#2563EB'),
        })
    return JsonResponse(data, safe=False)