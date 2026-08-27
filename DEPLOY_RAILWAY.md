# Déploiement Railway — Sanar (all-in-one supervisord)

Ce guide explique comment déployer le projet Sanar sur Railway avec **tous les services fonctionnels** (API REST, WebSockets WebRTC, Celery worker, Celery beat) dans un seul conteneur via supervisord.

## Architecture Railway (all-in-one)

```
┌─────────────── Railway (.up.railway.app) ───────────────┐
│                                                          │
│  ┌──────────────┐   ┌──────────────┐                    │
│  │ PostgreSQL   │   │    Redis     │  ← Plugins Railway │
│  │ (Railway DB)  │   │  (Railway)   │    (auto-provision)│
│  └──────┬───────┘   └───────┬──────┘                    │
│         └────────┬─────────┘                            │
│                  ▼                                       │
│  ┌──────────────────────────────────────────┐            │
│  │  Conteneur Railway (all-in-one)          │            │
│  │  supervisord lance 4 processus :         │            │
│  │                                          │            │
│  │  ┌─────────────────────────────────────┐ │            │
│  │  │ 1. gunicorn  ($PORT=8080)          │ │            │
│  │  │    → API REST + admin Django        │ │            │
│  │  │    → 38 endpoints JWT authentifiés  │ │            │
│  │  │    → Swagger UI + ReDoc             │ │            │
│  │  └─────────────────────────────────────┘ │            │
│  │  ┌─────────────────────────────────────┐ │            │
│  │  │ 2. daphne    ($PORT_WS=8001)       │ │            │
│  │  │    → WebSockets WebRTC             │ │            │
│  │  │    → Téléconsultation audio/vidéo   │ │            │
│  │  │    → Chat médecin-patient temps réel│ │            │
│  │  └─────────────────────────────────────┘ │            │
│  │  ┌─────────────────────────────────────┐ │            │
│  │  │ 3. celery worker (concurrency 2)    │ │            │
│  │  │    → Envoi SMS Twilio               │ │            │
│  │  │    → Notifications push FCM         │ │            │
│  │  │    → Génération exports PDF         │ │            │
│  │  │    → Entraînement modèle ML         │ │            │
│  │  │    → Notifications urgences         │ │            │
│  │  └─────────────────────────────────────┘ │            │
│  │  ┌─────────────────────────────────────┐ │            │
│  │  │ 4. celery beat (scheduler)         │ │            │
│  │  │    → Rappels RDV J-1 (daily 18h)   │ │            │
│  │  │    → Rappels RDV H-2 (hourly)       │ │            │
│  │  │    → Recalcul file d'attente (5min) │ │            │
│  │  │    → Re-notif urgences (10min)     │ │            │
│  │  │    → Nettoyage RGPD (mensuel)      │ │            │
│  │  │    → ML ré-entraînement (hebdo)    │ │            │
│  │  └─────────────────────────────────────┘ │            │
│  └──────────────────────────────────────────┘            │
│             │                                            │
│             ▼                                            │
│   https://sanar-ppe.up.railway.app                      │
└──────────────────────────────────────────────────────────┘
```

## Déploiement en 3 commandes

### 1. Installer Railway CLI et se connecter

```bash
npm install -g @railway/cli
railway login   # Ouvre le browser pour authentification
```

### 2. Lancer le script de déploiement automatisé

```bash
cd /home/z/my-project/repo-analysis/MyPpeProjects
bash /home/z/my-project/scripts/railway_deploy.sh
```

Le script effectue automatiquement :
- Création du projet Railway `Sanar-PPE`
- Provisioning PostgreSQL + Redis managés
- Génération des clés `SECRET_KEY` + `ENCRYPTION_KEY` aléatoires
- Configuration de toutes les variables d'environnement
- Build du conteneur (Nixpacks ou Dockerfile.railway)
- Démarrage des 4 services via supervisord
- Création du super-user `admin / AdminSanar2026!`
- Seed de 3 patients + 1 médecin de démo
- Affichage de l'URL publique

