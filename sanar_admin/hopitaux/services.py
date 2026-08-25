"""
Services métier pour les hôpitaux.

- assigner_hopital() : algorithme d'assignation multi-critères
  Score = distance + 3×file_attente - 5×lits_disponibles
- haversine() : distance orthodromique (redéfini ici pour éviter import circulaire)
"""
from typing import Optional
from math import radians, sin, cos, asin, sqrt
from geopy.distance import geodesic

from .models import Hopital, LitHopital
from medecins.models import Medecin
from file_attente.models import FileAttente


def haversine_km(lat1, lon1, lat2, lon2):
    """Distance orthodromique en km (formule Haversine)."""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (sin(dlat / 2) ** 2
         + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2)
    return 2 * R * asin(sqrt(a))


def assigner_hopital(patient, specialite_requise: str = None,
                     latitude: float = None, longitude: float = None,
                     niveau_urgence: str = 'P3') -> Optional[Hopital]:
    """Assigne le meilleur hôpital au patient selon :
    1. Spécialité requise (filtre dur si fournie)
    2. Distance géographique (Haversine)
    3. Charge actuelle de la file d'attente
    4. Disponibilité de lits

    Score = distance_km + (3 × charge_file) - (5 × lits_dispo)
    Pour P1, on priorise la distance pure.

    Retourne l'hôpital au score minimum, ou None si aucun candidat.
    """
    candidats = Hopital.objects.filter(actif=True)

    # 1. Filtrer par spécialité si fournie
    if specialite_requise:
        candidats = candidats.filter(
            medecins__specialite=specialite_requise,
            medecins__est_actif=True
        ).distinct()

    if not candidats.exists():
        return None

    # Si pas de géoloc patient → retourner le moins chargé
    if latitude is None or longitude is None:
        return _moins_charge(candidats, niveau_urgence)

    scores = []
    for h in candidats:
        if h.latitude is None or h.longitude is None:
            continue
        dist_km = haversine_km(latitude, longitude, h.latitude, h.longitude)
        # Charge file d'attente
        charge_file = FileAttente.objects.filter(
            hopital=h, statut='en_attente'
        ).count()
        # Lits disponibles (somme tous services confondus)
        lits_dispo = sum(l.disponibles for l in h.lits.all())

        # Pondération par niveau d'urgence
        if niveau_urgence == 'P1':
            # P1 : prioriser distance pure (1km par lit, 1km par file)
            score = dist_km + (charge_file * 1.0) - (lits_dispo * 1.0)
            # Bonus pour hôpital avec service urgences
            if h.lits.filter(service='urgences', occupes__lt=10).exists():
                score -= 10.0
        else:
            # Standard : 3km par patient en file, -5km par lit dispo
            score = dist_km + (charge_file * 3.0) - (lits_dispo * 5.0)

        scores.append((score, h))

    if not scores:
        return _moins_charge(candidats, niveau_urgence)

    scores.sort(key=lambda x: x[0])
    return scores[0][1]


def _moins_charge(candidats, niveau_urgence):
    """Retourne l'hôpital avec la plus petite file d'attente."""
    meilleur = None
    min_charge = float('inf')
    for h in candidats:
        charge = FileAttente.objects.filter(
            hopital=h, statut='en_attente'
        ).count()
        if charge < min_charge:
            min_charge = charge
            meilleur = h
    return meilleur
