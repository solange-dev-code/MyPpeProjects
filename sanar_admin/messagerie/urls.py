from django.urls import path
from . import views

app_name = 'messagerie'

urlpatterns = [
    path('', views.liste_messages, name='liste'),
    path('<int:pk>/', views.conversation, name='conversation'),
    path('envoyer/<int:pk>/', views.envoyer_message, name='envoyer'),
    path('nouvelle/', views.nouvelle_conversation, name='nouvelle'),
]