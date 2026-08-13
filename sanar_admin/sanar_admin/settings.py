"""
Django settings for sanar_admin project — version sécurisée.

Sécurité (vs version initiale) :
- SECRET_KEY depuis variable d'environnement (plus hardcodée)
- DEBUG depuis env, False par défaut (plus jamais True en prod)
- ALLOWED_HOSTS explicite (plus ['*'])
- CORS restrictif (plus CORS_ALLOW_ALL_ORIGINS=True)
- Security headers (HSTS, SSL redirect, secure cookies)
- Argon2id en priorité pour le hachage des mots de passe
- Durée de session réduite (1h d'inactivité)
"""

from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ──────────────────────────────────────────────────────────────
# 1. SECRET_KEY (CRITIQUE) — ne plus jamais être hardcodée
# ──────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError(
        "DJANGO_SECRET_KEY environment variable is required. "
        "Generate one with: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
    )

# ──────────────────────────────────────────────────────────────
# 2. DEBUG (CRITIQUE) — False par défaut, True uniquement si explicitement demandé
# ──────────────────────────────────────────────────────────────
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

# ──────────────────────────────────────────────────────────────
# 3. ALLOWED_HOSTS (CRITIQUE) — explicite, plus jamais ['*']
# ──────────────────────────────────────────────────────────────
ALLOWED_HOSTS = os.getenv(
    'DJANGO_ALLOWED_HOSTS',
    'localhost,127.0.0.1,sanar.app,www.sanar.app'
).split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 3rd-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_otp',                       # 2FA TOTP (phase 3)
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'auditlog',                         # audit trail (phase 3)
    'cryptography',                     # django-cryptography (phase 3)
    # Apps Sanar
    'dashboard',
    'patients',
    'consultations',
    'appointments',
    'analyses',
    'facturation',
    'messagerie',
    'dossiers_medicaux',
    'users_app',
    'calendrier',
    'medecins',
    'hopitaux',
    'personnel',
    'api',
    # Nouvelles apps (améliorations)
    'urgences',                         # module urgences + QR code (phase 2)
    'file_attente',                     # file d'attente temps réel (phase 2)
    'exports',                          # export PDF/CSV/FHIR (phase 4)
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # ← en premier
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',     # 2FA (phase 3)
    'auditlog.middleware.AuditlogMiddleware',  # audit trail (phase 3)
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sanar_admin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sanar_admin.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 10}},            # 10 caractères min (vs 8 par défaut)
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ──────────────────────────────────────────────────────────────
# 4. Argon2id en priorité pour le hachage des mots de passe (CRITIQUE)
#    Plus résistant aux attaques GPU que PBKDF2 (par défaut Django)
# ──────────────────────────────────────────────────────────────
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Lome'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# JWT — durées plus courtes (sécurité)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),   # 1h au lieu de 24h
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,              # révoque l'ancien refresh
    'ALGORITHM': 'HS256',
}

# ──────────────────────────────────────────────────────────────
# 5. CORS restrictif (CRITIQUE) — plus jamais CORS_ALLOW_ALL_ORIGINS=True
# ──────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    'https://sanar.app',
    'https://www.sanar.app',
    # Dev only :
    'http://localhost:8080',
    'http://127.0.0.1:8080',
    'http://localhost:5000',
]
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

# ──────────────────────────────────────────────────────────────
# 6. Security headers (CRITIQUE en production)
# ──────────────────────────────────────────────────────────────
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000                  # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    X_FRAME_OPTIONS = 'DENY'

# Session plus courte — 1h d'inactivité
SESSION_COOKIE_AGE = 3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# ──────────────────────────────────────────────────────────────
# 7. Clé de chiffrement pour django-cryptography (champs sensibles au repos)
#    En production, stocker dans un vault (HashiCorp Vault, AWS KMS...)
# ──────────────────────────────────────────────────────────────
FIELD_ENCRYPTION_KEY = os.getenv('DJANGO_ENCRYPTION_KEY')
if not FIELD_ENCRYPTION_KEY:
    # Génère une clé éphémère en dev (NE JAMAIS faire ça en prod)
    if DEBUG:
        from cryptography.fernet import Fernet
        FIELD_ENCRYPTION_KEY = Fernet.generate_key().decode()
    else:
        raise RuntimeError(
            "DJANGO_ENCRYPTION_KEY environment variable is required in production. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )

# ──────────────────────────────────────────────────────────────
# 8. Logging structuré
# ──────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'sanar.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 Mo
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO' if not DEBUG else 'DEBUG',
        },
        'sanar': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'auditlog': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# ──────────────────────────────────────────────────────────────
# 9. Twilio / SMS (configuration optionnelle, phase 2)
# ──────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER', '')

# Firebase Cloud Messaging (push notifications)
FCM_SERVER_KEY = os.getenv('FCM_SERVER_KEY', '')
FCM_PROJECT_ID = os.getenv('FCM_PROJECT_ID', '')

# WhatsApp Business API
WHATSAPP_API_TOKEN = os.getenv('WHATSAPP_API_TOKEN', '')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')
