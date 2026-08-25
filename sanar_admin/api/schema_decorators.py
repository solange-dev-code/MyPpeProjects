"""
Schémas OpenAPI/Swagger centralisés pour l'API Sanar.

Ce module contient des décorateurs ``drf_spectacular`` réutilisables qui
documentent les endpoints majeurs de l'API REST (40+ endpoints répartis
sur 14 apps Django). La configuration globale drf-spectacular est déjà en
place dans ``sanar_admin/settings.py`` (SPECTACULAR_SETTINGS) et
``sanar_admin/urls.py`` (/api/schema/, /api/docs/, /api/redoc/).

Chaque endpoint majeur expose DEUX artefacts complémentaires :

1. ``XXX_SCHEMA`` — un appel direct à ``extend_schema(...)`` applicable sur
   une vue fonctionnelle (FBV) via ``@api_view``. C'est la forme adaptée
   aux vues existantes de ``api/views.py`` qui sont toutes fonctionnelles.

2. ``XXXViewSchema`` — un ``extend_schema_view(...)`` applicable sur une
   vue basée classe (CBV). Fourni pour les futures migrations FBV → CBV
   et pour la cohérence avec le pattern demandé dans le cahier des charges.

Application immédiate (sans toucher au code métier) :

    # Pour une vue fonctionnelle (cas actuel) :
    from api.schema_decorators import LOGIN_SCHEMA

    @LOGIN_SCHEMA
    @api_view(['POST'])
    @permission_classes([AllowAny])
    def login_view(request):
        ...

    # Pour une vue basée classe (migration future) :
    from api.schema_decorators import LoginViewSchema

    @LoginViewSchema
    class LoginView(APIView):
        permission_classes = [AllowAny]

        def post(self, request):
            ...

Les schémas sont volontairement riches (summary + description + tags +
request inline + responses multi-statuts + exemples request/response) afin
que le Swagger UI généré sur /api/docs/ soit directement utilisable par
les intégrateurs Flutter (app patient ``sanar`` et app médecin
``sanar_medecin``) et les partenaires externes (exports FHIR).

Conventions :
- Tags : utiliser exclusivement les valeurs de ``API_TAGS`` (ordre garanti).
- Erreurs : étendre ``STANDARD_ERROR_RESPONSES`` via ``_errors(401, 404)``
  pour éviter la duplication des schémas d'erreur 401/403/404/409/500.
- Exemples : préfixer par ``XXX_REQUEST_EXAMPLE`` / ``XXX_RESPONSE_EXAMPLE``
  pour les rendre réutilisables dans la doc externe.
"""

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)
from rest_framework import status

# ═══════════════════════════════════════════════════════════════════════════
# 1. TAGS OPENAPI — ordre garanti pour le Swagger UI
# ═══════════════════════════════════════════════════════════════════════════
API_TAGS = [
    'Authentification',
    'Patient',
    'Rendez-vous',
    'Urgences',
    "File d'attente",
    'Analyses',
    'Dossier médical',
    'Téléconsultation',
    'ML Prédictions',
    'Exports',
    'RGPD',
    'Sécurité 2FA',
    'Notifications',
    'Monitoring',
]

# ═══════════════════════════════════════════════════════════════════════════
# 2. RÉPONSES D'ERREUR STANDARD — mutualisées sur tous les endpoints
# ═══════════════════════════════════════════════════════════════════════════
STANDARD_ERROR_RESPONSES = {
    400: {
        'description': 'Requête malformée — paramètres manquants ou invalides',
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'},
                    },
                },
                'example': {'error': 'Paramètre requis manquant'},
            }
        },
    },
    401: {
        'description': 'Non authentifié — token JWT manquant, expiré ou invalide',
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {'type': 'string'},
                    },
                },
                'example': {
                    'detail': 'Authentication credentials were not provided.'
                },
            }
        },
    },
    403: {
        'description': 'Permissions insuffisantes — rôle médecin/personnel requis',
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'},
                    },
                },
                'example': {'error': 'Réservé médecins et personnel'},
            }
        },
    },
    404: {
        'description': 'Ressource non trouvée — patient, RDV, dossier, token invalide',
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'},
                    },
                },
                'example': {'error': 'Patient non trouvé'},
            }
        },
    },
    409: {
        'description': 'Conflit — ressource déjà existante ou créneau déjà réservé',
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'},
                    },
                },
                'example': {
                    'error': 'Ce créneau est déjà réservé pour ce médecin.'
                },
            }
        },
    },
    500: {
        'description': 'Erreur interne du serveur — contacter l\'administrateur '
                       'avec le correlation ID retourné',
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'},
                        'correlation_id': {'type': 'string', 'format': 'uuid'},
                    },
                },
                'example': {'error': 'Erreur interne', 'correlation_id': '...'},
            }
        },
    },
}


def _errors(*codes):
    """Retourne un sous-dict de STANDARD_ERROR_RESPONSES pour les codes donnés.

    Utilisation dans un schéma :

        responses={
            200: {...},
            **_errors(400, 404),
        }
    """
    return {code: STANDARD_ERROR_RESPONSES[code] for code in codes}


# ═══════════════════════════════════════════════════════════════════════════
# 3. EXEMPLES DE REQUEST / RESPONSE — réutilisés par les OpenApiExample
# ═══════════════════════════════════════════════════════════════════════════

# ─── Authentification ───
LOGIN_REQUEST_EXAMPLE = {
    'username': 'patient@example.com',
    'password': 'Sup3rStr0ngPass!',
}

LOGIN_RESPONSE_EXAMPLE = {
    'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIn0.signature',
    'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCJ9.signature',
    'user': {
        'id': 1,
        'username': 'patient',
        'email': 'patient@example.com',
        'first_name': 'Jean',
        'last_name': 'Dupont',
    },
    'patient': {
        'id': 1,
        'patient_id': 'PAT-2024-0001',
        'nom': 'Dupont',
        'prenom': 'Jean',
        'email': 'patient@example.com',
        'telephone': '+229 90 00 00 00',
        'groupe_sanguin': 'O+',
        'date_naissance': '1985-04-12',
    },
    'require_2fa': False,
}

REGISTER_REQUEST_EXAMPLE = {
    'username': 'jean.dupont',
    'email': 'patient@example.com',
    'password': 'Sup3rStr0ngPass!',
    'password2': 'Sup3rStr0ngPass!',
    'nom': 'Dupont',
    'prenom': 'Jean',
    'telephone': '+229 90 00 00 00',
    'date_naissance': '1985-04-12',
    'groupe_sanguin': 'O+',
    'sexe': 'M',
}

REGISTER_RESPONSE_EXAMPLE = {
    'access': 'eyJ0eXAi...',
    'refresh': 'eyJ0eXAi...',
    'user': {'id': 42, 'username': 'jean.dupont', 'email': 'patient@example.com'},
    'patient': {
        'id': 42,
        'patient_id': 'PAT-2024-0042',
        'nom': 'Dupont',
        'prenom': 'Jean',
        'groupe_sanguin': 'O+',
    },
}

