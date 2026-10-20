from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import (
    Bed,
    Cbo,
    Cid10,
    DischargeReason,
    Establishment,
    Municipality,
    SigtapProcedure,
    User,
    Ward,
)


class ReadOnlyReferenceAdmin(admin.ModelAdmin):
    """Tabelas oficiais: só leitura, carregadas pelos comandos import_*."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Municipality)
class MunicipalityAdmin(ReadOnlyReferenceAdmin):
    list_display = ["ibge_code", "name", "state"]
    list_filter = ["state"]
    search_fields = ["ibge_code", "name"]


@admin.register(Cid10)
class Cid10Admin(ReadOnlyReferenceAdmin):
    list_display = ["code", "description"]
    search_fields = ["code", "description"]


@admin.register(SigtapProcedure)
class SigtapProcedureAdmin(ReadOnlyReferenceAdmin):
    list_display = ["code", "name", "competence"]
    search_fields = ["code", "name"]


@admin.register(Cbo)
class CboAdmin(ReadOnlyReferenceAdmin):
    list_display = ["code", "title"]
    search_fields = ["code", "title"]


@admin.register(DischargeReason)
class DischargeReasonAdmin(ReadOnlyReferenceAdmin):
    list_display = ["code", "description", "kind"]
    list_filter = ["kind"]


class BedInline(admin.TabularInline):
    model = Bed
    extra = 0


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ["name", "establishment", "is_active"]
    list_filter = ["establishment", "is_active"]
    inlines = [BedInline]


@admin.register(Establishment)
class EstablishmentAdmin(admin.ModelAdmin):
    list_display = ["name", "cnes", "municipality"]
    autocomplete_fields = ["municipality"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "full_name", "cbo", "is_active"]
    search_fields = ["username", "full_name", "cpf", "cns"]
    autocomplete_fields = ["cbo"]
    fieldsets = (
        *BaseUserAdmin.fieldsets,
        (
            _("Dados profissionais"),
            {"fields": ["full_name", "cpf", "cns", "cbo", "council_registry", "establishment"]},
        ),
    )
