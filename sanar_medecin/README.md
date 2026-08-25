# Sanar Medecin

Application Flutter **dediee aux medecins** du projet Sanar PPE. Elle est destinee a un usage mobile au lit du patient, en consultation et en teleconsultation.

## Contexte

Ce module est une application **independante** de l'app patient (`sanar/`). Elle partage le meme backend Django (`sanar_admin/`) et la meme API REST, mais expose uniquement les fonctionnes utiles au practicien :

- Tableau de bord medecin (KPIs + agenda du jour + file d'attente)
- Gestion des rendez-vous (agenda jour / semaine)
- File d'attente triee P1-P5 avec actions Appeler / Terminer / Abandonner
- Recherche et fiche patient condensed (allergies, ATCD, traitements)
- Saisie de consultation (diagnostic, code ICD-10, cout, type) + prescription
- Validation d'analyses avec flag automatique Normal / Haut / Bas / Critique
- Teleconsultation WebRTC audio/video
- Profil medecin + statistiques personnelles + deconnexion

## Installation

```bash
cd sanar_medecin
flutter pub get
flutter run            # emulateur Android (API baseUrl http://10.0.2.2:8080/api)
flutter run -d chrome  # web (API baseUrl http://127.0.0.1:8080/api)
```

### Prerequis

- Flutter SDK >= 3.11.5
- Backend Django `sanar_admin` lance sur `localhost:8080`
- Un utilisateur medecin avec 2FA TOTP active (django-otp)

## Configuration

| Parametre | Valeur |
|-----------|--------|
| API baseUrl (Android emulateur) | `http://10.0.2.2:8080/api` |
| API baseUrl (web) | `http://127.0.0.1:8080/api` |
| Couleur primaire | `#1F6C92` (bleu medical) |
| Couleur accent | `#16A34A` (vert) |
| Couleur danger | `#DC2626` (rouge urgence) |
| Fond | `#F5F7FA` |

## Endpoints API utilises

| Methode | Endpoint | Usage |
|---------|----------|-------|
| POST | `/api/auth/login/` | Authentification medecin (retourne JWT + flag `require_2fa`) |
| POST | `/api/2fa/verify/` | Verification du code TOTP 6 chiffres |
| GET | `/api/rendez-vous/` | Liste des RDV du medecin |
| GET | `/api/file-attente/ma-position/` | File d'attente mode medecin (liste P1-P5) |
| GET | `/api/patient/profile/` | Recherche / profil patient |
| GET | `/api/analyses/` | Analyses en attente de validation |
| POST | `/api/analyses/<id>/valider/` | Validation d'une analyse (saisie resultat) |
| GET | `/api/medecins/<id>/creneaux/?date=YYYY-MM-DD` | Creneaux disponibles du medecin |
| POST | `/api/device-token/` | Enregistrement du token FCM |
| POST | `/api/consultations/` | Enregistrement d'une consultation |
| POST | `/api/prescriptions/` | Enregistrement d'une prescription |

## Flux d'authentification

1. Saisie email + mot de passe sur `LoginPage`
2. Si la reponse contient `require_2fa: true` -> redirection vers `Verify2faPage`
3. Saisie du code TOTP 6 chiffres -> POST `/api/2fa/verify/`
4. En cas de succes, le token JWT est stocke via `SharedPreferences`
5. Redirection vers le `DashboardPage`

## Difference avec l'app patient (`sanar/`)

| Aspect | App patient (`sanar/`) | App medecin (`sanar_medecin/`) |
|--------|------------------------|--------------------------------|
| Utilisateur cible | Patient | Medecin |
| Authentification | Email / mot de passe | Email / mot de passe + 2FA TOTP |
| Page d'accueil | Raccourcis : urgences, QR medical, file d'attente (position patient) | KPIs medicaux + agenda du jour + file d'attente (gestion) |
| Bouton SOS | Oui (rouge, flottant) | Non |
| Teleconsultation | Non | Oui (WebRTC) |
| Saisie consultation / prescription | Non | Oui |
| Validation analyses | Non | Oui |
| Couleur primaire | `#2563EB` | `#1F6C92` (bleu medical) |

## Structure du projet

```
sanar_medecin/
├── pubspec.yaml
├── README.md
└── lib/
    ├── main.dart                       (SplashScreen + routing auth)
    ├── core/
    │   ├── constants/app_colors.dart
    │   └── theme/app_theme.dart
    ├── shared/
    │   ├── services/
    │   │   ├── api_service.dart        (Dio + JWT)
    │   │   ├── auth_service.dart       (login + 2FA TOTP)
    │   │   └── fcm_service.dart        (notifications push)
    │   └── widgets/
    │       ├── stat_card.dart          (KPI card reutilisable)
    │       └── patient_chip.dart       (badge patient)
    └── features/
        ├── auth/                       (login + verify 2FA)
        ├── dashboard/                  (KPIs + agenda + file d'attente)
        ├── appointments/               (agenda jour/semaine + detail)
        ├── file_attente/               (liste P1-P5 triee)
        ├── patients/                   (recherche + fiche condensed)
        ├── consultation/               (consultation + prescription)
        ├── analyses/                   (liste + validation)
        ├── teleconsultation/           (WebRTC audio/video)
        └── profile/                    (profil medecin + stats + logout)
```

## Licences

Projet PPE - usage pedagogique.
