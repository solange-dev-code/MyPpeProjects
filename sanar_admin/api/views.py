from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from patients.models import Patient
from appointments.models import RendezVous 
from consultations.models import Consultation
from analyses.models import Analyse
from facturation.models import Facture
from messagerie.models import Conversation, Message
from dossiers_medicaux.models import DossierMedical
from .serializers import *
from medecins.models import Medecin
from hopitaux.models import Hopital

# AUTH
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username') or request.data.get('email')
    password = request.data.get('password')

    # Connexion par email
    try:
        user_obj = User.objects.get(email=username)
        username = user_obj.username
    except User.DoesNotExist:
        pass

    user = authenticate(username=username, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        try:
            patient = Patient.objects.get(user=user)
            patient_data = PatientSerializer(patient).data
        except Patient.DoesNotExist:
            patient_data = None
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'patient': patient_data,
        })
    return Response(
        {'error': 'Identifiants incorrects'},
        status=status.HTTP_401_UNAUTHORIZED
    )

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        patient = Patient.objects.get(user=user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'patient': PatientSerializer(patient).data,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# PATIENT
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def patient_profile(request):
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)

    if request.method == 'GET':
        return Response(PatientSerializer(patient).data)
    elif request.method == 'PUT':
        serializer = PatientSerializer(patient, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

# RENDEZ-VOUS
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def rendez_vous_list(request):
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)

    if request.method == 'GET':
        rdvs = RendezVous.objects.filter(
            patient=patient
        ).select_related('medecin')
        return Response(RendezVousSerializer(rdvs, many=True).data)

    elif request.method == 'POST':
        try:
            medecin = Medecin.objects.get(pk=request.data.get('medecin_id'))
        except Medecin.DoesNotExist:
            return Response({'error': 'Médecin non trouvé'}, status=404)

        hopital = None
        hopital_id = request.data.get('hopital_id')
        if hopital_id:
            try:
                hopital = Hopital.objects.get(pk=hopital_id)
            except Hopital.DoesNotExist:
                return Response({'error': 'Hôpital non trouvé'}, status=404)

       
        rdv = RendezVous.objects.create(
            patient=patient,
            medecin=medecin,
            hopital=hopital,
            date=request.data.get('date'),
            heure=request.data.get('heure'),
            motif=request.data.get('motif'),
            note=request.data.get('note', ''),
            statut='en_attente',
        )

        # Si le patient n'a pas encore d'hôpital assigné, on le rattache à celui-ci
        if hopital and not patient.hopital:
            patient.hopital = hopital
            patient.save()
        return Response(
            RendezVousSerializer(rdv).data,
            status=status.HTTP_201_CREATED
        )
# HOPITAUX
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hopitaux_list(request):
    hopitaux = Hopital.objects.filter(actif=True)
    return Response(HopitalSerializer(hopitaux, many=True).data)

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def rendez_vous_detail(request, pk):
    try:
        patient = Patient.objects.get(user=request.user)
        rdv = RendezVous.objects.get(pk=pk, patient=patient)
    except (Patient.DoesNotExist, RendezVous.DoesNotExist):
        return Response({'error': 'Non trouvé'}, status=404)

    if request.method == 'PUT':
        rdv.statut = request.data.get('statut', rdv.statut)
        rdv.save()
        return Response(RendezVousSerializer(rdv).data)
    elif request.method == 'DELETE':
        rdv.statut = 'annule'
        rdv.save()
        return Response({'message': 'Rendez-vous annulé'})

# CONSULTATIONS
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def consultations_list(request):
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)
    consultations = Consultation.objects.filter(
        patient=patient
    ).select_related('medecin')
    return Response(ConsultationSerializer(consultations, many=True).data)

# ANALYSES
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analyses_list(request):
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)
    analyses = Analyse.objects.filter(patient=patient)
    return Response(AnalyseSerializer(analyses, many=True).data)

