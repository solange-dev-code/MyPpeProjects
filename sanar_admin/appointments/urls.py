from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.liste_appointments, name='liste'),
    path('<int:pk>/', views.detail_appointment, name='detail'),
    path('ajouter/', views.ajouter_appointment, name='ajouter'),
    path('<int:pk>/modifier/', views.modifier_statut, name='modifier_statut'),
]