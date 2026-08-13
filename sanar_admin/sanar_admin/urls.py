"""URL configuration for sanar_admin project."""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
)


urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Apps existantes
    path('', include('dashboard.urls')),
    path('patients/', include('patients.urls')),
    path('consultations/', include('consultations.urls')),
    path('appointments/', include('appointments.urls')),
    path('analyses/', include('analyses.urls')),
    path('facturation/', include('facturation.urls')),
    path('messagerie/', include('messagerie.urls')),
    path('dossiers-medicaux/', include('dossiers_medicaux.urls')),
    path('users/', include('users_app.urls')),
    path('calendrier/', include('calendrier.urls')),
    path('medecins/', include('medecins.urls')),
    path('hopitaux/', include('hopitaux.urls')),

    # Apps ajoutées (phase 2)
    path('urgences/', include('urgences.urls')),
    path('file-attente/', include('file_attente.urls')),
    path('exports/', include('exports.urls')),

    # API REST (Flutter) — tous les endpoints /api/...
    # teleconsultation et ml_predictions sont inclus sous /api/
    path('api/', include('api.urls')),

    # ═══ NOUVEAU : Documentation API Swagger/OpenAPI (phase 3) ═══
    path('api/schema/', SpectacularAPIView.as_view(), name='api_schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api_schema'),
         name='api_docs'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='api_schema'),
         name='api_redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