# DOSSIER MEDICAL
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dossier_medical(request):
    try:
        patient = Patient.objects.get(user=request.user)
        dossier = DossierMedical.objects.get(patient=patient)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)
    except DossierMedical.DoesNotExist:
        return Response({'error': 'Dossier non trouvé'}, status=404)
    return Response(DossierMedicalSerializer(dossier).data)

# FACTURATION
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def factures_list(request):
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)
    factures = Facture.objects.filter(patient=patient)
    return Response(FactureSerializer(factures, many=True).data)

# MESSAGERIE
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversations_list(request):
    try:
        patient = Patient.objects.get(user=request.user)
        conversations = Conversation.objects.filter(patient=patient)
        data = []
        for conv in conversations:
            # Dernier message
            last_msg = conv.messages.last()
            # Nom à afficher = admin/médecin qui a écrit
            admin_msgs = conv.messages.exclude(expediteur=request.user)
            nom_affiche = 'Équipe Sanar'
            if admin_msgs.exists():
                exp = admin_msgs.last().expediteur
                nom_affiche = exp.get_full_name() or exp.username

            data.append({
                'id': conv.pk,
                'nom': nom_affiche,
                'type_contact': conv.type_contact,
                'get_type_contact_display': conv.get_type_contact_display(),
                'dernier_message': last_msg.contenu if last_msg else None,
                'updated_at': str(conv.updated_at),
                'patient': conv.patient.pk if conv.patient else None,
            })
        return Response(data)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def messages_list(request, conv_id):
    try:
        conv = Conversation.objects.get(pk=conv_id)
    except Conversation.DoesNotExist:
        return Response({'error': 'Conversation non trouvée'}, status=404)

    if request.method == 'GET':
        msgs = conv.messages.all().order_by('created_at')
        data = []
        for msg in msgs:
            data.append({
                'id': msg.pk,
                'contenu': msg.contenu,
                'created_at': str(msg.created_at),
                'expediteur_nom': msg.expediteur.get_full_name() or msg.expediteur.username,
                'est_moi': msg.expediteur == request.user,
            })
        return Response(data)

    elif request.method == 'POST':
        contenu = request.data.get('contenu', '').strip()
        if not contenu:
            return Response({'error': 'Message vide'}, status=400)
        msg = Message.objects.create(
            conversation=conv,
            expediteur=request.user,
            contenu=contenu,
        )
        return Response({
            'id': msg.pk,
            'contenu': msg.contenu,
            'created_at': str(msg.created_at),
            'est_moi': True,
        }, status=status.HTTP_201_CREATED)
    
# MEDECINS
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def medecins_list(request):
    medecins = Medecin.objects.all()
    return Response(MedecinSerializer(medecins, many=True).data)

# NOTIFICATIONS
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications_list(request):
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)

    notifications = []

    rdvs = RendezVous.objects.filter(
        patient=patient, statut='confirme'
    ).order_by('-created_at')[:3]
    for rdv in rdvs:
        notifications.append({
            'type': 'rdv',
            'titre': 'Rendez-vous confirmé',
            'message': f'Dr. {rdv.medecin.nom} — {rdv.date} à {rdv.heure}',
            'date': str(rdv.created_at),
        })

    analyses = Analyse.objects.filter(
        patient=patient, statut='disponible'
    ).order_by('-created_at')[:3]
    for analyse in analyses:
        notifications.append({
            'type': 'analyse',
            'titre': 'Résultats disponibles',
            'message': f'{analyse.get_type_analyse_display()} disponible',
            'date': str(analyse.created_at),
        })

    factures = Facture.objects.filter(
        patient=patient, statut='en_attente'
    ).order_by('-date_facture')[:3]
    for facture in factures:
        notifications.append({
            'type': 'facture',
            'titre': 'Facture en attente',
            'message': f'{facture.montant_total} FCFA à payer',
            'date': str(facture.date_facture),
        })

    return Response(notifications)