"""
Vues gestion médecins — Nouvelle idéologie :
- super_admin : NE PEUT PAS ajouter/modifier/supprimer de médecins
  (il gère uniquement les hôpitaux et les admin_hopital)
- admin_hopital : SEUL autorisé à ajouter/modifier/supprimer les médecins
  de SON hôpital
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from .models import Medecin, DisponibiliteMedecin, CongeMedecin
from appointments.models import RendezVous
from consultations.models import Consultation
from hopitaux.models import Hopital


def _est_super_admin(request):
    """Un super_admin n'a pas de personnel OU a le role super_admin."""
    personnel = getattr(request.user, 'personnel', None)
    return personnel is None or personnel.role == 'super_admin'


def _est_admin_hopital(request):
    """Un admin_hopital a un personnel avec role admin_hopital ET un hopital."""
    personnel = getattr(request.user, 'personnel', None)
    return personnel is not None and personnel.role == 'admin_hopital' and personnel.hopital is not None


def _hopital_personnel(request):
    personnel = getattr(request.user, 'personnel', None)
    return personnel.hopital if personnel else None


@login_required
def liste_medecins(request):
    """Liste des médecins.
    - super_admin : voit tous les médecins (lecture seule, pas d'ajout)
    - admin_hopital : voit uniquement les médecins de son hôpital (peut ajouter)
    """
    recherche = request.GET.get('q', '')
    specialite = request.GET.get('specialite', '')

    if _est_super_admin(request):
        medecins_qs = Medecin.objects.all()
    elif _est_admin_hopital(request):
        medecins_qs = Medecin.objects.filter(hopital=_hopital_personnel(request))
    else:
        # Médecin ou patient : accès refusé
        return render(request, 'patients/acces_refuse.html', status=403)

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
        'est_super_admin': _est_super_admin(request),
        'est_admin_hopital': _est_admin_hopital(request),
        'hopital_personnel': _hopital_personnel(request),
    }
    return render(request, 'medecins/liste.html', context)


@login_required
def detail_medecin(request, pk):
    """Détail d'un médecin.
    - super_admin : lecture seule (peut voir tous les médecins)
    - admin_hopital : uniquement les médecins de son hôpital
    """
    medecin = get_object_or_404(Medecin, pk=pk)

    if not _est_super_admin(request):
        if not _est_admin_hopital(request) or medecin.hopital != _hopital_personnel(request):
            return render(request, 'patients/acces_refuse.html', status=403)

    rdvs = RendezVous.objects.filter(
        medecin=medecin
    ).order_by('-date')[:5]
    consultations = Consultation.objects.filter(
        medecin=medecin
    ).order_by('-date')[:5]
    
    # Récupérer les disponibilités du médecin
    disponibilites = DisponibiliteMedecin.objects.filter(
        medecin=medecin, actif=True
    ).order_by('jour_semaine', 'heure_debut')
    
    context = {
        'medecin': medecin,
        'rdvs': rdvs,
        'consultations': consultations,
        'disponibilites': disponibilites,
        'total_rdvs': RendezVous.objects.filter(medecin=medecin).count(),
        'total_consultations': Consultation.objects.filter(medecin=medecin).count(),
        'est_super_admin': _est_super_admin(request),
        'est_admin_hopital': _est_admin_hopital(request),
    }
    return render(request, 'medecins/detail.html', context)


@login_required
def ajouter_medecin(request):
    """Ajouter un médecin — RÉSERVÉ à admin_hopital uniquement.
    
    Nouvelle idéologie : le super_admin NE PEUT PAS ajouter de médecin.
    Seul l'admin_hopital peut ajouter des médecins pour SON hôpital.
    """
    # Blocage du super_admin
    if _est_super_admin(request):
        messages.error(request, 
            "Le super administrateur ne peut pas ajouter de medecins. "
            "Cette action est reservee a l'administrateur de l'hopital concerne.")
        return redirect('medecins:liste')
    
    if not _est_admin_hopital(request):
        return render(request, 'patients/acces_refuse.html', status=403)
    
    hopital = _hopital_personnel(request)
    
    if request.method == 'POST':
        medecin = Medecin.objects.create(
            nom=request.POST.get('nom'),
            prenom=request.POST.get('prenom'),
            specialite=request.POST.get('specialite'),
            telephone=request.POST.get('telephone'),
            email=request.POST.get('email', ''),
            cabinet=request.POST.get('cabinet', ''),
            hopital=hopital,  # Forcé à l'hôpital de l'admin
        )
        messages.success(request, f"Medecin {medecin.prenom} {medecin.nom} ajoute avec succes.")
        return redirect('medecins:liste')
    
    context = {
        'specialites': Medecin.SPECIALITE_CHOICES,
        'hopital': hopital,
    }
    return render(request, 'medecins/ajouter.html', context)