### 3. Vérifier le déploiement (3-5 min)

```bash
# Health check — doit retourner status=ok
curl https://<votre-domaine>.up.railway.app/api/health/

# Swagger UI — documentation interactive
# Ouvrir : https://<votre-domaine>.up.railway.app/api/docs/

# Admin Django
# Ouvrir : https://<votre-domaine>.up.railway.app/admin/
# Login : admin / AdminSanar2026!

# Login API (patient démo)
curl -X POST https://<votre-domaine>.up.railway.app/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"username":"patient_0@demo.app","password":"Patient2026!"}'
```

## Variables d'environnement Railway

### Auto-fournies par Railway (ne pas définir)

| Variable | Description |
|----------|-------------|
| `PORT` | Port HTTP dynamique (gunicorn écoute dessus) |
| `DATABASE_URL` | PostgreSQL Railway (format `postgres://user:pass@host:port/db`) |
| `REDIS_URL` | Redis Railway (format `redis://:pass@host:port`) |
| `REDIS_PRIVATE_URL` | Redis réseau interne Railway (plus rapide) |
| `RAILWAY_PUBLIC_DOMAIN` | Domaine `.up.railway.app` |

### À définir manuellement (une seule fois)

| Variable | Valeur recommandée | Description |
|----------|-------------------|-------------|
| `DJANGO_SECRET_KEY` | Générée aléatoirement (50+ chars) | Clé secrète Django |
| `DJANGO_DEBUG` | `False` | Mode production |
| `DJANGO_ENCRYPTION_KEY` | Générée (Fernet base64) | Chiffrement AES-256 champs sensibles |
| `DJANGO_SUPERUSER_USERNAME` | `admin` | Login admin Django |
| `DJANGO_SUPERUSER_PASSWORD` | `AdminSanar2026!` | Mot de passe admin |
| `DJANGO_SUPERUSER_EMAIL` | `admin@sanar.app` | Email admin |
| `DJANGO_SEED_DEMO` | `True` | Seed 3 patients + 1 médecin de démo |
| `PORT_WS` | `8001` | Port Daphne pour WebSockets |

### Optionnelles (services externes)

| Variable | Service | Statut sans config |
|----------|---------|-------------------|
| `TWILIO_ACCOUNT_SID` + `AUTH_TOKEN` + `FROM_NUMBER` | SMS Twilio | SMS non envoyés (warning log) |
| `FCM_SERVER_KEY` + `FCM_PROJECT_ID` | Notifications push FCM | Push non envoyés (warning log) |
| `SENTRY_DSN` | Monitoring erreurs | Sentry désactivé |
| `GOOGLE_CLIENT_ID` + `SECRET` | Synchro Google Calendar | Calendar désactivé |

## Architecture des fichiers Railway

| Fichier | Rôle |
|---------|------|
| `railway.json` | Config build NIXPACKS + healthcheck + restart policy |
| `nixpacks.toml` | Build optimisé Python 3.12 + deps système + supervisord |
| `Dockerfile.railway` | Alternative Docker (si Nixpacks échoue) |
| `Procfile` | Compatibilité Heroku buildpack |
| `sanar_admin/start_all.sh` | Script principal (lance supervisord) |
| `sanar_admin/start.sh` | Backend gunicorn uniquement (mode simple) |
| `sanar_admin/start_worker.sh` | Celery worker uniquement (mode multi-services) |
| `sanar_admin/start_beat.sh` | Celery beat uniquement (mode multi-services) |
| `sanar_admin/start_daphne.sh` | Daphne WebSockets uniquement (mode multi-services) |
| `sanar_admin/supervisord.conf` | Config supervisord (4 processus) |

## Comptes de démo (si `DJANGO_SEED_DEMO=True`)

