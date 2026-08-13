from django.contrib import admin
from .models import Teleconsultation, WebRTCSignaling


@admin.register(Teleconsultation)
class TeleconsultationAdmin(admin.ModelAdmin):
    list_display = ('room_uuid', 'patient', 'medecin', 'statut',
                    'date_planifiee', 'duree_secondes')
    list_filter = ('statut', 'date_planifiee')
    search_fields = ('room_uuid', 'patient__nom', 'medecin__nom')
    readonly_fields = ('room_uuid', 'created_at', 'date_debut', 'date_fin',
                       'duree_secondes')


@admin.register(WebRTCSignaling)
class WebRTCSignalingAdmin(admin.ModelAdmin):
    list_display = ('teleconsultation', 'expediteur', 'type_message', 'created_at')
    list_filter = ('type_message', 'created_at')
    readonly_fields = ('created_at',)
