"""URLs API pour la téléconsultation."""
from django.urls import path
from . import views

app_name = 'teleconsultation'

urlpatterns = [
    path('', views.creer_teleconsultation, name='creer'),
    path('mes-teleconsultations/', views.mes_teleconsultations, name='mes'),
    path('<uuid:room_uuid>/demarrer/', views.demarrer_teleconsultation, name='demarrer'),
    path('<uuid:room_uuid>/terminer/', views.terminer_teleconsultation, name='terminer'),
]
