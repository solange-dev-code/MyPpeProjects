from django.urls import path
from . import views

app_name = 'consultations'

urlpatterns = [
    path('', views.liste_consultations, name='liste'),
    path('<int:pk>/', views.detail_consultation, name='detail'),
    path('ajouter/', views.ajouter_consultation, name='ajouter'),
    path('<int:pk>/modifier/', views.modifier_statut, name='modifier_statut'),
]