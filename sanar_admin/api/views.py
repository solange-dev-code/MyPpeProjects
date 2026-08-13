from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from patients.models import Patient
from appointments.models import RendezVous
from consultations.models import Consultation
from analyses.models import Analyse, TypeAnalyse, ResultatAnalyse
from facturation.models import Facture
from messagerie.models import Conversation, Message
from dossiers_medicaux.models import DossierMedical, Prescription
from medecins.models import Medecin, DisponibiliteMedecin
from medecins.services import creneaux_disponibles, verifier_conflit
from hopitaux.models import Hopital
from hopitaux.services import assigner_hopital
from urgences.models import DemandeUrgence, AccesUrgence
from urgences.services import hopital_optimal, trigger_notifications_urgence
from file_attente.models import FileAttente
from file_attente.services import (
    ordre_passage, estimer_temps_attente, marquer_en_consultation,
    marquer_termine, position_patient
)
from api.models import DeviceToken
from api.services import envoyer_push_fcm, envoyer_rappel_rdv
from .serializers import *

logger = logging.getLogger('sanar.api')


# ═══════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════
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

        # Vérifie si 2FA requis (médecin ou personnel)
        require_2fa = False
        if hasattr(user, 'medecin_profile') or hasattr(user, 'personnel'):
            require_2fa = not user.is_verified() if hasattr(user, 'is_verified') else False

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'patient': patient_data,
            'require_2fa': require_2fa,
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


# ═══════════════════════════════════════════════════════════════
# PATIENT
# ═══════════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════════
# RENDEZ-VOUS
# ═══════════════════════════════════════════════════════════════
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
        ).select_related('medecin', 'hopital')
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

        # ── NOUVEAU : vérification de conflit (anti double-booking) ──
        date_rdv = request.data.get('date')
        heure_rdv = request.data.get('heure')
        if date_rdv and heure_rdv and verifier_conflit(medecin.id, date_rdv, heure_rdv):
            return Response(
                {'error': 'Ce créneau est déjà réservé pour ce médecin. '
                          'Veuillez en choisir un autre.'},
                status=status.HTTP_409_CONFLICT
            )

        rdv = RendezVous.objects.create(
            patient=patient,
            medecin=medecin,
            hopital=hopital,
            date=date_rdv,
            heure=heure_rdv,
            motif=request.data.get('motif'),
            note=request.data.get('note', ''),
            statut='en_attente',
        )

        # Si le patient n'a pas encore d'hôpital assigné, on le rattache
        if hopital and not patient.hopital:
            patient.hopital = hopital
            patient.save()
        return Response(
            RendezVousSerializer(rdv).data,
            status=status.HTTP_201_CREATED
        )


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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analyses_list(request):
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)
    analyses = Analyse.objects.filter(patient=patient)
    return Response(AnalyseSerializer(analyses, many=True).data)


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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def factures_list(request):
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)
    factures = Facture.objects.filter(patient=patient)
    return Response(FactureSerializer(factures, many=True).data)


# ═══════════════════════════════════════════════════════════════
# MESSAGERIE
# ═══════════════════════════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversations_list(request):
    try:
        patient = Patient.objects.get(user=request.user)
        conversations = Conversation.objects.filter(patient=patient)
        data = []
        for conv in conversations:
            last_msg = conv.messages.last()
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def medecins_list(request):
    medecins = Medecin.objects.filter(est_actif=True)
    return Response(MedecinSerializer(medecins, many=True).data)


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


