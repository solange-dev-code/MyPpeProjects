from django.contrib import admin
from .models import Personnel

@admin.register(Personnel)
class PersonnelAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "hopital", "telephone", "date_creation")
    list_filter = ("role", "hopital")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")