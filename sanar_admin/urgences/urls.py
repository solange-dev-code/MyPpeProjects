"""Configuration URLs du module urgences (interface admin HTML)."""
from django.urls import path
from . import views

app_name = 'urgences'

urlpatterns = [
    path('', views.liste_urgences, name='liste'),
    path('<uuid:uuid>/', views.detail_urgence, name='detail'),
    path('audit/', views.audit_acces_urgence, name='audit'),
]