# ─── Patient ───
PATIENT_PROFILE_RESPONSE_EXAMPLE = {
    'id': 1,
    'patient_id': 'PAT-2024-0001',
    'nom': 'Dupont',
    'prenom': 'Jean',
    'email': 'patient@example.com',
    'telephone': '+229 90 00 00 00',
    'date_naissance': '1985-04-12',
    'groupe_sanguin': 'O+',
    'sexe': 'M',
    'poids': 75.5,
    'taille': 178,
    'allergies': 'Pénicilline, arachide',
    'adresse': 'Cotonou, Bénin',
    'hopital': 1,
    'date_inscription': '2024-01-15T10:30:00Z',
}

# ─── Rendez-vous ───
RDV_REQUEST_EXAMPLE = {
    'medecin_id': 3,
    'hopital_id': 1,
    'date': '2026-09-15',
    'heure': '09:30',
    'motif': 'Consultation de suivi cardiologique',
    'note': 'Apporter dernier ECG',
}

RDV_RESPONSE_EXAMPLE = {
    'id': 158,
    'patient': 1,
    'medecin': 3,
    'hopital': 1,
    'date': '2026-09-15',
    'heure': '09:30:00',
    'motif': 'Consultation de suivi cardiologique',
    'note': 'Apporter dernier ECG',
    'statut': 'en_attente',
    'google_event_id': None,
}

# ─── Urgences ───
URGENCE_REQUEST_EXAMPLE = {
    'niveau': 'P2',
    'latitude': 6.1725,
    'longitude': 1.2314,
    'description': 'Douleur thoracique aiguë irradiant dans le bras gauche',
}

URGENCE_RESPONSE_EXAMPLE = {
    'uuid': '550e8400-e29b-41d4-a716-446655440000',
    'patient_nom': 'Jean Dupont',
    'patient_groupe_sanguin': 'O+',
    'hopital_nom': 'CHU Campus',
    'niveau': 'P2',
    'statut': 'en_attente',
    'latitude': 6.1725,
    'longitude': 1.2314,
}

URGENCE_PUBLIQUE_RESPONSE_EXAMPLE = {
    'nom': 'Dupont',
    'prenom': 'Jean',
    'date_naissance': '1985-04-12',
    'groupe_sanguin': 'O+',
    'allergies': 'Pénicilline, arachide',
    'traitements_actifs': [
        {'medicament': 'Amlodipine', 'posologie': '5mg', 'duree': 'chronique'},
        {'medicament': 'Aspégic', 'posologie': '100mg/j', 'duree': 'chronique'},
    ],
    'medecin_referent': {
        'nom': 'Dr. Alice Mensah',
        'specialite': 'Cardiologie',
        'telephone': '+229 96 11 22 33',
    },
    'patient_telephone': '+229 90 00 00 00',
    'hopital': {
        'nom': 'CHU Campus',
        'telephone': '+229 21 30 00 00',
    },
    'acces_id': 42,
    'acces_timestamp': '2026-08-20T14:32:11.123456+00:00',
}

# ─── File d'attente ───
FILE_ATTENTE_RESPONSE_EXAMPLE = {
    'id': 27,
    'patient': 1,
    'hopital': 1,
    'niveau': 'P3',
    'statut': 'en_attente',
    'position': 4,
    'temps_attente_estime': 18,
    'date_arrivee': '2026-08-20T14:00:00+00:00',
}

# ─── Créneaux médecin ───
CRENEAUX_RESPONSE_EXAMPLE = [
    {'heure': '08:30', 'libre': True},
    {'heure': '09:00', 'libre': True},
    {'heure': '09:30', 'libre': False, 'raison': 'RDV existant'},
    {'heure': '10:00', 'libre': True},
]

# ─── Assignation multi-hôpitaux ───
ASSIGNER_REQUEST_EXAMPLE = {
    'specialite': 'Cardiologie',
    'latitude': 6.1725,
    'longitude': 1.2314,
    'niveau_urgence': 'P3',
}

ASSIGNER_RESPONSE_EXAMPLE = {
    'hopital_id': 1,
    'hopital_nom': 'CHU Campus',
    'hopital_telephone': '+229 21 30 00 00',
    'hopital_adresse': 'Cotonou, Bénin',
    'hopital_ville': 'Cotonou',
    'temps_attente_estime': 18,
}

# ─── Exports ───
EXPORT_FHIR_RESPONSE_EXAMPLE = {
    'resourceType': 'Bundle',
    'type': 'document',
    'entry': [
        {
            'resource': {
                'resourceType': 'Patient',
                'id': 'PAT-2024-0001',
                'name': [{'family': 'Dupont', 'given': ['Jean']}],
            }
        }
    ],
}

# ─── Device token (notifications) ───
DEVICE_TOKEN_REQUEST_EXAMPLE = {
    'token': 'dGhpcyBpcyBhIGZjbSB0b2tlbiBleGFtcGxl',
    'platform': 'android',
}

DEVICE_TOKEN_RESPONSE_EXAMPLE = {
    'id': 12,
    'created': True,
    'message': 'Token enregistré',
}

# ─── 2FA ───
SETUP_2FA_RESPONSE_EXAMPLE = {
    'secret': 'JBSWY3DPEHPK3PXP',
    'otpauth_url': 'otpauth://totp/Sanar:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Sanar',
    'qr_image_base64': 'PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjwvc3ZnPg==',
    'message': 'Scannez ce QR code avec Google Authenticator, '
               'puis confirmez avec /api/2fa/verify/',
}

# ─── Signature prescription ───
SIGNER_PRESCRIPTION_RESPONSE_EXAMPLE = {
    'message': 'Prescription signée électroniquement',
    'signature_hash': 'a3f5b8c1d9e2f4a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0',
    'signe_par': 'Dr. Alice Mensah',
    'date_signature': '2026-08-20T14:45:00.123456+00:00',
}

# ─── RGPD ───
ANONYMISER_REQUEST_EXAMPLE = {
    'password': 'Sup3rStr0ngPass!',
    'confirmation': 'ANONYMISER DEFINITIVEMENT',
}

ANONYMISER_RESPONSE_EXAMPLE = {
    'message': 'Données anonymisées conformément au RGPD (art. 17)',
    'patient_id_anonymise': 'PAT-XXXX-XXXX',
    'action': 'irreversible',
    'timestamp': '2026-08-20T14:50:00.123456+00:00',
}

# ─── Recherche floue ───
RECHERCHE_FLOUE_RESPONSE_EXAMPLE = {
    'query': 'dupon',
    'count': 2,
    'results': [
        {
            'id': 1,
            'patient_id': 'PAT-2024-0001',
            'nom': 'Dupont',
            'prenom': 'Jean',
            'telephone': '+229 90 00 00 00',
            'groupe_sanguin': 'O+',
            'hopital': 'CHU Campus',
            'score': 1.0,
        },
        {
            'id': 7,
            'patient_id': 'PAT-2024-0007',
            'nom': 'Dupond',
            'prenom': 'Marie',
            'telephone': '+229 91 11 11 11',
            'groupe_sanguin': 'A-',
            'hopital': 'CHU Campus',
            'score': 0.857,
        },
    ],
}

