from django.contrib import admin

from .models import ExamType, Medication


@admin.register(Medication, ExamType)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]

    def has_delete_permission(self, request, obj=None):
        # Itens já usados em prescrições não podem sumir; desative em vez de apagar.
        return False