| Type | Username | Password | Rôle |
|------|----------|----------|------|
| Admin Django | `admin` | `AdminSanar2026!` | Accès admin complet |
| Patient 1 | `patient_0@demo.app` | `Patient2026!` | Patient Kossi Afi |
| Patient 2 | `patient_1@demo.app` | `Patient2026!` | Patient Mansour Bou |
| Patient 3 | `patient_2@demo.app` | `Patient2026!` | Patient Adjovi Claire |
| Médecin | `dr_demo@demo.app` | `Medecin2026!` | Dr. Demo (généraliste) |

## Endpoints à tester après déploiement

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/health/` | Health check (public) |
| GET | `/api/docs/` | Swagger UI interactif |
| GET | `/api/redoc/` | ReDoc documentation |
| POST | `/api/auth/login/` | Login → JWT |
| POST | `/api/auth/register/` | Inscription patient |
| GET | `/api/patient/profile/` | Profil patient (JWT) |
| GET | `/api/medecins/` | Liste médecins |
| GET | `/api/hopitaux/` | Liste hôpitaux |
| POST | `/api/rendez-vous/` | Prendre RDV (détection conflit) |
| POST | `/api/urgences/` | Bouton SOS Flutter |
| GET | `/api/urgence/<uuid:token>/` | Accès PUBLIC par QR code |
| GET | `/api/file-attente/ma-position/` | Position file d'attente |
| POST | `/api/assigner-patient/` | Assignation multi-hôpitaux |
| GET | `/api/exports/dossier-pdf/` | Export PDF dossier |
| GET | `/api/exports/dossier-fhir/` | Export FHIR R4 JSON |
| POST | `/api/prescriptions/<id>/signer/` | Signature électronique |
| DELETE | `/api/rgpd/anonymiser/` | Droit à l'oubli RGPD |
| GET | `/api/patients/recherche-floue/?q=Dupont` | Recherche floue |

## Limitations connues (plan gratuit Railway)

| Ressource | Plan gratuit | Plan Hobby (5$/mois) |
|-----------|--------------|---------------------|
| CPU | 0.5 vCPU partagé | 1 vCPU |
| RAM | 500 MB | 1 GB |
| Crédit | 5$ (≈ 500h) | Illimité |
| Sleep | Après 30 min idle | Toujours actif |
| SSL | Auto (Let's Encrypt) | Auto |
| Domaine | `.up.railway.app` | Personnalisé OK |

**Pour la démo PPE** : le plan gratuit suffit pour 500 heures de tests (≈ 3 semaines à 5h/jour).

## Limitations techniques

1. **WebSockets sans reverse proxy** : Daphne écoute sur le port 8001, séparé du port principal 8080 (gunicorn). Pour accéder aux WebSockets depuis l'extérieur, configurer un reverse proxy ou utiliser Railway TCP proxy. La téléconsultation WebRTC peut nécessiter une configuration supplémentaire.

2. **Coturn TURN non déployé** : le serveur TURN pour NAT traversal WebRTC n'est pas inclus. Pour la téléconsultation entre 2 clients sur réseaux différents, ajouter un service Coturn séparé.

3. **Fichiers media non persistants** : les fichiers uploadés (analyses PDF, documents) sont stockés dans `/app/media/` qui est éphémère. Pour la persistance, configurer un bucket S3 ou un volume Railway persistant.

## Logs et debugging

```bash
# Logs en temps réel (tous les services)
railway logs

# Ouvrir un shell dans le conteneur
railway shell

# Vérifier les variables
railway variables

# Redémarrer le service
railway redeploy

# Statut du service
railway status
```

## Coût estimé (démo PPE)

- Plan gratuit (5$ credit) : ~500 heures de tests
- Plan Hobby (5$/mois) : démo 24/7 pendant 1 mois
- PostgreSQL Railway : inclus dans le crédit (500 MB gratuits)
- Redis Railway : inclus dans le crédit (500 MB gratuits)
- **Coût total ≈ 5$ pour une démo complète de soutenance**

## Arrêter / supprimer le déploiement

```bash
# Suspendre temporairement (ne supprime pas les données)
railway down

# Reprendre
railway up

# Supprimer le projet (DELETE toutes les données !)
railway delete
```
