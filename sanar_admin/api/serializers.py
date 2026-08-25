from rest_framework import serializers
from django.contrib.auth.models import User
from patients.models import Patient
from appointments.models import RendezVous
from consultations.models import Consultation
from analyses.models import Analyse, TypeAnalyse, ResultatAnalyse
from facturation.models import Facture
from messagerie.models import Conversation, Message
from dossiers_medicaux.models import DossierMedical, Prescription
from medecins.models import Medecin, DisponibiliteMedecin
from hopitaux.models import Hopital, LitHopital
from urgences.models import DemandeUrgence
from file_attente.models import FileAttente
from api.models import DeviceToken


class HopitalSerializer(serializers.ModelSerializer):
    lits_disponibles = serializers.SerializerMethodField()

    class Meta:
        model = Hopital
        fields = ['id', 'nom', 'adresse', 'ville', 'telephone', 'email',
                  'latitude', 'longitude', 'actif', 'lits_disponibles']

    def get_lits_disponibles(self, obj):
        return sum(l.disponibles for l in obj.lits.all())


class LitHopitalSerializer(serializers.ModelSerializer):
    disponibles = serializers.ReadOnlyField()
    taux_occupation = serializers.ReadOnlyField()

    class Meta:
        model = LitHopital
        fields = ['id', 'hopital', 'service', 'total', 'occupes',
                  'disponibles', 'taux_occupation']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'user', 'nom', 'prenom', 'email', 'telephone',
                  'date_naissance', 'adresse', 'groupe_sanguin', 'allergies',
                  'poids', 'taille', 'patient_id', 'date_inscription',
                  'est_critique', 'hopital', 'token_urgence',
                  'urgence_qr_actif']
        read_only_fields = ['token_urgence', 'patient_id', 'date_inscription']


class MedecinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medecin
        fields = '__all__'


class DisponibiliteMedecinSerializer(serializers.ModelSerializer):
    jour_display = serializers.SerializerMethodField()

    class Meta:
        model = DisponibiliteMedecin
        fields = ['id', 'medecin', 'hopital', 'jour_semaine', 'jour_display',
                  'heure_debut', 'heure_fin', 'duree_creneau', 'actif']

    def get_jour_display(self, obj):
        return obj.get_jour_semaine_display()


class RendezVousSerializer(serializers.ModelSerializer):
    patient_nom = serializers.SerializerMethodField()
    medecin_nom = serializers.SerializerMethodField()
    medecin_specialite = serializers.SerializerMethodField()

    class Meta:
        model = RendezVous
        fields = '__all__'

    def get_patient_nom(self, obj):
        return f"{obj.patient.prenom} {obj.patient.nom}"

    def get_medecin_nom(self, obj):
        return f"Dr. {obj.medecin.prenom} {obj.medecin.nom}"

    def get_medecin_specialite(self, obj):
        return obj.medecin.get_specialite_display()


class ConsultationSerializer(serializers.ModelSerializer):
    patient_nom = serializers.SerializerMethodField()
    medecin_nom = serializers.SerializerMethodField()
    medecin_specialite = serializers.SerializerMethodField()

    class Meta:
        model = Consultation
        fields = '__all__'

    def get_patient_nom(self, obj):
        return f"{obj.patient.prenom} {obj.patient.nom}"

    def get_medecin_nom(self, obj):
        return f"Dr. {obj.medecin.prenom} {obj.medecin.nom}"

    def get_medecin_specialite(self, obj):
        return obj.medecin.get_specialite_display()


class TypeAnalyseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeAnalyse
        fields = '__all__'


class ResultatAnalyseSerializer(serializers.ModelSerializer):
    type_analyse_code = serializers.SerializerMethodField()

    class Meta:
        model = ResultatAnalyse
        fields = ['id', 'analyse', 'type_analyse', 'type_analyse_code',
                  'valeur', 'unite', 'flag', 'valeur_normale_basse',
                  'valeur_normale_haute', 'created_at']
        read_only_fields = ['flag', 'created_at']

    def get_type_analyse_code(self, obj):
        return obj.type_analyse.code


class AnalyseSerializer(serializers.ModelSerializer):
    patient_nom = serializers.SerializerMethodField()
    type_display = serializers.SerializerMethodField()
    resultats = ResultatAnalyseSerializer(many=True, read_only=True)

    class Meta:
        model = Analyse
        fields = '__all__'

    def get_patient_nom(self, obj):
        return f"{obj.patient.prenom} {obj.patient.nom}"

    def get_type_display(self, obj):
        return obj.get_type_analyse_display()


class FactureSerializer(serializers.ModelSerializer):
    patient_nom = serializers.SerializerMethodField()
    moyen_paiement_display = serializers.SerializerMethodField()

    class Meta:
        model = Facture
        fields = '__all__'

    def get_patient_nom(self, obj):
        return f"{obj.patient.prenom} {obj.patient.nom}"

    def get_moyen_paiement_display(self, obj):
        return obj.get_moyen_paiement_display()


