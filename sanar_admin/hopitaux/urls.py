from django.urls import path
from . import views

app_name = 'hopitaux'

urlpatterns = [
    path('', views.liste_hopitaux, name='liste'),
    path('ajouter/', views.ajouter_hopital, name='ajouter'),
    path('<int:pk>/modifier/', views.modifier_hopital, name='modifier'),
    path('<int:pk>/supprimer/', views.supprimer_hopital, name='supprimer'),
]