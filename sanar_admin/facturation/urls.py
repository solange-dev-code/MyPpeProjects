from django.urls import path
from . import views

app_name = 'facturation'

urlpatterns = [
    path('', views.liste_factures, name='liste'),
    path('<int:pk>/', views.detail_facture, name='detail'),
    path('ajouter/', views.ajouter_facture, name='ajouter'),
    path('<int:pk>/payer/', views.marquer_paye, name='payer'),
    path('<int:pk>/supprimer/', views.supprimer_facture, name='supprimer'),
]