# ═══════════════════════════════════════════════════════════════
# NOUVEAU : URGENCES (bouton SOS Flutter)
# ═══════════════════════════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_urgence(request):
    """Déclenche une demande d'urgence (bouton SOS Flutter).

    Body: {niveau, latitude, longitude, description}
    """
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)

    niveau = request.data.get('niveau', 'P2')
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    description = request.data.get('description', '')

    if latitude is None or longitude is None:
        return Response(
            {'error': 'Position GPS requise (latitude, longitude)'},
            status=400
        )

    # Sélection automatique de l'hôpital optimal (Haversine + charge)
    hopital = hopital_optimal(float(latitude), float(longitude), niveau)

    urgence = DemandeUrgence.objects.create(
        patient=patient,
        hopital_destine=hopital,
        niveau=niveau,
        latitude=float(latitude),
        longitude=float(longitude),
        description=description,
        statut='en_attente',
    )

    # Déclenche les notifications (FCM + SMS + WhatsApp) à l'équipe d'astreinte
    trigger_notifications_urgence(urgence)

    return Response(
        DemandeUrgenceSerializer(urgence).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_urgences(request):
    """Liste les demandes d'urgence du patient connecté."""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)
    urgences = DemandeUrgence.objects.filter(patient=patient)
    return Response(DemandeUrgenceSerializer(urgences, many=True).data)


# ═══════════════════════════════════════════════════════════════
# NOUVEAU : Accès d'urgence par QR code (PUBLIC, audit RGPD)
# ═══════════════════════════════════════════════════════════════
@api_view(['GET'])
@permission_classes([AllowAny])  # PUBLIC — mais token UUID opaque
def acces_urgence_publique(request, token):
    """Endpoint PUBLIC d'accès d'urgence par QR code.

    Permet à un secouriste de récupérer les données vitales d'un patient
    inconscient en scannant son QR code médical.

    Sécurité :
    - Token UUID opaque (non devinable)
    - Audit trail obligatoire (AccesUrgence)
    - Rate limit : à implémenter via django-ratelimit (max 10/h par IP)
    - Données restreintes : pas d'historique complet ni notes libres
    """
    try:
        patient = Patient.objects.select_related('user').get(
            token_urgence=token, urgence_qr_actif=True
        )
    except (Patient.DoesNotExist, ValueError):
        return Response({'error': 'Token invalide ou révoqué'}, status=404)

    # Journalisation obligatoire (audit RGPD)
    acces = AccesUrgence.objects.create(
        patient=patient,
        source_ip=request.META.get('REMOTE_ADDR', '0.0.0.0'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        referer=request.META.get('HTTP_REFERER', ''),
    )

    # Notifie le patient qu'un accès a eu lieu
    try:
        from urgences.services import notifier_patient_acces_urgence
        notifier_patient_acces_urgence(acces)
    except Exception:
        pass

    # Récupère prescriptions actives
    prescriptions_actives = []
    try:
        dossier = DossierMedical.objects.get(patient=patient)
        prescriptions_actives = [
            {'medicament': p.medicament, 'posologie': p.posologie, 'duree': p.duree}
            for p in dossier.prescriptions.filter(est_active=True)
        ]
        medecin_referent = dossier.medecin_referent
    except DossierMedical.DoesNotExist:
        medecin_referent = None

    return Response({
        'nom': patient.nom,
        'prenom': patient.prenom,
        'date_naissance': patient.date_naissance.isoformat(),
        'groupe_sanguin': patient.groupe_sanguin,
        'allergies': patient.allergies,
        'traitements_actifs': prescriptions_actives,
        'medecin_referent': (
            {
                'nom': f"Dr. {medecin_referent.prenom} {medecin_referent.nom}",
                'specialite': medecin_referent.get_specialite_display(),
                'telephone': medecin_referent.telephone,
            } if medecin_referent else None
        ),
        'patient_telephone': patient.telephone,
        'hopital': (
            {
                'nom': patient.hopital.nom,
                'telephone': patient.hopital.telephone,
            } if patient.hopital else None
        ),
        'acces_id': acces.id,
        'acces_timestamp': acces.created_at.isoformat(),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerer_qr_urgence(request):
    """Révoque l'ancien token et en génère un nouveau (en cas de fuite)."""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)
    nouveau_token = patient.regenerer_token_urgence()
    return Response({
        'message': 'QR code régénéré. L\'ancien token est révoqué.',
        'token_urgence': str(nouveau_token),
        'qr_url': f'/api/urgence/{nouveau_token}/'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_qr_urgence(request):
    """Active ou désactive le QR code d'urgence."""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)
    patient.urgence_qr_actif = not patient.urgence_qr_actif
    patient.save()
    return Response({
        'urgence_qr_actif': patient.urgence_qr_actif,
        'message': 'QR code activé' if patient.urgence_qr_actif
                   else 'QR code désactivé'
    })


# ═══════════════════════════════════════════════════════════════
# NOUVEAU : FILE D'ATTENTE (côté patient)
# ═══════════════════════════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ma_file_attente(request):
    """Renvoie la position du patient dans la file d'attente de son hôpital."""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)

    try:
        entry = FileAttente.objects.get(
            patient=patient, statut='en_attente'
        )
        return Response(FileAttenteSerializer(entry).data)
    except FileAttente.DoesNotExist:
        return Response({'message': 'Vous n\'êtes pas en file d\'attente'},
                        status=404)


# ═══════════════════════════════════════════════════════════════
# NOUVEAU : CRÉNEAUX DISPONIBLES (gestion disponibilités médecin)
# ═══════════════════════════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def creneaux_medecin(request, medecin_id):
    """Renvoie les créneaux réservables d'un médecin pour une date donnée.

    Query param: ?date=2026-08-20
    """
    date_str = request.GET.get('date')
    if not date_str:
        return Response({'error': 'Paramètre date requis (YYYY-MM-DD)'},
                        status=400)
    try:
        date_cible = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Format date invalide (YYYY-MM-DD)'},
                        status=400)

    creneaux = creneaux_disponibles(medecin_id, date_cible)
    return Response(creneaux)


# ═══════════════════════════════════════════════════════════════
# NOUVEAU : ASSIGNATION MULTI-HÔPITAUX
# ═══════════════════════════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assigner_patient(request):
    """Assigne automatiquement le meilleur hôpital au patient.

    Body: {specialite?, latitude?, longitude?, niveau_urgence?}
    """
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)

    specialite = request.data.get('specialite')
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    niveau_urgence = request.data.get('niveau_urgence', 'P3')

    hopital = assigner_hopital(
        patient,
        specialite_requise=specialite,
        latitude=float(latitude) if latitude else None,
        longitude=float(longitude) if longitude else None,
        niveau_urgence=niveau_urgence,
    )

    if not hopital:
        return Response(
            {'error': 'Aucun hôpital disponible pour ces critères'},
            status=404
        )

    # Temps d'attente estimé
    temps_estime = estimer_temps_attente(
        hopital.id, niveau=4  # P4 par défaut
    )

    return Response({
        'hopital_id': hopital.id,
        'hopital_nom': hopital.nom,
        'hopital_telephone': hopital.telephone,
        'hopital_adresse': hopital.adresse,
        'hopital_ville': hopital.ville,
        'temps_attente_estime': temps_estime,
    })