# ─── Health check ───
HEALTH_CHECK_RESPONSE_EXAMPLE = {
    'status': 'ok',
    'timestamp': '2026-08-20T14:55:00.123456+00:00',
    'version': '2.0.0',
    'services': {
        'database': 'ok',
        'redis': 'ok',
        'storage': 'ok',
    },
}

# ─── Téléconsultation ───
TELECONSULTATION_REQUEST_EXAMPLE = {
    'patient_id': 1,
    'medecin_id': 3,
    'date_planifiee': '2026-08-20T15:00:00Z',
}

TELECONSULTATION_RESPONSE_EXAMPLE = {
    'room_uuid': '7c9e6f5a-3b2d-4e8f-9a1b-2c3d4e5f6a7b',
    'patient': 'Jean Dupont',
    'medecin': 'Dr. Alice Mensah',
    'statut': 'planifiee',
    'ws_url': '/ws/teleconsultation/7c9e6f5a-3b2d-4e8f-9a1b-2c3d4e5f6a7b/',
}

# ─── ML prédictions ───
ML_PREDICTION_RESPONSE_EXAMPLE = {
    'score_risque': 0.642,
    'niveau_risque': 'eleve',
    'features_importantes': {
        'glycemie_moyenne': 1.42,
        'tension_arterielle': 0.87,
        'age': 0.55,
        'imc': 0.41,
    },
    'analyses_utilisees': 12,
    'modele_version': '1.3.0',
    'date_prediction': '2026-08-20T14:30:00.123456+00:00',
}


# ═══════════════════════════════════════════════════════════════════════════
# 4. SCHÉMAS PAR ENDPOINT — 19 endpoints majeurs documentés
# ═══════════════════════════════════════════════════════════════════════════

# ─── 1. POST /api/auth/login/ ─────────────────────────────────────────────
LOGIN_SCHEMA = extend_schema(
    summary='Authentifier un utilisateur',
    description=(
        "Authentifie un patient ou médecin via email + mot de passe. "
        "Retourne un token JWT (access + refresh) et les données du "
        "patient si applicable. Le token access expire en 1h, le refresh "
        "en 7 jours.\n\n"
        "**2FA** : si l'utilisateur est médecin ou personnel et a activé "
        "le 2FA TOTP, `require_2fa=true` est retourné et le client doit "
        "appeler `/api/2fa/verify/` avant d'utiliser le token."
    ),
    tags=['Authentification'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'username': {
                    'type': 'string',
                    'description': 'Email ou username du patient/médecin',
                },
                'password': {'type': 'string', 'format': 'password'},
            },
            'required': ['username', 'password'],
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'access': {'type': 'string'},
                'refresh': {'type': 'string'},
                'user': {'type': 'object'},
                'patient': {
                    'type': 'object',
                    'nullable': True,
                    'description': 'Présent si l\'utilisateur est un patient',
                },
                'require_2fa': {
                    'type': 'boolean',
                    'description': 'True si 2FA TOTP requis avant usage du token',
                },
            },
        },
        401: {'description': 'Identifiants incorrects'},
    },
    examples=[
        OpenApiExample(
            'Requête login',
            value=LOGIN_REQUEST_EXAMPLE,
            request_only=True,
        ),
        OpenApiExample(
            'Login réussi',
            value=LOGIN_RESPONSE_EXAMPLE,
            response_only=True,
        ),
    ],
)

LoginViewSchema = extend_schema_view(post=LOGIN_SCHEMA)


# ─── 2. POST /api/auth/register/ ──────────────────────────────────────────
REGISTER_SCHEMA = extend_schema(
    summary='Créer un compte patient',
    description=(
        "Crée un nouvel utilisateur + patient. Retourne immédiatement les "
        "tokens JWT (pas de nécessité de se reconnecter).\n\n"
        "Le `patient_id` est généré automatiquement au format `PAT-YYYY-NNNN`. "
        "Un `DossierMedical` vide est initialisé en cascade par signal."
    ),
    tags=['Authentification'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string'},
                'email': {'type': 'string', 'format': 'email'},
                'password': {'type': 'string', 'format': 'password', 'minLength': 8},
                'password2': {'type': 'string', 'format': 'password'},
                'nom': {'type': 'string'},
                'prenom': {'type': 'string'},
                'telephone': {'type': 'string'},
                'date_naissance': {'type': 'string', 'format': 'date'},
                'groupe_sanguin': {
                    'type': 'string',
                    'enum': ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'],
                },
                'sexe': {'type': 'string', 'enum': ['M', 'F']},
            },
            'required': ['username', 'email', 'password', 'password2',
                         'nom', 'prenom', 'date_naissance'],
        }
    },
    responses={
        201: {
            'type': 'object',
            'properties': {
                'access': {'type': 'string'},
                'refresh': {'type': 'string'},
                'user': {'type': 'object'},
                'patient': {'type': 'object'},
            },
        },
        400: {
            'description': 'Données invalides (email déjà utilisé, mots de passe '
                           'différents, champs obligatoires manquants)',
        },
    },
    examples=[
        OpenApiExample(
            'Requête inscription',
            value=REGISTER_REQUEST_EXAMPLE,
            request_only=True,
        ),
        OpenApiExample(
            'Inscription réussie',
            value=REGISTER_RESPONSE_EXAMPLE,
            response_only=True,
            status_codes=['201'],
        ),
    ],
)

RegisterViewSchema = extend_schema_view(post=REGISTER_SCHEMA)


# ─── 3. GET / PUT /api/patient/profile/ ───────────────────────────────────
PATIENT_PROFILE_SCHEMA = extend_schema(
    summary='Récupérer ou mettre à jour le profil patient',
    description=(
        "GET : retourne le profil complet du patient connecté.\n"
        "PUT : met à jour partiellement le profil (tous les champs sont "
        "optionnels).\n\n"
        "Les champs sensibles (groupe sanguin, allergies) sont horodatés "
        "dans l'audit trail django-auditlog."
    ),
    tags=['Patient'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'telephone': {'type': 'string'},
                'adresse': {'type': 'string'},
                'poids': {'type': 'number'},
                'taille': {'type': 'integer'},
                'allergies': {'type': 'string'},
            },
            'additionalProperties': False,
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'patient_id': {'type': 'string'},
                'nom': {'type': 'string'},
                'prenom': {'type': 'string'},
                'email': {'type': 'string', 'format': 'email'},
                'telephone': {'type': 'string'},
                'date_naissance': {'type': 'string', 'format': 'date'},
                'groupe_sanguin': {'type': 'string'},
                'sexe': {'type': 'string'},
                'poids': {'type': 'number'},
                'taille': {'type': 'integer'},
                'allergies': {'type': 'string'},
                'adresse': {'type': 'string'},
                'hopital': {'type': 'integer', 'nullable': True},
                'date_inscription': {'type': 'string', 'format': 'date-time'},
            },
        },
        **_errors(400, 401, 404),
    },
    examples=[
        OpenApiExample(
            'Profil patient',
            value=PATIENT_PROFILE_RESPONSE_EXAMPLE,
            response_only=True,
        ),
    ],
)

