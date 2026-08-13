from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # ── Auth ──
    path('auth/login/', views.login_view, name='api_login'),
    path('auth/register/', views.register_view, name='api_register'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ── Patient ──
    path('patient/profile/', views.patient_profile, name='patient_profile'),

    # ── Rendez-vous ──
    path('rendez-vous/', views.rendez_vous_list, name='rdv_list'),
    path('rendez-vous/<int:pk>/', views.rendez_vous_detail, name='rdv_detail'),

    # ── Consultations ──
    path('consultations/', views.consultations_list, name='consultations'),

    # ── Analyses ──
    path('analyses/', views.analyses_list, name='analyses'),

    # ── Dossier médical ──
    path('dossier-medical/', views.dossier_medical, name='dossier'),

    # ── Facturation ──
    path('factures/', views.factures_list, name='factures'),

    # ── Messagerie ──
    path('conversations/', views.conversations_list, name='conversations'),
    path('conversations/<int:conv_id>/messages/', views.messages_list, name='messages'),

    # ── Médecins ──
    path('medecins/', views.medecins_list, name='medecins'),

    # ── Hôpitaux ──
    path('hopitaux/', views.hopitaux_list, name='hopitaux'),

    # ── Notifications ──
    path('notifications/', views.notifications_list, name='notifications'),

    # ═══ NOUVEAU : URGENCES ═══
    path('urgences/', views.trigger_urgence, name='trigger_urgence'),
    path('urgences/mes-urgences/', views.mes_urgences, name='mes_urgences'),

    # ═══ NOUVEAU : Accès d'urgence PUBLIC par QR code ═══
    # Endpoint PUBLIC (AllowAny) — sécurisé par token UUID opaque
    path('urgence/<uuid:token>/', views.acces_urgence_publique, name='urgence_publique'),
    path('urgence/regenerer-qr/', views.regenerer_qr_urgence, name='regenerer_qr'),
    path('urgence/toggle-qr/', views.toggle_qr_urgence, name='toggle_qr'),

    # ═══ NOUVEAU : File d'attente ═══
    path('file-attente/ma-position/', views.ma_file_attente, name='ma_file_attente'),

    # ═══ NOUVEAU : Créneaux disponibles ═══
    path('medecins/<int:medecin_id>/creneaux/', views.creneaux_medecin, name='creneaux_medecin'),

    # ═══ NOUVEAU : Assignation multi-hôpitaux ═══
    path('assigner-patient/', views.assigner_patient, name='assigner_patient'),

    # ═══ NOUVEAU : Exports ═══
    path('exports/dossier-pdf/', views.export_mon_dossier_pdf, name='export_dossier_pdf'),
    path('exports/dossier-fhir/', views.export_mon_dossier_fhir, name='export_dossier_fhir'),

    # ═══ NOUVEAU : Token FCM (notifications push) ═══
    path('device-token/', views.register_device_token, name='register_device_token'),
    path('device-token/<str:token>/', views.unregister_device_token, name='unregister_device_token'),

    # ═══ NOUVEAU : 2FA TOTP ═══
    path('2fa/setup/', views.setup_2fa, name='setup_2fa'),
    path('2fa/verify/', views.verify_2fa, name='verify_2fa'),

    # ═══ NOUVEAU : Test notification ═══
    path('test-notification/', views.test_notification, name='test_notification'),
]
