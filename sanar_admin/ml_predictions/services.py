"""
Service de prédiction ML pour analyses médicales.

Approche : Random Forest entraîné sur l'historique des analyses patient
pour prédire un score de risque de complication à 30 jours.

Pipeline :
1. Extraction features : pour chaque patient, agrège les dernières valeurs
   de chaque paramètre (glycémie, hémoglobine, créatinine, etc.)
2. Label : 1 si le patient a eu une analyse critique dans les 30 jours suivants,
   0 sinon.
3. Entraînement : RandomForestClassifier (scikit-learn)
4. Inférence : predict_proba sur nouveaux patients
5. Stockage : MLPrediction avec score + features_importantes

Note : en l'absence de données historiques suffisantes, le service retourne
un score par défaut de 0.3 (modéré) avec un flag `modele_froid=True`.
"""
import logging
import pickle
import io
from datetime import timedelta
from typing import Dict, List, Tuple, Optional
from django.utils import timezone
from django.core.files.base import ContentFile

from patients.models import Patient
from analyses.models import Analyse, ResultatAnalyse, TypeAnalyse
from .models import MLModel, MLPrediction

logger = logging.getLogger('sanar.ml')


# ──────────────────────────────────────────────────────────────
# 1. Extraction des features
# ──────────────────────────────────────────────────────────────
def extraire_features_patient(patient_id: int) -> Dict[str, float]:
    """Extrait les features d'un patient à partir de son historique d'analyses.

    Pour chaque paramètre (TypeAnalyse), prend la dernière valeur mesurée.
    Retourne un dict {code_type_analyse: derniere_valeur}.
    """
    features = {}
    resultats = ResultatAnalyse.objects.filter(
        analyse__patient_id=patient_id
    ).select_related('analyse', 'type_analyse').order_by('-analyse__date')

    for r in resultats:
        code = r.type_analyse.code
        if code not in features:  # prendre seulement la dernière valeur
            features[code] = r.valeur
    return features


def extraire_label_patient(patient_id: int, date_ref) -> int:
    """Label : 1 si le patient a eu une analyse critique dans les 30 jours
    après date_ref, 0 sinon.
    """
    has_critique = Analyse.objects.filter(
        patient_id=patient_id,
        est_critique=True,
        date__gte=date_ref,
        date__lt=date_ref + timedelta(days=30)
    ).exists()
    return 1 if has_critique else 0


