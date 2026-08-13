from django.urls import path
from . import views

app_name = 'users_app'

urlpatterns = [
    path('', views.liste_users, name='liste'),
    path('ajouter/', views.ajouter_user, name='ajouter'),
    path('<int:pk>/modifier/', views.modifier_user, name='modifier'),
    path('<int:pk>/supprimer/', views.supprimer_user, name='supprimer'),
]