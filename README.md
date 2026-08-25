# Sanar — Application Médicale

Application médicale fullstack composée de :
- `sanar/` → Application mobile Flutter (patient)
- `sanar_admin/` → Interface d'administration Django (médecin/admin)

## Stack technique
- Backend : Django 6.0.5+ + Django REST Framework
- Mobile : Flutter 3.41.7
- Base de données : PostgreSQL (local) / Neon (cloud)
- Auth : JWT (djangorestframework-simplejwt) + 2FA TOTP (médecins/personnel)
- Sécurité : Argon2id (mots de passe) + AES-256-GCM (champs sensibles au repos)

## Fonctionnalités principales

### Modules existants (v1.0)
- Gestion des patients, médecins, hôpitaux
- Rendez-vous avec détection de conflits (anti double-booking)
- Consultations, analyses, dossiers médicaux
- Facturation multi-moyens (Mobile Money ouest-africain)
- Messagerie interne asynchrone
- Dashboard admin avec KPIs

### Nouvelles fonctionnalités (v2.0 — améliorations PPE)
- **Module Urgences** : bouton SOS Flutter, algorithme Haversine d'hôpital optimal, notifications FCM+SMS+WhatsApp
- **QR Code Médical** : carte de santé imprimable, accès d'urgence par token UUID avec audit RGPD
- **File d'attente temps réel** : triage P1-P5, algorithme de file prioritaire, estimation temps moyen mobile
- **Disponibilités médecin** : plages récurrentes, génération automatique de créneaux, gestion des congés
- **Assignation multi-hôpitaux** : algorithme de scoring (distance + charge + lits)
- **Analyses enrichies** : catalogue structuré, référentiel par âge/sexe, alertes critiques automatiques, graphiques d'évolution
- **Exports** : PDF (WeasyPrint), CSV (statistiques), FHIR R4 (interopérabilité SIH)
- **Télécommunications** : FCM (push), Twilio (SMS), WhatsApp Business
- **Sécurité avancée** : Argon2id, chiffrement au repos, audit trail (django-auditlog), 2FA TOTP (django-otp)

## Installation

### 1. Backend Django
```bash
cd sanar_admin
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copier .env.example en .env et remplir les valeurs
cp .env.example .env
# Générer SECRET_KEY :
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# Générer DJANGO_ENCRYPTION_KEY :
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Migrations
python manage.py migrate

# Créer un super-user
python manage.py createsuperuser

# Lancer
python manage.py runserver 127.0.0.1:8080
```

### 2. Mobile Flutter
```bash
cd sanar
flutter pub get
flutter run
```

## Sécurité — configurations critiques

Le fichier `settings.py` a été sécurisé (vs version initiale) :
- `SECRET_KEY` depuis variable d'environnement (plus hardcodée)
- `DEBUG=False` par défaut (plus jamais True en prod)
- `ALLOWED_HOSTS` explicite (plus `['*']`)
- `CORS_ALLOW_ALL_ORIGINS=False` (origines Flutter uniquement)
- Security headers (HSTS, SSL redirect, secure cookies)
- `Argon2id` en priorité pour le hachage des mots de passe
- Chiffrement AES-256-GCM des champs médicaux sensibles au repos

## API REST

Documentation des endpoints principaux :

### Auth
- `POST /api/auth/login/` — connexion (JWT)
- `POST /api/auth/register/` — inscription patient
- `POST /api/auth/refresh/` — refresh token JWT
- `POST /api/2fa/setup/` — génère secret TOTP + QR code
- `POST /api/2fa/verify/` — vérifie code TOTP

### Patient
- `GET/PUT /api/patient/profile/`
- `GET /api/dossier-medical/`
- `GET /api/rendez-vous/`
- `POST /api/rendez-vous/` (avec détection conflit)

### Urgences (NOUVEAU)
- `POST /api/urgences/` — déclenche urgence (bouton SOS)
- `GET /api/urgences/mes-urgences/` — historique
- `GET /api/urgence/<uuid:token>/` — **PUBLIC** accès d'urgence par QR code
- `POST /api/urgence/regenerer-qr/` — révocation + nouveau token
- `POST /api/urgence/toggle-qr/` — active/désactive

### File d'attente (NOUVEAU)
- `GET /api/file-attente/ma-position/`

### Créneaux médecin (NOUVEAU)
- `GET /api/medecins/<id>/creneaux/?date=YYYY-MM-DD`

### Assignation hôpital (NOUVEAU)
- `POST /api/assigner-patient/`

### Exports (NOUVEAU)
- `GET /api/exports/dossier-pdf/` — PDF du dossier
- `GET /api/exports/dossier-fhir/` — JSON FHIR R4

### Notifications (NOUVEAU)
- `POST /api/device-token/` — enregistre token FCM
- `DELETE /api/device-token/<token>/` — supprime token
- `POST /api/test-notification/` — test push

## Tests
```bash
cd sanar_admin
python manage.py test urgences file_attente
```

## Conformité RGPD
- Chiffrement au repos (AES-256-GCM)
- Audit trail automatique (create/update/delete) sur modèles sensibles
- Journalisation des accès en lecture (endpoint d'urgence)
- Notification au patient à chaque accès d'urgence
- Droit à l'oubli : `Patient.delete()` anonymise
- Portabilité : export FHIR + PDF

## Licence
Projet PPE — usage académique.
