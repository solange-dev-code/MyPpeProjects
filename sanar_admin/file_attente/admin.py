from django.contrib import admin
from .models import FileAttente


@admin.register(FileAttente)
class FileAttenteAdmin(admin.ModelAdmin):
    list_display = (
        'patient', 'hopital', 'niveau_triage', 'statut',
        'temps_attente_estime', 'arrivee_at'
    )
    list_filter = ('statut', 'niveau_triage', 'hopital')
    search_fields = ('patient__nom', 'patient__prenom')
    readonly_fields = ('arrivee_at', 'consultation_at', 'fin_at')
    date_hierarchy = 'arrivee_at'
