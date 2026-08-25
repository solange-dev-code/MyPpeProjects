"""Admin Django pour le module urgences."""
from django.contrib import admin
from .models import DemandeUrgence, AccesUrgence


@admin.register(DemandeUrgence)
class DemandeUrgenceAdmin(admin.ModelAdmin):
    list_display = (
        'uuid', 'patient', 'niveau', 'statut', 'hopital_destine',
        'temps_reponse', 'created_at'
    )
    list_filter = ('niveau', 'statut', 'created_at')
    search_fields = ('patient__nom', 'patient__prenom', 'uuid')
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'temps_reponse')
    date_hierarchy = 'created_at'


@admin.register(AccesUrgence)
class AccesUrgenceAdmin(admin.ModelAdmin):
    list_display = ('patient', 'source_ip', 'created_at', 'user_agent')
    list_filter = ('created_at',)
    search_fields = ('patient__nom', 'source_ip')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
