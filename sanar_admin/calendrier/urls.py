from django.urls import path
from . import views

app_name = 'calendrier'

urlpatterns = [
    path('', views.calendrier, name='calendrier'),
    path('ajouter/', views.ajouter_evenement, name='ajouter'),
    path('evenements/', views.get_evenements, name='evenements'),
]