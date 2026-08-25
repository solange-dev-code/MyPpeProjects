"""
Services pour les analyses médicales.

- generer_graphique_evolution() : génère un PNG de l'évolution temporelle
  d'un paramètre pour un patient (matplotlib).
- get_dernieres_valeurs() : récupère l'historique d'un paramètre.
"""
import os
import io
import base64
from typing import List, Dict, Optional
from datetime import datetime

import matplotlib
matplotlib.use('Agg')  # backend non-interactif (sans GUI)
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as fm

# Police avec fallback CJK + symboles
try:
    fm.fontManager.addfont('/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf')
except Exception:
    pass
try:
    fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
except Exception:
    pass
plt.rcParams['font.sans-serif'] = ['Noto Sans SC', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['axes.unicode_minus'] = False

from .models import ResultatAnalyse, TypeAnalyse, Analyse


def get_historique_parametre(patient_id: int, type_analyse_code: str,
                              limit: int = 12) -> List[Dict]:
    """Récupère l'historique des valeurs d'un paramètre pour un patient.

    Retourne une liste de dicts : [{'date': date, 'valeur': float, 'flag': str}, ...]
    triée par ordre chronologique.
    """
    try:
        type_analyse = TypeAnalyse.objects.get(code=type_analyse_code)
    except TypeAnalyse.DoesNotExist:
        return []

    resultats = ResultatAnalyse.objects.filter(
        analyse__patient_id=patient_id,
        type_analyse=type_analyse
    ).select_related('analyse').order_by('-analyse__date')[:limit]

    return [{
        'date': r.analyse.date,
        'valeur': r.valeur,
        'unite': r.unite,
        'flag': r.flag,
    } for r in reversed(list(resultats))]


def generer_graphique_evolution(patient_id: int, type_analyse_code: str,
                                 limit: int = 12) -> Optional[bytes]:
    """Génère un graphique PNG de l'évolution d'un paramètre.

    Affiche :
    - Les points de mesure
    - Une zone ombrée pour les bornes normales
    - Un code couleur par flag (vert=N, orange=H/L, rouge=C)
    - Titre, axes, légende

    Retourne les bytes PNG, ou None si pas de données.
    """
    historique = get_historique_parametre(patient_id, type_analyse_code, limit)
    if not historique:
        return None

    try:
        type_analyse = TypeAnalyse.objects.get(code=type_analyse_code)
    except TypeAnalyse.DoesNotExist:
        return None

    dates = [h['date'] for h in historique]
    valeurs = [h['valeur'] for h in historique]
    flags = [h['flag'] for h in historique]

    fig, ax = plt.subplots(figsize=(8, 4), constrained_layout=True)

    # Zone des bornes normales
    basse = type_analyse.normale_basse_defaut
    haute = type_analyse.normale_haute_defaut
    if basse is not None and haute is not None:
        ax.axhspan(basse, haute, alpha=0.15, color='green', label='Normale')

    # Seuils critiques
    if type_analyse.seuil_critique_haute is not None:
        ax.axhline(y=type_analyse.seuil_critique_haute, color='red',
                   linestyle='--', alpha=0.5, label='Seuil critique haut')
    if type_analyse.seuil_critique_basse is not None:
        ax.axhline(y=type_analyse.seuil_critique_basse, color='red',
                   linestyle='--', alpha=0.5, label='Seuil critique bas')

    # Points de mesure avec code couleur
    couleurs_map = {'N': 'green', 'H': 'orange', 'L': 'orange', 'C': 'red'}
    couleurs = [couleurs_map.get(f, 'blue') for f in flags]

    ax.plot(dates, valeurs, '-o', color='#1f6c92', linewidth=1.5,
            markersize=8, markerfacecolor='white',
            markeredgecolor='#1f6c92', markeredgewidth=2, label='Valeur')

    # Surligner les points critiques
    for i, (d, v, f) in enumerate(zip(dates, valeurs, flags)):
        ax.plot(d, v, 'o', color=couleurs[i], markersize=10, alpha=0.7)

    # Mise en forme
    titre = f"Évolution — {type_analyse.nom} ({type_analyse.unite})"
    ax.set_title(titre, fontsize=12, fontweight='bold', color='#131515')
    ax.set_ylabel(f"{type_analyse.nom} ({type_analyse.unite})", fontsize=10)
    ax.set_xlabel('Date', fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate(rotation=30)

    # Légende
    ax.legend(loc='best', fontsize=8, framealpha=0.9)

    # Rendu en bytes
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=120, facecolor='white')
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()
