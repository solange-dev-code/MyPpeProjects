from django.urls import path
from . import views

app_name = 'dossiers_medicaux'

urlpatterns = [
    path('', views.liste_dossiers, name='liste'),
    path('<int:pk>/', views.detail_dossier, name='detail'),
    path('nouveau/', views.nouveau_dossier, name='nouveau'),
    path('<int:pk>/modifier/', views.modifier_dossier, name='modifier'),
    path('<int:pk>/ajouter-prescription/', views.ajouter_prescription, name='ajouter_prescription'),
    path('<int:pk>/ajouter-document/', views.ajouter_document, name='ajouter_document'),
]