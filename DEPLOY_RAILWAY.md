# Déploiement Railway — Sanar

Ce guide explique comment déployer le projet Sanar sur Railway (plateforme PaaS) pour une démo publique ou un environnement de staging.

## Prérequis

1. Compte Railway (gratuit, 5$ de crédit/mois) : https://railway.app
2. Le dépôt GitHub du projet : https://github.com/solange-dev-code/MyPpeProjects
3. (Optionnel) Railway CLI installé localement

## Architecture Railway

Railway fournit automatiquement PostgreSQL et Redis managés. Le backend Django est déployé comme service unique via le `nixpacks.toml` ou `Dockerfile.railway`.

```
┌──────────────────────────────────────────────┐
│  Railway (https://sanar.up.railway.app)      │
│                                               │
│  ┌─────────────────┐   ┌─────────────────┐   │
│  │  PostgreSQL     │   │  Redis          │   │
│  │  (Railway DB)   │   │  (Railway Redis) │   │
│  └────────┬────────┘   └────────┬────────┘   │
│           │                      │            │
│           └──────────┬──────────┘            │
│                      │                       │
│           ┌──────────▼──────────┐            │
│           │  Backend Django     │            │
│           │  (gunicorn 4 workers)│           │
│           │  - API REST         │            │
│           │  - Admin            │            │
│           │  - Healthcheck      │            │
│           └──────────┬──────────┘            │
│                      │                       │
│                  PORT 8080                   │
│                      ▼                       │
│      https://sanar.up.railway.app            │
│                      │                       │
│           ┌──────────▼──────────┐            │
│           │  Apps Flutter        │           │
│           │  (patient + médecin)  │           │
│           └──────────────────────┘            │
└───────────────────────────────────────────────┘
```

## Déploiement étape par étape

### 1. Connecter le dépôt GitHub à Railway

```bash
# Option A : Via le dashboard Railway
# 1. Aller sur https://railway.app/new
# 2. "Deploy from GitHub repo"
# 3. Sélectionner solange-dev-code/MyPpeProjects
# 4. Cliquer "Deploy Now"

# Option B : Via Railway CLI
npm install -g @railway/cli
railway login
railway init  # Crée un nouveau projet Railway
railway link  # Lie le dépôt local au projet Railway
```

### 2. Ajouter les services PostgreSQL et Redis

Dans le dashboard Railway :
1. **+ New → Database → PostgreSQL** (Railway provisionne automatiquement)
2. **+ New → Database → Redis** (Railway provisionne automatiquement)
3. Railway génère automatiquement les variables `DATABASE_URL` et `REDIS_URL`

### 3. Configurer les variables d'environnement

Dans Railway → Settings → Variables, ajouter :

```env
DJANGO_SECRET_KEY=<générer via : python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DJANGO_DEBUG=False
DJANGO_ENCRYPTION_KEY=<générer via : python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">

# Super-user auto (optionnel, pour admin)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=AdminSanar2026!
DJANGO_SUPERUSER_EMAIL=admin@sanar.app

# Seed données démo
DJANGO_SEED_DEMO=True

# Services externes (optionnels pour démo)
# TWILIO_ACCOUNT_SID=
# FCM_SERVER_KEY=
# SENTRY_DSN=
```

Railway injecte automatiquement (ne pas définir manuellement) :
- `PORT` (port HTTP dynamique)
- `DATABASE_URL` (PostgreSQL Railway)
- `REDIS_URL` (Redis Railway)
- `RAILWAY_PUBLIC_DOMAIN` (domaine .railway.app)

### 4. Déclencher le déploiement

```bash
# Via CLI
railway up

# Ou via git push (si Railway webhook configuré)
git push origin main
# Railway détecte le push et rebuild automatiquement
```

### 5. Vérifier le déploiement

Une fois déployé (3-5 minutes), tester :

```bash
# Health check
curl https://<votre-domaine>.up.railway.app/api/health/
# Réponse attendue : {"status":"ok","services":{"database":"ok","redis":"ok","storage":"ok"}}

# Swagger UI (documentation API)
# Ouvrir : https://<votre-domaine>.up.railway.app/api/docs/

# Admin Django
# Ouvrir : https://<votre-domaine>.up.railway.app/admin/
# Login : admin / AdminSanar2026! (si DJANGO_SUPERUSER_* défini)

# Login API (patient démo)
curl -X POST https://<votre-domaine>.up.railway.app/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"username":"patient_0@demo.app","password":"Patient2026!"}'
```

### 6. Pointer les apps Flutter vers Railway

Modifier `sanar/lib/shared/services/api_service.dart` :

```dart
static String get baseUrl {
    // Production Railway
    return 'https://<votre-domaine>.up.railway.app/api';
    // En dev local :
    // return 'http://10.0.2.2:8080/api';
}
```

Idem dans `sanar_medecin/lib/shared/services/api_service.dart`.

## Limitations Railway (plan gratuit)

| Ressource | Plan gratuit | Plan Hobby (5$/mois) |
|-----------|--------------|---------------------|
| CPU | 0.5 vCPU | 1 vCPU |
| RAM | 500 MB | 1 GB |
| Crédit | 5$ (≈ 500h) | Illimité |
| SSL | Auto (Let's Encrypt) | Auto |
| Domaine | .up.railway.app | Personnalisé OK |
| Sleep | Après 30 min idle | Toujours actif |

**Pour la démo PPE** : le plan gratuit suffit pour 500 heures de tests.

## Limitations de ce déploiement

Ce setup Railway déploie **uniquement le backend Django**. Les fonctionnalités suivantes nécessitent des services séparés non inclus dans la démo :

1. **Celery worker** : les rappels RDV automatiques ne fonctionneront pas. Pour activer, créer un second service Railway avec `startCommand: celery -A sanar_admin worker --loglevel=info`.

2. **Celery beat** : les tâches planifiées ne se déclenchent pas. Idem, second service Railway.

3. **Daphne (WebSockets)** : la téléconsultation WebRTC ne fonctionne pas. Pour activer, remplacer gunicorn par Daphne dans `start.sh`.

4. **Coturn (TURN)** : le serveur TURN pour NAT traversal WebRTC n'est pas déployé. À configurer séparément.

Pour la démo PPE, ces limitations sont acceptables : l'API REST, le dashboard, l'admin, le bouton SOS (sans notif push), le QR code médical, la file d'attente, les exports et la signature électronique fonctionnent.

## Logs et debugging

```bash
# Logs en temps réel
railway logs

# Ouvrir un shell dans le conteneur
railway shell

# Variables d'environnement
railway variables

# Redémarrer le service
railway redeploy
```

## Arrêter / supprimer le déploiement

```bash
# Suspendre temporairement
railway down

# Supprimer le projet (DELETE toutes les données !)
railway delete
```

## Coût estimé (démo PPE)

- Plan gratuit (5$ credit) : suffisant pour ~500 heures de tests
- Plan Hobby (5$/mois) : pour une démo 24/7 pendant 1 mois
- Coût total ≈ 5$ pour une démo complète de soutenance
