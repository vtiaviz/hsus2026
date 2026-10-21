from django.contrib import admin

from .models import CareSession


@admin.register(CareSession)
class CareSessionAdmin(admin.ModelAdmin):
    """Só consulta: o atendimento muda apenas pelas telas, que passam pelo service."""

    list_display = ["pk", "patient", "origin", "status", "arrived_at", "finished_at"]
    list_filter = ["status", "origin"]
    search_fields = ["patient__name", "patient__cns", "patient__cpf"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
