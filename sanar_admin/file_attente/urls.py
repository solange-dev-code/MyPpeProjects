from django.urls import path
from . import views

app_name = 'file_attente'

urlpatterns = [
    path('', views.liste_file_attente, name='liste'),
    path('<int:file_id>/<str:action>/', views.action_file, name='action'),
    path('recalculer/', views.recalculer, name='recalculer'),
]