# ═══════════════════════════════════════════════════════════════
# NOUVEAU : EXPORTS (PDF / CSV / FHIR)
# ═══════════════════════════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_mon_dossier_pdf(request):
    """Export PDF du dossier médical du patient connecté."""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)

    from exports.services import export_dossier_pdf
    pdf_bytes = export_dossier_pdf(patient)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="dossier_{patient.patient_id}.pdf"'
    )
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_mon_dossier_fhir(request):
    """Export FHIR R4 (JSON) du dossier patient."""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient non trouvé'}, status=404)

    from exports.services import export_dossier_fhir
    bundle = export_dossier_fhir(patient)
    return JsonResponse(bundle, json_dumps_params={'indent': 2,
                                                    'ensure_ascii': False})


# ═══════════════════════════════════════════════════════════════
# NOUVEAU : TOKEN FCM (notifications push)
# ═══════════════════════════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_device_token(request):
    """Enregistre un token FCM pour l'utilisateur connecté.

    Body: {token, platform}
    À appeler à chaque ouverture de l'app Flutter.
    """
    token = request.data.get('token')
    platform = request.data.get('platform', 'android')
    if not token:
        return Response({'error': 'Token requis'}, status=400)

    device, created = DeviceToken.objects.update_or_create(
        user=request.user, token=token,
        defaults={'platform': platform, 'is_active': True}
    )
    return Response({
        'id': device.id,
        'created': created,
        'message': 'Token enregistré'
    }, status=status.HTTP_201_CREATED if created else 200)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unregister_device_token(request, token):
    """Désactive un token FCM (à l'app logout)."""
    deleted, _ = DeviceToken.objects.filter(
        user=request.user, token=token
    ).delete()
    if deleted:
        return Response({'message': 'Token supprimé'})
    return Response({'error': 'Token non trouvé'}, status=404)