PatientProfileSchema = extend_schema_view(
    get=extend_schema(
        summary='Récupérer le profil patient',
        description='Retourne le profil complet du patient connecté.',
        tags=['Patient'],
        responses={
            200: {'type': 'object'},
            **_errors(401, 404),
        },
        examples=[
            OpenApiExample(
                'Profil patient',
                value=PATIENT_PROFILE_RESPONSE_EXAMPLE,
                response_only=True,
            ),
        ],
    ),
    put=PATIENT_PROFILE_SCHEMA,
)


# ─── 4. GET / POST /api/rendez-vous/ ──────────────────────────────────────
RDV_LIST_GET_SCHEMA = extend_schema(
    summary='Lister les rendez-vous du patient',
    description=(
        "Retourne tous les rendez-vous du patient connecté, triés par date "
        "décroissante, avec médecin et hôpital préchargés "
        "(`select_related`)."
    ),
    tags=['Rendez-vous'],
    responses={
        200: {
            'type': 'array',
            'items': {'type': 'object'},
        },
        **_errors(401, 404),
    },
)

RDV_LIST_POST_SCHEMA = extend_schema(
    summary='Créer un rendez-vous',
    description=(
        "Crée un nouveau rendez-vous pour le patient connecté.\n\n"
        "**Anti double-booking** : vérification via "
        "`medecins.services.verifier_conflit(medecin_id, date, heure)` "
        "avant insertion. Retourne 409 si le créneau est déjà réservé."
    ),
    tags=['Rendez-vous'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'medecin_id': {'type': 'integer'},
                'hopital_id': {'type': 'integer', 'nullable': True},
                'date': {'type': 'string', 'format': 'date'},
                'heure': {'type': 'string', 'pattern': '^([0-1][0-9]|2[0-3]):[0-5][0-9]$'},
                'motif': {'type': 'string'},
                'note': {'type': 'string'},
            },
            'required': ['medecin_id', 'date', 'heure', 'motif'],
        }
    },
    responses={
        201: {'type': 'object'},
        **_errors(400, 401, 404, 409),
    },
    examples=[
        OpenApiExample(
            'Requête création RDV',
            value=RDV_REQUEST_EXAMPLE,
            request_only=True,
        ),
        OpenApiExample(
            'RDV créé',
            value=RDV_RESPONSE_EXAMPLE,
            response_only=True,
            status_codes=['201'],
        ),
    ],
)

RendezVousListSchema = extend_schema_view(
    get=RDV_LIST_GET_SCHEMA,
    post=RDV_LIST_POST_SCHEMA,
)


# ─── 5. POST /api/urgences/ ───────────────────────────────────────────────
TRIGGER_URGENCE_SCHEMA = extend_schema(
    summary='Déclencher une demande d\'urgence (bouton SOS)',
    description=(
        "Déclenche une demande d'urgence géolocalisée. L'API sélectionne "
        "automatiquement l'hôpital optimal via `urgences.services."
        "hopital_optimal(latitude, longitude, niveau)` (formule de "
        "Haversine + charge courante).\n\n"
        "Notifie l'équipe d'astreinte par FCM + SMS + WhatsApp "
        "(`trigger_notifications_urgence`).\n\n"
        "Niveaux : P1 (réanimation immédiate), P2 (urgent), P3 (standard), "
        "P4 (moins urgent), P5 (non urgent)."
    ),
    tags=['Urgences'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'niveau': {
                    'type': 'string',
                    'enum': ['P1', 'P2', 'P3', 'P4', 'P5'],
                    'default': 'P2',
                },
                'latitude': {
                    'type': 'number',
                    'minimum': -90,
                    'maximum': 90,
                },
                'longitude': {
                    'type': 'number',
                    'minimum': -180,
                    'maximum': 180,
                },
                'description': {'type': 'string'},
            },
            'required': ['latitude', 'longitude'],
        }
    },
    responses={
        201: {'type': 'object'},
        **_errors(400, 401, 404),
    },
    examples=[
        OpenApiExample(
            'Requête SOS',
            value=URGENCE_REQUEST_EXAMPLE,
            request_only=True,
        ),
        OpenApiExample(
            'Urgence créée',
            value=URGENCE_RESPONSE_EXAMPLE,
            response_only=True,
            status_codes=['201'],
        ),
    ],
)

TriggerUrgenceSchema = extend_schema_view(post=TRIGGER_URGENCE_SCHEMA)


# ─── 6. GET /api/urgence/<uuid:token>/ — ENDPOINT PUBLIC ─────────────────
ACCES_URGENCE_PUBLIQUE_SCHEMA = extend_schema(
    summary='Accès d\'urgence PUBLIC par QR code médical',
    description=(
        "**ENDPOINT PUBLIC — `AllowAny`** : accessible sans authentification "
        "par un secouriste scannant le QR code médical du patient.\n\n"
        "Sécurité :\n"
        "- Token UUID opaque (non devinable, 122 bits d'entropie)\n"
        "- Audit trail obligatoire (`urgences.AccesUrgence` : IP, user agent, "
        "referer)\n"
        "- Rate limit recommandé : 10/h par IP via django-ratelimit\n"
        "- Données restreintes : pas d'historique complet ni notes libres\n"
        "- Notification FCM envoyée au patient à chaque accès\n\n"
        "Le patient peut révoquer/régénérer son token via "
        "`POST /api/urgence/regenerer-qr/` ou `POST /api/urgence/toggle-qr/`."
    ),
    tags=['Urgences'],
    parameters=[
        OpenApiParameter(
            name='token',
            type=str,
            location=OpenApiParameter.PATH,
            required=True,
            description='Token UUID opaque du QR code médical patient',
        ),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'nom': {'type': 'string'},
                'prenom': {'type': 'string'},
                'date_naissance': {'type': 'string', 'format': 'date'},
                'groupe_sanguin': {'type': 'string'},
                'allergies': {'type': 'string'},
                'traitements_actifs': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'medicament': {'type': 'string'},
                            'posologie': {'type': 'string'},
                            'duree': {'type': 'string'},
                        },
                    },
                },
                'medecin_referent': {'type': 'object', 'nullable': True},
                'patient_telephone': {'type': 'string'},
                'hopital': {'type': 'object', 'nullable': True},
                'acces_id': {'type': 'integer'},
                'acces_timestamp': {'type': 'string', 'format': 'date-time'},
            },
        },
        404: {'description': 'Token invalide, révoqué, ou QR désactivé'},
    },
    examples=[
        OpenApiExample(
            'Accès urgence accordé',
            value=URGENCE_PUBLIQUE_RESPONSE_EXAMPLE,
            response_only=True,
        ),
    ],
)

