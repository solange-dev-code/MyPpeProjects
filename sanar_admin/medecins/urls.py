from django.urls import path
from . import views

app_name = 'medecins'

urlpatterns = [
    path('', views.liste_medecins, name='liste'),
    path('<int:pk>/', views.detail_medecin, name='detail'),
    path('ajouter/', views.ajouter_medecin, name='ajouter'),
    path('<int:pk>/modifier/', views.modifier_medecin, name='modifier'),
    path('<int:pk>/supprimer/', views.supprimer_medecin, name='supprimer'),
    path('<int:pk>/horaires/', views.horaires_medecin, name='horaires'),
    path('<int:medecin_id>/disponibilite/ajouter/', views.ajouter_disponibilite, name='ajouter_disponibilite'),
]