# ═══════════════════════════════════════════════════════════════
# NOUVEAU : 2FA TOTP (pour médecins / personnel)
# ═══════════════════════════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setup_2fa(request):
    """Génère un secret TOTP + QR code pour activer le 2FA.

    Retourne :
    - secret : à saisir manuellement dans l'app TOTP
    - qr_url : URL otpauth à scanner
    - qr_image_base64 : image QR code en base64
    """
    if not (hasattr(request.user, 'medecin_profile')
            or hasattr(request.user, 'personnel')):
        return Response(
            {'error': '2FA réservé aux médecins et personnel'},
            status=403
        )

    from django_otp.plugins.otp_totp.models import TOTPDevice
    import qrcode
    import qrcode.image.svg
    import base64
    import io

    # Désactive anciens devices non confirmés
    TOTPDevice.objects.filter(user=request.user, confirmed=False).delete()

    device = TOTPDevice.objects.create(
        user=request.user, name='Sanar TOTP', confirmed=False
    )

    # Génère l'URL otpauth
    otpauth_url = device.config_url

    # Génère le QR code en SVG → base64
    factory = qrcode.image.svg.SvgImage
    img = qrcode.make(otpauth_url, image_factory=factory)
    buffer = io.BytesIO()
    img.save(buffer)
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()

    return Response({
        'secret': device.bin_key.hex(),  # pour saisie manuelle
        'otpauth_url': otpauth_url,
        'qr_image_base64': qr_b64,
        'message': 'Scannez ce QR code avec Google Authenticator, '
                   'puis confirmez avec /api/2fa/verify/'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_2fa(request):
    """Vérifie un code TOTP et confirme le 2FA.

    Body: {code: '123456'}
    """
    from django_otp.plugins.otp_totp.models import TOTPDevice

    code = request.data.get('code', '').strip()
    if not code:
        return Response({'error': 'Code requis'}, status=400)

    device = TOTPDevice.objects.filter(
        user=request.user, confirmed=False
    ).first()
    if not device:
        return Response({'error': 'Aucun 2FA en attente. Appelez /api/2fa/setup/'},
                        status=404)

    if device.verify_token(code):
        device.confirmed = True
        device.save()
        return Response({'message': '2FA activé avec succès'})
    else:
        return Response({'error': 'Code invalide'}, status=400)


# ═══════════════════════════════════════════════════════════════
# NOUVEAU : RAPPELS RDV (tâche déclenchable manuellement pour test)
# ═══════════════════════════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_notification(request):
    """Envoie une notification push de test au patient connecté.

    Utile pour vérifier que le token FCM est bien enregistré.
    """
    tokens = list(
        DeviceToken.objects.filter(
            user=request.user, is_active=True
        ).values_list('token', flat=True)
    )
    if not tokens:
        return Response({'error': 'Aucun token FCM enregistré'}, status=404)

    result = envoyer_push_fcm(
        tokens=tokens,
        titre='Test Sanar',
        corps='Notification de test — votre appareil est bien enregistré.',
        data={'type': 'test'}
    )
    return Response(result)
