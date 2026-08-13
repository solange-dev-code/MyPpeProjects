from django.urls import path
from . import views

app_name = 'analyses'

urlpatterns = [
    path('', views.liste_analyses, name='liste'),
    path('<int:pk>/', views.detail_analyse, name='detail'),
    path('<int:pk>/valider/', views.valider_analyse, name='valider'),
    path('ajouter/', views.ajouter_analyse, name='ajouter'),
    path('resultats/', views.resultats_analyse, name='resultats'),
    
]