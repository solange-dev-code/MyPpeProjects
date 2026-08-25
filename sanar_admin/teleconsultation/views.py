"""Vues API REST pour la téléconsultation."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Teleconsultation
from patients.models import Patient
from medecins.models import Medecin
from api.services import envoyer_push_fcm


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def creer_teleconsultation(request):
    """Crée une session de téléconsultation.

    Body: {patient_id, medecin_id?, date_planifiee?}
    Retourne: room_uuid à partager avec les deux parties.
    """
    patient_id = request.data.get('patient_id')
    medecin_id = request.data.get('medecin_id')
    date_planifiee = request.data.get('date_planifiee')

    try:
        patient = Patient.objects.get(pk=patient_id)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)

    # Si medecin_id non fourni, utiliser le médecin référent du dossier
    if not medecin_id:
        try:
            medecin = patient.dossiermedical.medecin_referent
            if not medecin:
                return Response({'error': 'Aucun médecin référent'}, status=400)
        except Exception:
            return Response({'error': 'Aucun médecin référent'}, status=400)
    else:
        medecin = get_object_or_404(Medecin, pk=medecin_id)

    tc = Teleconsultation.objects.create(
        patient=patient,
        medecin=medecin,
        initiateur=request.user,
        date_planifiee=date_planifiee or timezone.now(),
        statut='planifiee',
    )

    # Notifier le patient (push FCM)
    try:
        from api.models import DeviceToken
        tokens = list(
            DeviceToken.objects.filter(
                user=patient.user, is_active=True
            ).values_list('token', flat=True)
        )
        if tokens:
            envoyer_push_fcm(
                tokens=tokens,
                titre='Téléconsultation',
                corps=f"Dr. {medecin.prenom} {medecin.nom} vous appelle en téléconsultation",
                data={
                    'type': 'teleconsultation',
                    'room_uuid': str(tc.room_uuid),
                }
            )
    except Exception:
        pass

    return Response({
        'room_uuid': str(tc.room_uuid),
        'patient': f"{patient.prenom} {patient.nom}",
        'medecin': f"Dr. {medecin.prenom} {medecin.nom}",
        'statut': tc.statut,
        'ws_url': f'/ws/teleconsultation/{tc.room_uuid}/',
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def demarrer_teleconsultation(request, room_uuid):
    """Marque la téléconsultation comme en cours (appelé quand le 2e participant rejoint)."""
    tc = get_object_or_404(Teleconsultation, room_uuid=room_uuid)
    if tc.statut not in ('planifiee', 'en_cours'):
        return Response({'error': f'Téléconsultation {tc.statut}'}, status=400)
    tc.statut = 'en_cours'
    tc.date_debut = timezone.now()
    tc.save()
    return Response({'statut': tc.statut, 'date_debut': tc.date_debut.isoformat()})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def terminer_teleconsultation(request, room_uuid):
    """Termine la téléconsultation."""
    tc = get_object_or_404(Teleconsultation, room_uuid=room_uuid)
    tc.statut = 'terminee'
    tc.date_fin = timezone.now()
    if tc.date_debut:
        tc.duree_secondes = int((tc.date_fin - tc.date_debut).total_seconds())
    tc.save()
    return Response({
        'statut': tc.statut,
        'duree_secondes': tc.duree_secondes,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_teleconsultations(request):
    """Liste les téléconsultations de l'utilisateur (médecin ou patient)."""
    user = request.user
    if hasattr(user, 'medecin_profile'):
        tcs = Teleconsultation.objects.filter(medecin=user.medecin_profile)
    elif hasattr(user, 'patient'):
        tcs = Teleconsultation.objects.filter(patient=user.patient)
    else:
        return Response({'error': 'Utilisateur ni médecin ni patient'}, status=403)

    return Response([{
        'room_uuid': str(tc.room_uuid),
        'patient': f"{tc.patient.prenom} {tc.patient.nom}",
        'medecin': f"Dr. {tc.medecin.prenom} {tc.medecin.nom}",
        'statut': tc.statut,
        'date_planifiee': tc.date_planifiee.isoformat() if tc.date_planifiee else None,
        'date_debut': tc.date_debut.isoformat() if tc.date_debut else None,
        'date_fin': tc.date_fin.isoformat() if tc.date_fin else None,
        'duree_secondes': tc.duree_secondes,
    } for tc in tcs])
