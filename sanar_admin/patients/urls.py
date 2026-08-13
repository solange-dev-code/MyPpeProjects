from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('', views.liste_patients, name='liste'),
    path('<int:pk>/', views.detail_patient, name='detail'),
    path('<int:pk>/dossier/', views.voir_dossier_patient, name='dossier'),
    path('ajouter/', views.ajouter_patient, name='ajouter'),
    path('<int:pk>/modifier/', views.modifier_patient, name='modifier'),
    path('<int:pk>/supprimer/', views.supprimer_patient, name='supprimer'),
]