@login_required
def modifier_medecin(request, pk):
    """Modifier un médecin — RÉSERVÉ à admin_hopital de SON hôpital."""
    medecin = get_object_or_404(Medecin, pk=pk)

    if _est_super_admin(request):
        messages.error(request, 
            "Le super administrateur ne peut pas modifier de medecins. "
            "Cette action est reservee a l'administrateur de l'hopital.")
        return redirect('medecins:liste')
    
    if not _est_admin_hopital(request) or medecin.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    if request.method == 'POST':
        medecin.nom = request.POST.get('nom')
        medecin.prenom = request.POST.get('prenom')
        medecin.specialite = request.POST.get('specialite')
        medecin.telephone = request.POST.get('telephone')
        medecin.email = request.POST.get('email', '')
        medecin.cabinet = request.POST.get('cabinet', '')
        medecin.est_actif = request.POST.get('est_actif') == 'on'
        # L'hôpital ne peut pas être changé (sécurité)
        medecin.save()
        messages.success(request, f"Medecin {medecin.prenom} {medecin.nom} modifie avec succes.")
        return redirect('medecins:liste')
    
    context = {
        'medecin': medecin,
        'specialites': Medecin.SPECIALITE_CHOICES,
    }
    return render(request, 'medecins/modifier.html', context)


@login_required
def supprimer_medecin(request, pk):
    """Supprimer un médecin — RÉSERVÉ à admin_hopital de SON hôpital."""
    medecin = get_object_or_404(Medecin, pk=pk)

    if _est_super_admin(request):
        messages.error(request, 
            "Le super administrateur ne peut pas supprimer de medecins. "
            "Cette action est reservee a l'administrateur de l'hopital.")
        return redirect('medecins:liste')
    
    if not _est_admin_hopital(request) or medecin.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)

    if request.method == 'POST':
        nom_medecin = f"{medecin.prenom} {medecin.nom}"
        medecin.delete()
        messages.success(request, f"Medecin {nom_medecin} supprime avec succes.")
    return redirect('medecins:liste')


@login_required
def horaires_medecin(request, pk):
    """Tableau d'horaires du médecin — visible par admin_hopital et patient.
    
    - admin_hopital : peut modifier les disponibilités
    - patient : peut voir les créneaux disponibles pour changer son RDV
    """
    medecin = get_object_or_404(Medecin, pk=pk)
    
    disponibilites = DisponibiliteMedecin.objects.filter(
        medecin=medecin, actif=True
    ).order_by('jour_semaine', 'heure_debut')
    
    # Pour les patients : récupérer les créneaux disponibles pour les 7 prochains jours
    from .services import creneaux_disponibles
    from datetime import date, timedelta
    
    jours = []
    today = date.today()
    for i in range(7):
        jour = today + timedelta(days=i)
        creneaux = creneaux_disponibles(medecin.id, jour)
        jours.append({
            'date': jour,
            'jour_nom': ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][jour.weekday()],
            'creneaux': creneaux,
            'nb_disponibles': len([c for c in creneaux if c['disponible']]),
        })
    
    context = {
        'medecin': medecin,
        'disponibilites': disponibilites,
        'jours': jours,
        'est_admin_hopital': _est_admin_hopital(request),
        'est_super_admin': _est_super_admin(request),
    }
    return render(request, 'medecins/horaires.html', context)


@login_required
def ajouter_disponibilite(request, medecin_id):
    """Ajouter une disponibilité — admin_hopital uniquement."""
    if _est_super_admin(request):
        messages.error(request, "Action reservee a l'administrateur de l'hopital.")
        return redirect('medecins:liste')
    
    if not _est_admin_hopital(request):
        return render(request, 'patients/acces_refuse.html', status=403)
    
    medecin = get_object_or_404(Medecin, pk=medecin_id)
    if medecin.hopital != _hopital_personnel(request):
        return render(request, 'patients/acces_refuse.html', status=403)
    
    if request.method == 'POST':
        DisponibiliteMedecin.objects.create(
            medecin=medecin,
            hopital=medecin.hopital,
            jour_semaine=request.POST.get('jour_semaine'),
            heure_debut=request.POST.get('heure_debut'),
            heure_fin=request.POST.get('heure_fin'),
            duree_creneau=request.POST.get('duree_creneau', 30),
            validite_depuis=request.POST.get('validite_depuis'),
            validite_jusqua=request.POST.get('validite_jusqua') or None,
        )
        messages.success(request, "Disponibilite ajoutee avec succes.")
    return redirect('medecins:horaires', pk=medecin_id)
