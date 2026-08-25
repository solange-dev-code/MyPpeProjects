"""Vues API REST pour les prédictions ML."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from patients.models import Patient
from .models import MLPrediction, MLModel
from .services import predire_risque_patient, entrainer_modele


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def prediction_courante(request):
    """Retourne la dernière prédiction ML pour le patient connecté.

    Déclenche une nouvelle prédiction si aucune prédiction < 24h n'existe.
    """
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)

    # Dernière prédiction < 24h
    from django.utils import timezone
    from datetime import timedelta
    recentes = MLPrediction.objects.filter(
        patient=patient,
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-created_at')

    if recentes.exists():
        pred = recentes.first()
    else:
        pred = predire_risque_patient(patient.id)

    return Response({
        'score_risque': round(pred.score_risque, 3),
        'niveau_risque': pred.niveau_risque,
        'features_importantes': pred.features_importantes,
        'analyses_utilisees': pred.analyses_utilisees,
        'modele_version': pred.modele.version if pred.modele else None,
        'date_prediction': pred.created_at.isoformat(),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def entrainer_modele_view(request):
    """Déclenche l'entraînement d'un nouveau modèle ML.

    Réservé super_admin.
    """
    personnel = getattr(request.user, 'personnel', None)
    if personnel is None or personnel.role != 'super_admin':
        return Response({'error': 'Réservé super admin'}, status=403)

    modele = entrainer_modele()
    if not modele:
        return Response({
            'error': 'Données insuffisantes pour entraîner (min 10 patients avec analyses)'
        }, status=400)

    return Response({
        'version': modele.version,
        'precision': modele.precision,
        'rappel': modele.rappel,
        'auc': modele.auc,
        'hyperparametres': modele.hyperparametres,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_modeles(request):
    """Liste tous les modèles ML entraînés."""
    modeles = MLModel.objects.all().order_by('-date_entrainement')
    return Response([{
        'version': m.version,
        'date_entrainement': m.date_entrainement.isoformat(),
        'precision': m.precision,
        'rappel': m.rappel,
        'auc': m.auc,
        'est_actif': m.est_actif,
        'n_patients': m.hyperparametres.get('n_patients', 0),
    } for m in modeles])
