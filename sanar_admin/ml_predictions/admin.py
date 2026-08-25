from django.contrib import admin
from .models import MLModel, MLPrediction


@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = ('nom', 'version', 'date_entrainement', 'precision',
                    'rappel', 'auc', 'est_actif')
    list_filter = ('est_actif',)
    readonly_fields = ('date_entrainement',)


@admin.register(MLPrediction)
class MLPredictionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'score_risque', 'niveau_risque',
                    'modele', 'created_at')
    list_filter = ('niveau_risque', 'created_at')
    readonly_fields = ('created_at', 'niveau_risque')
    date_hierarchy = 'created_at'
