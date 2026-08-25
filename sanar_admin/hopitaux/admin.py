from django.contrib import admin
from .models import Hopital

@admin.register(Hopital)
class HopitalAdmin(admin.ModelAdmin):
    list_display = ("nom", "ville", "telephone", "actif", "date_creation")
    list_filter = ("ville", "actif")
    search_fields = ("nom", "ville", "adresse")