AccesUrgencePubliqueSchema = extend_schema_view(
    get=ACCES_URGENCE_PUBLIQUE_SCHEMA,
)


# ─── 7. GET /api/file-attente/ma-position/ ───────────────────────────────
MA_FILE_ATTENTE_SCHEMA = extend_schema(
    summary='Position du patient dans la file d\'attente',
    description=(
        "Retourne la position actuelle du patient dans la file d'attente "
        "de son hôpital, ainsi que le temps d'attente estimé (moyenne "
        "mobile des consultations terminées).\n\n"
        "Le niveau de triage P1-P5 est déterminé à l'arrivée par "
        "l'infirmier d'accueil via `file_attente.services.ordre_passage` "
        "(file prioritaire basée sur un heap)."
    ),
    tags=["File d'attente"],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'patient': {'type': 'integer'},
                'hopital': {'type': 'integer'},
                'niveau': {
                    'type': 'string',
                    'enum': ['P1', 'P2', 'P3', 'P4', 'P5'],
                },
                'statut': {'type': 'string'},
                'position': {'type': 'integer'},
                'temps_attente_estime': {
                    'type': 'integer',
                    'description': 'Minutes estimées avant consultation',
                },
                'date_arrivee': {'type': 'string', 'format': 'date-time'},
            },
        },
        **_errors(401, 404),
    },
    examples=[
        OpenApiExample(
            'Position en file',
            value=FILE_ATTENTE_RESPONSE_EXAMPLE,
            response_only=True,
        ),
    ],
)

MaFileAttenteSchema = extend_schema_view(get=MA_FILE_ATTENTE_SCHEMA)


# ─── 8. GET /api/medecins/<id>/creneaux/?date=YYYY-MM-DD ─────────────────
CRENEAUX_MEDECIN_SCHEMA = extend_schema(
    summary='Créneaux disponibles d\'un médecin pour une date',
    description=(
        "Calcule les créneaux réservables d'un médecin pour une date "
        "donnée en croisant :\n"
        "- Les `DisponibiliteMedecin` récurrentes (jour de la semaine, "
        "  plages horaires)\n"
        "- Les congés (`CongeMedecin`)\n"
        "- Les RDV déjà réservés (`appointments.RendezVous`)\n\n"
        "Utilisé par l'app Flutter patient pour l'écran de prise de RDV."
    ),
    tags=['Rendez-vous'],
    parameters=[
        OpenApiParameter(
            name='medecin_id',
            type=int,
            location=OpenApiParameter.PATH,
            required=True,
            description='ID du médecin',
        ),
        OpenApiParameter(
            name='date',
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Date au format ISO 8601 YYYY-MM-DD',
            pattern=r'^\d{4}-\d{2}-\d{2}$',
        ),
    ],
    responses={
        200: {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'heure': {'type': 'string'},
                    'libre': {'type': 'boolean'},
                    'raison': {
                        'type': 'string',
                        'nullable': True,
                        'description': 'Raison si non libre (RDV existant, '
                                       'congé, hors plage)',
                    },
                },
            },
        },
        **_errors(400, 401),
    },
    examples=[
        OpenApiExample(
            'Créneaux du jour',
            value=CRENEAUX_RESPONSE_EXAMPLE,
            response_only=True,
        ),
    ],
)

CreneauxMedecinSchema = extend_schema_view(get=CRENEAUX_MEDECIN_SCHEMA)


# ─── 9. POST /api/assigner-patient/ ───────────────────────────────────────
ASSIGNER_PATIENT_SCHEMA = extend_schema(
    summary='Assigner automatiquement le meilleur hôpital',
    description=(
        "Assigne automatiquement le meilleur hôpital au patient selon "
        "plusieurs critères via `hopitaux.services.assigner_hopital` :\n\n"
        "1. Distance (Haversine) entre la position patient et l'hôpital\n"
        "2. Spécialité requise disponible\n"
        "3. Charge courante (lits disponibles `LitHopital`)\n"
        "4. Niveau d'urgence (P1 → réanimation, P2 → urgences, etc.)\n\n"
        "Retourne aussi le temps d'attente estimé "
        "(`file_attente.services.estimer_temps_attente`)."
    ),
    tags=['Urgences'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'specialite': {
                    'type': 'string',
                    'description': 'Spécialité médicale requise (ex: Cardiologie)',
                },
                'latitude': {'type': 'number'},
                'longitude': {'type': 'number'},
                'niveau_urgence': {
                    'type': 'string',
                    'enum': ['P1', 'P2', 'P3', 'P4', 'P5'],
                    'default': 'P3',
                },
            },
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'hopital_id': {'type': 'integer'},
                'hopital_nom': {'type': 'string'},
                'hopital_telephone': {'type': 'string'},
                'hopital_adresse': {'type': 'string'},
                'hopital_ville': {'type': 'string'},
                'temps_attente_estime': {'type': 'integer'},
            },
        },
        **_errors(401, 404),
    },
    examples=[
        OpenApiExample(
            'Requête assignation',
            value=ASSIGNER_REQUEST_EXAMPLE,
            request_only=True,
        ),
        OpenApiExample(
            'Hôpital assigné',
            value=ASSIGNER_RESPONSE_EXAMPLE,
            response_only=True,
        ),
    ],
)

AssignerPatientSchema = extend_schema_view(post=ASSIGNER_PATIENT_SCHEMA)


# ─── 10. GET /api/exports/dossier-pdf/ ───────────────────────────────────
EXPORT_DOSSIER_PDF_SCHEMA = extend_schema(
    summary='Export PDF du dossier médical',
    description=(
        "Génère un PDF complet du dossier médical du patient connecté "
        "via `exports.services.export_dossier_pdf`.\n\n"
        "Moteur : WeasyPrint (HTML/CSS → PDF) avec fallback reportlab "
        "si WeasyPrint indisponible.\n\n"
        "Inclut : identité, antécédents, traitements, consultations, "
        "prescriptions (signées), analyses avec flags N/H/L/C, "
        "allergies encadrées en rouge."
    ),
    tags=['Exports'],
    responses={
        200: {
            'type': 'string',
            'format': 'binary',
            'description': 'PDF binaire (Content-Disposition: attachment)',
        },
        **_errors(401, 404, 500),
    },
)
ExportDossierPdfSchema = extend_schema_view(get=EXPORT_DOSSIER_PDF_SCHEMA)


