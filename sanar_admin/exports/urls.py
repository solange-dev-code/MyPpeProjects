from django.urls import path
from . import views

app_name = 'exports'

urlpatterns = [
    path('dossier-pdf/<int:patient_pk>/', views.export_pdf, name='dossier_pdf'),
    path('patients.csv', views.export_csv, name='patients_csv'),
    path('dossier-fhir/<int:patient_pk>/', views.export_fhir, name='dossier_fhir'),
]
