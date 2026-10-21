from django.contrib import admin

from .models import Patient, PatientAccessLog


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ["name", "medical_record_number", "cns", "cpf", "birth_date"]
    search_fields = ["name", "mother_name", "cns", "cpf", "medical_record_number"]
    readonly_fields = ["created_by", "created_at", "updated_at"]

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PatientAccessLog)
class PatientAccessLogAdmin(admin.ModelAdmin):
    list_display = ["accessed_at", "user", "patient", "view_name"]
    list_filter = ["view_name"]
    search_fields = ["patient__name", "user__username"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