# ─── 11. GET /api/exports/dossier-fhir/ ───────────────────────────────────
EXPORT_DOSSIER_FHIR_SCHEMA = extend_schema(
    summary='Export FHIR R4 (JSON) du dossier médical',
    description=(
        "Génère un Bundle FHIR R4 (JSON) contenant toutes les ressources "
        "du dossier patient : Patient, Condition (antécédents), "
        "MedicationRequest (prescriptions), Observation (analyses), "
        "Encounter (consultations).\n\n"
        "Compatible avec les SIH standards (HL7 FHIR R4)."
    ),
    tags=['Exports'],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'resourceType': {
                    'type': 'string',
                    'enum': ['Bundle'],
                },
                'type': {
                    'type': 'string',
                    'enum': ['document', 'collection'],
                },
                'entry': {
                    'type': 'array',
                    'items': {'type': 'object'},
                },
            },
        },
        **_errors(401, 404, 500),
    },
    examples=[
        OpenApiExample(
            'Bundle FHIR R4',
            value=EXPORT_FHIR_RESPONSE_EXAMPLE,
            response_only=True,
        ),
    ],
)
ExportDossierFhirSchema = extend_schema_view(get=EXPORT_DOSSIER_FHIR_SCHEMA)


# ─── 12. POST /api/device-token/ ─────────────────────────────────────────
DEVICE_TOKEN_SCHEMA = extend_schema(
    summary='Enregistrer un token FCM (notifications push)',
    description=(
        "Enregistre ou met à jour un token Firebase Cloud Messaging pour "
        "l'utilisateur connecté. À appeler à chaque ouverture de l'app "
        "Flutter (le token peut changer).\n\n"
        "Utilisé pour : rappels RDV J-1/H-2, alertes d'urgence, "
        "notifications de téléconsultation, alertes analyses critiques."
    ),
    tags=['Notifications'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'token': {
                    'type': 'string',
                    'description': 'Token FCM renvoyé par firebase_messaging',
                },
                'platform': {
                    'type': 'string',
                    'enum': ['android', 'ios', 'web'],
                    'default': 'android',
                },
            },
            'required': ['token'],
        }
    },
    responses={
        201: {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'created': {
                    'type': 'boolean',
                    'description': 'True si nouveau token, False si mise à jour',
                },
                'message': {'type': 'string'},
            },
        },
        **_errors(400, 401),
    },
    examples=[
        OpenApiExample(
            'Requête enregistrement',
            value=DEVICE_TOKEN_REQUEST_EXAMPLE,
            request_only=True,
        ),
        OpenApiExample(
            'Token enregistré',
            value=DEVICE_TOKEN_RESPONSE_EXAMPLE,
            response_only=True,
            status_codes=['201'],
        ),
    ],
)

DeviceTokenSchema = extend_schema_view(post=DEVICE_TOKEN_SCHEMA)


# ─── 13. POST /api/2fa/setup/ ────────────────────────────────────────────
SETUP_2FA_SCHEMA = extend_schema(
    summary='Activer le 2FA TOTP (médecins et personnel uniquement)',
    description=(
        "Génère un secret TOTP + QR code SVG (base64) pour activer le 2FA. "
        "Le secret n'est pas encore actif : l'utilisateur doit scanner le "
        "QR code avec Google Authenticator (ou équivalent), puis confirmer "
        "via `POST /api/2fa/verify/` avec un code à 6 chiffres.\n\n"
        "Réservé aux médecins (`hasattr(user, 'medecin_profile')`) et au "
        "personnel (`hasattr(user, 'personnel')`)."
    ),
    tags=['Sécurité 2FA'],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'secret': {
                    'type': 'string',
                    'description': 'Secret hex pour saisie manuelle',
                },
                'otpauth_url': {
                    'type': 'string',
                    'format': 'uri',
                    'description': 'URL otpauth:// à encoder en QR code',
                },
                'qr_image_base64': {
                    'type': 'string',
                    'description': 'QR code SVG en base64',
                },
                'message': {'type': 'string'},
            },
        },
        **_errors(401, 403),
    },
    examples=[
        OpenApiExample(
            'Setup 2FA',
            value=SETUP_2FA_RESPONSE_EXAMPLE,
            response_only=True,
        ),
    ],
)

Setup2FASchema = extend_schema_view(post=SETUP_2FA_SCHEMA)


# ─── 14. POST /api/prescriptions/<id>/signer/ ────────────────────────────
SIGNER_PRESCRIPTION_SCHEMA = extend_schema(
    summary='Signer électroniquement une prescription (médecin)',
    description=(
        "Signe électroniquement une prescription via `Prescription.signer()`.\n\n"
        "Calcule le hash SHA-256 du contenu (médicament + posologie + durée "
        "+ médecin + timestamp) et le stocke. Rend la prescription "
        "infalsifiable a posteriori : toute modification ultérieure sera "
        "détectée par `GET /api/prescriptions/<id>/verifier/`.\n\n"
        "**Auth** : seul un médecin peut signer. Le médecin signataire est "
        "consigné dans `signe_par`."
    ),
    tags=['Dossier médical'],
    parameters=[
        OpenApiParameter(
            name='prescription_id',
            type=int,
            location=OpenApiParameter.PATH,
            required=True,
            description='ID de la prescription à signer',
        ),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'signature_hash': {
                    'type': 'string',
                    'pattern': '^[a-f0-9]{64}$',
                    'description': 'Hash SHA-256 hexadécimal',
                },
                'signe_par': {'type': 'string'},
                'date_signature': {'type': 'string', 'format': 'date-time'},
            },
        },
        **_errors(400, 401, 403, 404),
    },
    examples=[
        OpenApiExample(
            'Prescription signée',
            value=SIGNER_PRESCRIPTION_RESPONSE_EXAMPLE,
            response_only=True,
        ),
    ],
)

SignerPrescriptionSchema = extend_schema_view(post=SIGNER_PRESCRIPTION_SCHEMA)


# ─── 15. DELETE /api/rgpd/anonymiser/ — DROIT À L'OUBLI ──────────────────
ANONYMISER_MES_DONNEES_SCHEMA = extend_schema(
    summary='Anonymiser mes données (droit à l\'oubli RGPD art. 17)',
    description=(
        "**ACTION IRRÉVERSIBLE** — anonymise toutes les données du patient "
        "connecté conformément à l'article 17 du RGPD.\n\n"
        "Opérations effectuées :\n"
        "1. Anonymisation du Patient (nom, prenom, email, telephone, "
        "   adresse → 'ANONYMISE')\n"
        "2. Révocation du token d'urgence (`urgence_qr_actif=False` + "
        "   régénération)\n"
        "3. Suppression des `DeviceToken` FCM\n"
        "4. Suppression du `DossierMedical` + prescriptions + documents\n"
        "5. Désactivation du compte utilisateur (`is_active=False`)\n"
        "6. Conservation de l'ID patient pour traçabilité comptable\n"
        "7. Journalisation dans l'audit trail\n\n"
        "**Double confirmation requise** :\n"
        "- Mot de passe du compte (`password`)\n"
        "- Chaîne `\"ANONYMISER DEFINITIVEMENT\"` dans `confirmation`"
    ),
    tags=['RGPD'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'password': {
                    'type': 'string',
                    'format': 'password',
                    'description': 'Mot de passe du compte pour confirmation',
                },
                'confirmation': {
                    'type': 'string',
                    'enum': ['ANONYMISER DEFINITIVEMENT'],
                },
            },
            'required': ['password', 'confirmation'],
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'patient_id_anonymise': {'type': 'string'},
                'action': {
                    'type': 'string',
                    'enum': ['irreversible'],
                },
                'timestamp': {'type': 'string', 'format': 'date-time'},
            },
        },
        **_errors(400, 401, 403, 404),
    },
    examples=[
        OpenApiExample(
            'Demande d\'anonymisation',
            value=ANONYMISER_REQUEST_EXAMPLE,
            request_only=True,
        ),
        OpenApiExample(
            'Données anonymisées',
            value=ANONYMISER_RESPONSE_EXAMPLE,
            response_only=True,
        ),
    ],
)