# ──────────────────────────────────────────────────────────────
# 2. Entraînement
# ──────────────────────────────────────────────────────────────
def entrainer_modele() -> Optional[MLModel]:
    """Entraîne un Random Forest sur les analyses historiques.

    Retourne le MLModel créé, ou None si données insuffisantes.
    """
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import precision_score, recall_score, roc_auc_score
        import numpy as np
    except ImportError:
        logger.warning("scikit-learn non installé — entraînement impossible")
        return None

    # Récupérer tous les patients avec au moins 3 analyses
    patients_avec_analyses = Patient.objects.annotate(
        n_analyses=__import__('django.db.models', fromlist=['Count']).Count('analyses')
    ).filter(n_analyses__gte=3)

    if patients_avec_analyses.count() < 10:
        logger.warning("Pas assez de patients avec analyses (min 10 requis, "
                       "eu %d)", patients_avec_analyses.count())
        return None

    # Construire dataset
    features_list = []
    labels = []
    all_codes = set()
    for p in patients_avec_analyses:
        features = extraire_features_patient(p.id)
        if len(features) < 3:
            continue
        all_codes.update(features.keys())
        # Date de référence = dernière analyse
        derniere_analyse = p.analyses.order_by('-date').first()
        if not derniere_analyse:
            continue
        label = extraire_label_patient(p.id, derniere_analyse.date)
        features_list.append((p.id, features))
        labels.append(label)

    if len(features_list) < 10:
        logger.warning("Dataset insuffisant après filtrage")
        return None

    # Construire matrice X (avec features manquantes = 0)
    all_codes = sorted(all_codes)
    X = []
    for _, features in features_list:
        row = [features.get(code, 0.0) for code in all_codes]
        X.append(row)
    y = labels

    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Entraînement
    clf = RandomForestClassifier(
        n_estimators=100, max_depth=10, random_state=42
    )
    clf.fit(X_train, y_train)

    # Métriques
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1] if len(set(y_test)) > 1 else [0.5]*len(y_test)
    precision = precision_score(y_test, y_pred, zero_division=0)
    rappel = recall_score(y_test, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_test, y_proba) if len(set(y_test)) > 1 else 0.5
    except Exception:
        auc = 0.5

    # Sérialiser le modèle
    modele_bytes = pickle.dumps({
        'model': clf,
        'feature_codes': all_codes,
    })

    # Version auto-incrémentée
    version = f"v{MLModel.objects.count() + 1}.0"
    ml_model = MLModel.objects.create(
        nom='random_forest_analyses',
        version=version,
        precision=precision,
        rappel=rappel,
        auc=auc,
        hyperparametres={
            'n_estimators': 100,
            'max_depth': 10,
            'n_patients': len(features_list),
            'n_features': len(all_codes),
        },
        est_actif=True,
    )
    ml_model.fichier_modele.save(
        f'model_{version}.pkl', ContentFile(modele_bytes), save=True
    )
    # Désactiver les anciens modèles
    MLModel.objects.exclude(pk=ml_model.pk).update(est_actif=False)

    logger.info("Modèle ML entraîné : %s (precision=%.3f, rappel=%.3f, AUC=%.3f)",
                version, precision, rappel, auc)
    return ml_model


# ──────────────────────────────────────────────────────────────
# 3. Inférence
# ──────────────────────────────────────────────────────────────
def predire_risque_patient(patient_id: int) -> MLPrediction:
    """Prédit le score de risque pour un patient.

    Retourne une MLPrediction stockée en base.
    """
    ml_model = MLModel.objects.filter(est_actif=True).first()

    # Cas 1 : pas de modèle entraîné → score froid
    if not ml_model or not ml_model.fichier_modele:
        return _prediction_froide(patient_id)

    # Charger le modèle
    try:
        modele_bytes = ml_model.fichier_modele.read()
        data = pickle.loads(modele_bytes)
        clf = data['model']
        feature_codes = data['feature_codes']
    except Exception as e:
        logger.error("Chargement modèle échoué : %s", e)
        return _prediction_froide(patient_id)

    # Extraire features du patient
    features = extraire_features_patient(patient_id)
    X = [[features.get(code, 0.0) for code in feature_codes]]

    # Prédire
    try:
        proba = clf.predict_proba(X)[0, 1]
    except Exception as e:
        logger.error("Inférence échouée : %s", e)
        return _prediction_froide(patient_id)

    # Features importantes
    importances = {}
    if hasattr(clf, 'feature_importances_'):
        top_idx = sorted(range(len(clf.feature_importances_)),
                         key=lambda i: -clf.feature_importances_[i])[:5]
        importances = {
            feature_codes[i]: float(clf.feature_importances_[i])
            for i in top_idx
        }

    # Stocker la prédiction
    pred = MLPrediction.objects.create(
        patient_id=patient_id,
        modele=ml_model,
        score_risque=float(proba),
        features_importantes=importances,
        analyses_utilisees=list(features.keys()),
    )
    return pred


def _prediction_froide(patient_id: int) -> MLPrediction:
    """Prédiction par défaut quand pas de modèle entraîné.

    Score = 0.3 (modéré) si le patient a des antécédents critiques,
    0.1 (faible) sinon.
    """
    patient = Patient.objects.get(pk=patient_id)
    score = 0.5 if patient.est_critique else 0.2
    return MLPrediction.objects.create(
        patient_id=patient_id,
        modele=None,
        score_risque=score,
        features_importantes={'note': 'modele_froid'},
        analyses_utilisees=[],
    )
