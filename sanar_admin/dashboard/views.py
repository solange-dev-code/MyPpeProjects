from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from patients.models import Patient
from appointments.models import RendezVous
from analyses.models import Analyse
from consultations.models import Consultation
from django.utils import timezone


def _est_super_admin(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel is None or personnel.role == 'super_admin'


def _hopital_personnel(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel.hopital if personnel else None


@login_required
def dashboard(request):
    today = timezone.now().date()

    if _est_super_admin(request):
        rdv_qs = RendezVous.objects.all()
        analyses_qs = Analyse.objects.all()
        patients_qs = Patient.objects.all()
    else:
        hopital = _hopital_personnel(request)
        rdv_qs = RendezVous.objects.filter(hopital=hopital)
        analyses_qs = Analyse.objects.filter(patient__hopital=hopital)
        patients_qs = Patient.objects.filter(hopital=hopital)

    derniers_patients = patients_qs.order_by('-date_inscription')[:3]
    derniers_rdvs = rdv_qs.order_by('-created_at')[:3]
    dernieres_analyses = analyses_qs.filter(
        statut='disponible'
    ).order_by('-created_at')[:2]

    activites = []
    for p in derniers_patients:
        activites.append({
            'icone': 'bi-person-plus',
            'texte': f'Nouveau patient : {p.prenom} {p.nom}',
            'temps': p.date_inscription,
        })
    for r in derniers_rdvs:
        activites.append({
            'icone': 'bi-calendar-check',
            'texte': f'RDV {r.get_statut_display()} — {r.patient}',
            'temps': r.created_at,
        })

    context = {
        'total_patients': patients_qs.count(),
        'rdv_jour': rdv_qs.filter(date=today).count(),
        'analyses_cours': analyses_qs.filter(statut='en_attente').count(),
        'patients_critiques': patients_qs.filter(est_critique=True).count(),
        'activites': activites,
    }
    return render(request, 'dashboard/dashboard.html', context)