AnonymiserMesDonneesSchema = extend_schema_view(
    delete=ANONYMISER_MES_DONNEES_SCHEMA,
)


# ─── 16. GET /api/patients/recherche-floue/?q=...&limit=10 ───────────────
RECHERCHE_FLOUE_SCHEMA = extend_schema(
    summary='Recherche floue de patients (Levenshtein/SequenceMatcher)',
    description=(
        "Recherche de patients avec tolérance aux fautes de frappe. "
        "Algorithme en 2 étapes :\n\n"
        "1. Recherche `icontains` rapide (sous-chaîne) sur nom + prénom\n"
        "2. Si résultats insuffisants, recherche floue via "
        "   `difflib.SequenceMatcher` (seuil 60% de similarité) sur nom, "
        "   prénom et concaténation `prenom nom`\n\n"
        "**Réservé** aux médecins et personnel admin. Les `admin_hopital` "
        "ne voient que les patients de leur hôpital."
    ),
    tags=['Patient'],
    parameters=[
        OpenApiParameter(
            name='q',
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Chaîne de recherche (min 2 caractères)',
            pattern=r'.{2,}',
        ),
        OpenApiParameter(
            name='limit',
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            default=10,
            description='Nombre max de résultats (défaut 10, max 50)',
        ),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'query': {'type': 'string'},
                'count': {'type': 'integer'},
                'results': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'patient_id': {'type': 'string'},
                            'nom': {'type': 'string'},
                            'prenom': {'type': 'string'},
                            'telephone': {'type': 'string'},
                            'groupe_sanguin': {'type': 'string'},
                            'hopital': {'type': 'string', 'nullable': True},
                            'score': {
                                'type': 'number',
                                'minimum': 0,
                                'maximum': 1,
                                'description': 'Score de similarité (1.0 = exact)',
                            },
                        },
                    },
                },
            },
        },
        **_errors(400, 401, 403),
    },
    examples=[
        OpenApiExample(
            'Recherche "dupon"',
            value=RECHERCHE_FLOUE_RESPONSE_EXAMPLE,
            response_only=True,
        ),
    ],
)

RechercheFloueSchema = extend_schema_view(get=RECHERCHE_FLOUE_SCHEMA)


# ─── 17. GET /api/health/ — ENDPOINT PUBLIC (monitoring) ─────────────────
HEALTH_CHECK_SCHEMA = extend_schema(
    summary='Health check — statut des services critiques',
    description=(
        "**ENDPOINT PUBLIC** — utilisé par les load balancers, Kubernetes "
        "liveness/readiness probes et le monitoring externe (UptimeRobot).\n\n"
        "Vérifie :\n"
        "- Database PostgreSQL (SELECT 1)\n"
        "- Redis (broker Celery, channel layers WebRTC)\n"
        "- Storage (Django default_storage)\n\n"
        "Retourne 200 si tout est ok, **503 si dégradé**."
    ),
    tags=['Monitoring'],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {
                    'type': 'string',
                    'enum': ['ok', 'degraded'],
                },
                'timestamp': {'type': 'string', 'format': 'date-time'},
                'version': {'type': 'string'},
                'services': {
                    'type': 'object',
                    'properties': {
                        'database': {'type': 'string'},
                        'redis': {'type': 'string'},
                        'storage': {'type': 'string'},
                    },
                },
            },
        },
        503: {
            'description': 'Service dégradé — au moins un service critique '
                           'est en erreur',
        },
    },
    examples=[
        OpenApiExample(
            'Tous services OK',
            value=HEALTH_CHECK_RESPONSE_EXAMPLE,
            response_only=True,
        ),
    ],
)

HealthCheckSchema = extend_schema_view(get=HEALTH_CHECK_SCHEMA)


# ─── 18. POST /api/teleconsultation/ ─────────────────────────────────────
TELECONSULTATION_CREER_SCHEMA = extend_schema(
    summary='Créer une session de téléconsultation WebRTC',
    description=(
        "Crée une session de téléconsultation et notifie le patient par "
        "push FCM. Retourne un `room_uuid` à partager entre le médecin et "
        "le patient.\n\n"
        "La signalisation WebRTC (offer/answer/ICE candidates) se fait "
        "ensuite via le consumer WebSocket "
        "`/ws/teleconsultation/<room_uuid>/` "
        "(`teleconsultation.consumers.TeleconsultationConsumer`).\n\n"
        "Si `medecin_id` non fourni, utilise le médecin référent du dossier "
        "patient."
    ),
    tags=['Téléconsultation'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'patient_id': {'type': 'integer'},
                'medecin_id': {
                    'type': 'integer',
                    'nullable': True,
                    'description': 'Si omis, utilise le médecin référent',
                },
                'date_planifiee': {
                    'type': 'string',
                    'format': 'date-time',
                    'nullable': True,
                },
            },
            'required': ['patient_id'],
        }
    },
    responses={
        201: {
            'type': 'object',
            'properties': {
                'room_uuid': {'type': 'string', 'format': 'uuid'},
                'patient': {'type': 'string'},
                'medecin': {'type': 'string'},
                'statut': {
                    'type': 'string',
                    'enum': ['planifiee', 'en_cours', 'terminee'],
                },
                'ws_url': {'type': 'string', 'format': 'uri'},
            },
        },
        **_errors(400, 401, 404),
    },
    examples=[
        OpenApiExample(
            'Requête création téléconsultation',
            value=TELECONSULTATION_REQUEST_EXAMPLE,
            request_only=True,
        ),
        OpenApiExample(
            'Téléconsultation créée',
            value=TELECONSULTATION_RESPONSE_EXAMPLE,
            response_only=True,
            status_codes=['201'],
        ),
    ],
)

TeleconsultationCreerSchema = extend_schema_view(
    post=TELECONSULTATION_CREER_SCHEMA,
)


