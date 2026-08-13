from rest_framework import serializers
from django.contrib.auth.models import User
from patients.models import Patient
from appointments.models import RendezVous
from consultations.models import Consultation
from analyses.models import Analyse
from facturation.models import Facture
from messagerie.models import Conversation, Message
from dossiers_medicaux.models import DossierMedical, Prescription
from medecins.models import Medecin
from hopitaux.models import Hopital 

class HopitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hopital
        fields = ['id', 'nom', 'adresse', 'ville', 'telephone', 'latitude', 'longitude']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'

class MedecinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medecin
        fields = '__all__'

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

class AnalyseSerializer(serializers.ModelSerializer):
    patient_nom = serializers.SerializerMethodField()
    type_display = serializers.SerializerMethodField()

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