"""
Services métier pour les médecins.

- creneaux_disponibles() : génère les créneaux réservables pour une date,
  en excluant les RDV déjà pris et les périodes de congé.
- verifier_conflit() : détecte un conflit (double booking).
"""
from datetime import datetime, timedelta, date, time
from typing import List, Dict
from .models import DisponibiliteMedecin, CongeMedecin, Medecin
from appointments.models import RendezVous


def creneaux_disponibles(medecin_id: int, date_cible: date) -> List[Dict]:
    """Génère la liste des créneaux réservables pour un médecin à une date.

    Étapes :
    1. Vérifier que le médecin n'est pas en congé
    2. Récupérer les DisponibiliteMedecin actives pour le jour de la semaine
    3. Découper en créneaux de duree_creneau minutes
    4. Exclure les créneaux déjà réservés (RendezVous en_attente/confirme)
    5. Exclure les créneaux passés (si date_cible = aujourd'hui)

    Retourne une liste de dicts : [{'heure': '09:00', 'hopital_id': 1, 'disponible': True}, ...]
    """
    try:
        medecin = Medecin.objects.get(pk=medecin_id, est_actif=True)
    except Medecin.DoesNotExist:
        return []

    # 1. Vérifier congés
    if CongeMedecin.objects.filter(
        medecin=medecin, date_debut__lte=date_cible, date_fin__gte=date_cible
    ).exists():
        return []  # médecin en congé

    # 2. Disponibilités récurrentes
    dispos = DisponibiliteMedecin.objects.filter(
        medecin=medecin,
        jour_semaine=date_cible.weekday(),
        actif=True,
        validite_depuis__lte=date_cible,
    ).filter(
        # validite_jusqua null OU >= date_cible
        models_validite_filter(date_cible)
    )

    creneaux = []
    now = datetime.now()
    for d in dispos:
        current = datetime.combine(date_cible, d.heure_debut)
        fin = datetime.combine(date_cible, d.heure_fin)
        while current + timedelta(minutes=d.duree_creneau) <= fin:
            # Exclure créneaux passés si aujourd'hui
            if date_cible == now.date() and current <= now:
                current += timedelta(minutes=d.duree_creneau)
                continue
            creneaux.append({
                'heure': current.time().strftime('%H:%M'),
                'hopital_id': d.hopital_id,
                'medecin_id': medecin_id,
                'disponible': True,  # sera mis à False si déjà réservé
            })
            current += timedelta(minutes=d.duree_creneau)

    # 4. Exclure les créneaux déjà réservés
    rdvs_pris = set(
        RendezVous.objects.filter(
            medecin=medecin, date=date_cible,
            statut__in=['en_attente', 'confirme']
        ).values_list('heure', flat=True)
    )
    for c in creneaux:
        heure_obj = datetime.strptime(c['heure'], '%H:%M').time()
        if heure_obj in rdvs_pris:
            c['disponible'] = False

    return creneaux


def models_validite_filter(date_cible):
    """Helper : retourne un Q filter pour validite_jusqua."""
    from django.db.models import Q
    return Q(validite_jusqua__isnull=True) | Q(validite_jusqua__gte=date_cible)


def verifier_conflit(medecin_id: int, date_cible, heure) -> bool:
    """Retourne True s'il y a un conflit (un RDV existe déjà à cette date/heure)."""
    return RendezVous.objects.filter(
        medecin_id=medecin_id,
        date=date_cible,
        heure=heure,
        statut__in=['en_attente', 'confirme']
    ).exists()


def taux_occupation(medecin_id: int, date_debut, date_fin) -> float:
    """Calcule le taux d'occupation d'un médecin sur une période (0.0 à 1.0).

    KPI : taux optimal entre 0.70 et 0.80.
    """
    from django.db.models import Sum, Count
    dispos = DisponibiliteMedecin.objects.filter(
        medecin_id=medecin_id, actif=True
    )
    # Total créneaux théoriques (approximation : nb dispos × nb semaines)
    nb_jours = (date_fin - date_debut).days + 1
    total_minutes_theoriques = 0
    for d in dispos:
        # Calcul durée par jour de disponibilité
        duree_journaliere = (
            datetime.combine(date.today(), d.heure_fin) -
            datetime.combine(date.today(), d.heure_debut)
        ).total_seconds() / 60
        # Approx : si dispo 1 jour/semaine, multiplier par nb_semaines
        nb_semaines = nb_jours / 7
        total_minutes_theoriques += duree_journaliere * nb_semaines

    if total_minutes_theoriques == 0:
        return 0.0

    # Total minutes réservées
    rdvs = RendezVous.objects.filter(
        medecin_id=medecin_id,
        date__gte=date_debut,
        date__lte=date_fin,
        statut__in=['confirme', 'termine']
    )
    # Estimation : 30 min par RDV par défaut
    minutes_reservees = rdvs.count() * 30

    return min(1.0, minutes_reservees / total_minutes_theoriques)
