from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta

from patients.models import Patient
from appointments.models import RendezVous
from analyses.models import Analyse
from consultations.models import Consultation
from facturation.models import Facture
from urgences.models import DemandeUrgence
from file_attente.models import FileAttente


def _est_super_admin(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel is None or personnel.role == 'super_admin'


def _hopital_personnel(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel.hopital if personnel else None


@login_required
def dashboard(request):
    """Dashboard enrichi avec KPIs visuels (Chart.js).

    Affiche :
    - 4 KPI cards (patients, RDV jour, analyses en cours, urgences)
    - Évolution des inscriptions patients (12 mois)
    - RDV par jour (7 derniers jours)
    - Répartition statuts RDV (donut)
    - Analyses critiques récentes
    - File d'attente temps réel
    """
    today = timezone.now().date()
    il_y_a_30_jours = today - timedelta(days=30)
    il_y_a_7_jours = today - timedelta(days=7)
    il_y_a_12_mois = today - timedelta(days=365)

    if _est_super_admin(request):
        rdv_qs = RendezVous.objects.all()
        analyses_qs = Analyse.objects.all()
        patients_qs = Patient.objects.all()
        urgences_qs = DemandeUrgence.objects.all()
        file_qs = FileAttente.objects.filter(statut='en_attente')
    else:
        hopital = _hopital_personnel(request)
        rdv_qs = RendezVous.objects.filter(hopital=hopital)
        analyses_qs = Analyse.objects.filter(patient__hopital=hopital)
        patients_qs = Patient.objects.filter(hopital=hopital)
        urgences_qs = DemandeUrgence.objects.filter(hopital_destine=hopital)
        file_qs = FileAttente.objects.filter(hopital=hopital, statut='en_attente')

    # ── KPIs principaux ──
    total_patients = patients_qs.count()
    patients_30j = patients_qs.filter(
        date_inscription__gte=il_y_a_30_jours
    ).count()
    rdv_jour = rdv_qs.filter(date=today).count()
    analyses_cours = analyses_qs.filter(statut='en_attente').count()
    patients_critiques = patients_qs.filter(est_critique=True).count()
    urgences_en_cours = urgences_qs.filter(
        statut__in=['en_attente', 'assignee', 'en_route']
    ).count()

    # ── Évolution patients (12 mois) ──
    patients_par_mois = list(
        patients_qs.filter(date_inscription__gte=il_y_a_12_mois)
        .annotate(mois=TruncMonth('date_inscription'))
        .values('mois')
        .annotate(count=Count('id'))
        .order_by('mois')
    )
    evolution_labels = [p['mois'].strftime('%m/%y')
                        for p in patients_par_mois]
    evolution_data = [p['count'] for p in patients_par_mois]

    # ── RDV 7 derniers jours ──
    rdv_par_jour = list(
        rdv_qs.filter(date__gte=il_y_a_7_jours)
        .annotate(jour=TruncDate('date'))
        .values('jour')
        .annotate(count=Count('id'))
        .order_by('jour')
    )
    rdv_labels = [r['jour'].strftime('%d/%m') for r in rdv_par_jour]
    rdv_data = [r['count'] for r in rdv_par_jour]

    # ── Répartition statuts RDV (donut) ──
    statuts_rdv = rdv_qs.values('statut').annotate(count=Count('id'))
    statut_labels = [s['statut'] for s in statuts_rdv]
    statut_data = [s['count'] for s in statuts_rdv]

    # ── Analyses critiques récentes ──
    analyses_critiques = analyses_qs.filter(
        est_critique=True, alerte_traitee=False
    ).select_related('patient')[:10]

    # ── File d'attente temps réel ──
    file_attente = file_qs.select_related('patient').order_by(
        'niveau_triage', 'arrivee_at'
    )[:10]

    # ── Activités récentes (conservé pour compat) ──
    derniers_patients = patients_qs.order_by('-date_inscription')[:3]
    derniers_rdvs = rdv_qs.order_by('-created_at')[:3]
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

    # ── CA mensuel (super_admin only) ──
    ca_mensuel = None
    if _est_super_admin(request):
        ca_mensuel = Facture.objects.filter(
            statut='payee',
            date_paiement__gte=il_y_a_30_jours
        ).aggregate(total=Sum('montant_total'))['total'] or 0

    context = {
        # KPIs
        'total_patients': total_patients,
        'patients_30j': patients_30j,
        'rdv_jour': rdv_jour,
        'analyses_cours': analyses_cours,
        'patients_critiques': patients_critiques,
        'urgences_en_cours': urgences_en_cours,
        'ca_mensuel': ca_mensuel,

        # Charts
        'evolution_labels': evolution_labels,
        'evolution_data': evolution_data,
        'rdv_labels': rdv_labels,
        'rdv_data': rdv_data,
        'statut_labels': statut_labels,
        'statut_data': statut_data,

        # Listes
        'analyses_critiques': analyses_critiques,
        'file_attente': file_attente,
        'activites': activites,
    }
    return render(request, 'dashboard/dashboard.html', context)
