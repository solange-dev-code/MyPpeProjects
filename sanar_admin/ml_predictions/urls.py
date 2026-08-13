from django.urls import path
from . import views

app_name = 'ml_predictions'

urlpatterns = [
    path('prediction-courante/', views.prediction_courante, name='prediction_courante'),
    path('entrainer/', views.entrainer_modele_view, name='entrainer'),
    path('modeles/', views.liste_modeles, name='modeles'),
]