class MessageSerializer(serializers.ModelSerializer):
    expediteur_nom = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = '__all__'

    def get_expediteur_nom(self, obj):
        return obj.expediteur.get_full_name() or obj.expediteur.username


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    dernier_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = '__all__'

    def get_dernier_message(self, obj):
        last = obj.messages.last()
        return last.contenu if last else None


class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = '__all__'


class DossierMedicalSerializer(serializers.ModelSerializer):
    patient_info = PatientSerializer(source='patient', read_only=True)
    prescriptions = PrescriptionSerializer(many=True, read_only=True)

    class Meta:
        model = DossierMedical
        fields = '__all__'


# ──────────────────────────────────────────────────────────────
# Nouveaux serializers (améliorations)
# ──────────────────────────────────────────────────────────────
class DemandeUrgenceSerializer(serializers.ModelSerializer):
    patient_nom = serializers.SerializerMethodField()
    patient_groupe_sanguin = serializers.SerializerMethodField()
    patient_allergies = serializers.SerializerMethodField()
    patient_telephone = serializers.SerializerMethodField()
    hopital_nom = serializers.SerializerMethodField()

    class Meta:
        model = DemandeUrgence
        fields = ['uuid', 'patient', 'patient_nom', 'patient_groupe_sanguin',
                  'patient_allergies', 'patient_telephone',
                  'hopital_destine', 'hopital_nom', 'niveau', 'latitude',
                  'longitude', 'description', 'statut', 'temps_reponse',
                  'created_at', 'pris_en_charge_at']
        read_only_fields = ['uuid', 'hopital_destine', 'temps_reponse',
                            'created_at', 'pris_en_charge_at']

    def get_patient_nom(self, obj):
        return f"{obj.patient.prenom} {obj.patient.nom}"

    def get_patient_groupe_sanguin(self, obj):
        return obj.patient.groupe_sanguin

    def get_patient_allergies(self, obj):
        return obj.patient.allergies

    def get_patient_telephone(self, obj):
        return obj.patient.telephone

    def get_hopital_nom(self, obj):
        return obj.hopital_destine.nom if obj.hopital_destine else None


class FileAttenteSerializer(serializers.ModelSerializer):
    patient_nom = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()

    class Meta:
        model = FileAttente
        fields = ['id', 'patient', 'patient_nom', 'hopital', 'medecin',
                  'niveau_triage', 'statut', 'motif', 'arrivee_at',
                  'temps_attente_estime', 'position']

    def get_patient_nom(self, obj):
        return f"{obj.patient.prenom} {obj.patient.nom}"

    def get_position(self, obj):
        from file_attente.services import position_patient
        if obj.statut == 'en_attente':
            return position_patient(obj)
        return None


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['id', 'token', 'platform', 'is_active', 'created_at']
        read_only_fields = ['is_active', 'created_at']


class CreneauDisponibleSerializer(serializers.Serializer):
    """Serializer pour un créneau disponible (pas un modèle Django)."""
    heure = serializers.CharField()
    hopital_id = serializers.IntegerField()
    medecin_id = serializers.IntegerField()
    disponible = serializers.BooleanField()


class AssignationHopitalSerializer(serializers.Serializer):
    """Serializer pour la réponse d'assignation multi-hôpitaux."""
    hopital_id = serializers.IntegerField()
    hopital_nom = serializers.CharField()
    hopital_telephone = serializers.CharField()
    temps_attente_estime = serializers.IntegerField()
    distance_km = serializers.FloatField()
    score = serializers.FloatField()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    nom = serializers.CharField(write_only=True)
    prenom = serializers.CharField(write_only=True)
    telephone = serializers.CharField(write_only=True)
    date_naissance = serializers.DateField(write_only=True)
    adresse = serializers.CharField(write_only=True)
    groupe_sanguin = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password',
            'nom', 'prenom', 'telephone',
            'date_naissance', 'adresse', 'groupe_sanguin'
        ]

    def create(self, validated_data):
        import random
        nom = validated_data.pop('nom')
        prenom = validated_data.pop('prenom')
        telephone = validated_data.pop('telephone')
        date_naissance = validated_data.pop('date_naissance')
        adresse = validated_data.pop('adresse')
        groupe_sanguin = validated_data.pop('groupe_sanguin')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=password,
            first_name=prenom,
            last_name=nom,
        )

        Patient.objects.create(
            user=user,
            nom=nom,
            prenom=prenom,
            email=validated_data.get('email', ''),
            telephone=telephone,
            date_naissance=date_naissance,
            adresse=adresse,
            groupe_sanguin=groupe_sanguin,
            patient_id=f"KM{random.randint(2026000, 2026999)}",
        )
        return user
