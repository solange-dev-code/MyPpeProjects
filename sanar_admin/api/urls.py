from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('auth/login/', views.login_view, name='api_login'),
    path('auth/register/', views.register_view, name='api_register'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Patient
    path('patient/profile/', views.patient_profile, name='patient_profile'),

    # Rendez-vous
    path('rendez-vous/', views.rendez_vous_list, name='rdv_list'),
    path('rendez-vous/<int:pk>/', views.rendez_vous_detail, name='rdv_detail'),

    # Consultations
    path('consultations/', views.consultations_list, name='consultations'),

    # Analyses
    path('analyses/', views.analyses_list, name='analyses'),

    # Dossier médical
    path('dossier-medical/', views.dossier_medical, name='dossier'),

    # Facturation
    path('factures/', views.factures_list, name='factures'),

    # Messagerie
    path('conversations/', views.conversations_list, name='conversations'),
    path('conversations/<int:conv_id>/messages/', views.messages_list, name='messages'),

    # Médecins
    path('medecins/', views.medecins_list, name='medecins'),

    # Hôpitaux
    path('hopitaux/', views.hopitaux_list, name='hopitaux'),

    # Notifications
    path('notifications/', views.notifications_list, name='notifications'),
]