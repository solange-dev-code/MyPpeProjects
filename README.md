# Sanar — Application Médicale

Application médicale fullstack composée de :
- `sanar/` → Application mobile Flutter (patient)
- `sanar_admin/` → Interface d'administration Django (médecin/admin)

## Stack technique
- Backend : Django 6.0.5 + Django REST Framework
- Mobile : Flutter 3.41.7
- Base de données : PostgreSQL (local) / Neon (cloud)
- Auth : JWT (djangorestframework-simplejwt)

## Lancement

### Backend Django
cd sanar_admin
python manage.py runserver 127.0.0.1:8080

### Mobile Flutter
cd sanar
flutter run