# ─── 19. GET /api/ml/prediction-courante/ ────────────────────────────────
ML_PREDICTION_SCHEMA = extend_schema(
    summary='Prédiction ML de risque patient (RandomForestClassifier)',
    description=(
        "Retourne la dernière prédiction ML du patient connecté. Si aucune "
        "prédiction de moins de 24h n'existe, déclenche un nouveau calcul "
        "synchrone via `ml_predictions.services.predire_risque_patient`.\n\n"
        "Modèle : RandomForestClassifier (100 estimateurs, max_depth=10) "
        "entraîné sur les analyses historiques. Features extraites : "
        "glycémie, tension artérielle, IMC, age, etc.\n\n"
        "Niveaux de risque : `faible`, `modere`, `eleve`, `critique` "
        "(calculés à partir du `score_risque` 0-1)."
    ),
    tags=['ML Prédictions'],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'score_risque': {
                    'type': 'number',
                    'minimum': 0,
                    'maximum': 1,
                },
                'niveau_risque': {
                    'type': 'string',
                    'enum': ['faible', 'modere', 'eleve', 'critique'],
                },
                'features_importantes': {
                    'type': 'object',
                    'description': 'Dict {feature: importance}',
                },
                'analyses_utilisees': {
                    'type': 'integer',
                    'description': 'Nombre d\'analyses utilisées pour la prédiction',
                },
                'modele_version': {'type': 'string', 'nullable': True},
                'date_prediction': {'type': 'string', 'format': 'date-time'},
            },
        },
        **_errors(401, 404, 500),
    },
    examples=[
        OpenApiExample(
            'Prédiction risque élevé',
            value=ML_PREDICTION_RESPONSE_EXAMPLE,
            response_only=True,
        ),
    ],
)

MLPredictionSchema = extend_schema_view(get=ML_PREDICTION_SCHEMA)


# ═══════════════════════════════════════════════════════════════════════════
# 5. REGISTRE — facilitateur pour application en masse / introspection
# ═══════════════════════════════════════════════════════════════════════════
SCHEMA_REGISTRY = {
    # (route, http_method) -> (FBV decorator, CBV decorator)
    ('/api/auth/login/', 'POST'): (LOGIN_SCHEMA, LoginViewSchema),
    ('/api/auth/register/', 'POST'): (REGISTER_SCHEMA, RegisterViewSchema),
    ('/api/patient/profile/', 'GET'): (PATIENT_PROFILE_SCHEMA, PatientProfileSchema),
    ('/api/patient/profile/', 'PUT'): (PATIENT_PROFILE_SCHEMA, PatientProfileSchema),
    ('/api/rendez-vous/', 'GET'): (RDV_LIST_GET_SCHEMA, RendezVousListSchema),
    ('/api/rendez-vous/', 'POST'): (RDV_LIST_POST_SCHEMA, RendezVousListSchema),
    ('/api/urgences/', 'POST'): (TRIGGER_URGENCE_SCHEMA, TriggerUrgenceSchema),
    ('/api/urgence/<uuid:token>/', 'GET'): (
        ACCES_URGENCE_PUBLIQUE_SCHEMA, AccesUrgencePubliqueSchema,
    ),
    ('/api/file-attente/ma-position/', 'GET'): (
        MA_FILE_ATTENTE_SCHEMA, MaFileAttenteSchema,
    ),
    ('/api/medecins/<id>/creneaux/', 'GET'): (
        CRENEAUX_MEDECIN_SCHEMA, CreneauxMedecinSchema,
    ),
    ('/api/assigner-patient/', 'POST'): (
        ASSIGNER_PATIENT_SCHEMA, AssignerPatientSchema,
    ),
    ('/api/exports/dossier-pdf/', 'GET'): (
        EXPORT_DOSSIER_PDF_SCHEMA, ExportDossierPdfSchema,
    ),
    ('/api/exports/dossier-fhir/', 'GET'): (
        EXPORT_DOSSIER_FHIR_SCHEMA, ExportDossierFhirSchema,
    ),
    ('/api/device-token/', 'POST'): (DEVICE_TOKEN_SCHEMA, DeviceTokenSchema),
    ('/api/2fa/setup/', 'POST'): (SETUP_2FA_SCHEMA, Setup2FASchema),
    ('/api/prescriptions/<id>/signer/', 'POST'): (
        SIGNER_PRESCRIPTION_SCHEMA, SignerPrescriptionSchema,
    ),
    ('/api/rgpd/anonymiser/', 'DELETE'): (
        ANONYMISER_MES_DONNEES_SCHEMA, AnonymiserMesDonneesSchema,
    ),
    ('/api/patients/recherche-floue/', 'GET'): (
        RECHERCHE_FLOUE_SCHEMA, RechercheFloueSchema,
    ),
    ('/api/health/', 'GET'): (HEALTH_CHECK_SCHEMA, HealthCheckSchema),
    ('/api/teleconsultation/', 'POST'): (
        TELECONSULTATION_CREER_SCHEMA, TeleconsultationCreerSchema,
    ),
    ('/api/ml/prediction-courante/', 'GET'): (
        ML_PREDICTION_SCHEMA, MLPredictionSchema,
    ),
}

__all__ = [
    # Tags & erreurs standard
    'API_TAGS',
    'STANDARD_ERROR_RESPONSES',
    # Schémas FBV (extend_schema direct)
    'LOGIN_SCHEMA',
    'REGISTER_SCHEMA',
    'PATIENT_PROFILE_SCHEMA',
    'RDV_LIST_GET_SCHEMA',
    'RDV_LIST_POST_SCHEMA',
    'TRIGGER_URGENCE_SCHEMA',
    'ACCES_URGENCE_PUBLIQUE_SCHEMA',
    'MA_FILE_ATTENTE_SCHEMA',
    'CRENEAUX_MEDECIN_SCHEMA',
    'ASSIGNER_PATIENT_SCHEMA',
    'EXPORT_DOSSIER_PDF_SCHEMA',
    'EXPORT_DOSSIER_FHIR_SCHEMA',
    'DEVICE_TOKEN_SCHEMA',
    'SETUP_2FA_SCHEMA',
    'SIGNER_PRESCRIPTION_SCHEMA',
    'ANONYMISER_MES_DONNEES_SCHEMA',
    'RECHERCHE_FLOUE_SCHEMA',
    'HEALTH_CHECK_SCHEMA',
    'TELECONSULTATION_CREER_SCHEMA',
    'ML_PREDICTION_SCHEMA',
    # Schémas CBV (extend_schema_view)
    'LoginViewSchema',
    'RegisterViewSchema',
    'PatientProfileSchema',
    'RendezVousListSchema',
    'TriggerUrgenceSchema',
    'AccesUrgencePubliqueSchema',
    'MaFileAttenteSchema',
    'CreneauxMedecinSchema',
    'AssignerPatientSchema',
    'ExportDossierPdfSchema',
    'ExportDossierFhirSchema',
    'DeviceTokenSchema',
    'Setup2FASchema',
    'SignerPrescriptionSchema',
    'AnonymiserMesDonneesSchema',
    'RechercheFloueSchema',
    'HealthCheckSchema',
    'TeleconsultationCreerSchema',
    'MLPredictionSchema',
    # Registre
    'SCHEMA_REGISTRY',
]
