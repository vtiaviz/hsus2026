"""Matriz de perfis × ações: a única fonte da verdade para views, barra lateral e testes."""

from functools import wraps

from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import PermissionDenied
from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.TextChoices):
    ADMIN = "admin", _("Administrador")
    ATTENDANT = "attendant", _("Atendente")
    NURSING_TECHNICIAN = "nursing_technician", _("Técnico de enfermagem")
    NURSE = "nurse", _("Enfermeiro")
    PHYSICIAN = "physician", _("Médico")


class Action(models.TextChoices):
    IDENTIFICATION = "identification", _("Entrada: identificação")
    TRIAGE = "triage", _("Entrada: triagem")
    CONSULTATION = "consultation", _("Entrada: consulta")
    AMBULATORY_PROCEDURES = "ambulatory_procedures", _("Ambulatório: procedimentos")
    ADMISSION = "admission", _("Enfermaria: admissão")
    NURSING_NOTE = "nursing_note", _("Enfermaria: evolução de enfermagem")
    MEDICAL_NOTE = "medical_note", _("Enfermaria: evolução médica e alta")
    FINISHED = "finished", _("Finalizados: ver e imprimir")
    ADMIN_PANEL = "admin_panel", _("Painel de administração")


ROLE_ACTIONS: dict[str, frozenset[str]] = {
    Role.ADMIN: frozenset(Action.values),
    Role.ATTENDANT: frozenset({Action.IDENTIFICATION, Action.FINISHED}),
    Role.NURSING_TECHNICIAN: frozenset(
        {Action.TRIAGE, Action.AMBULATORY_PROCEDURES, Action.NURSING_NOTE}
    ),
    Role.NURSE: frozenset(
        {Action.TRIAGE, Action.AMBULATORY_PROCEDURES, Action.ADMISSION, Action.NURSING_NOTE}
    ),
    Role.PHYSICIAN: frozenset(
        {
            Action.CONSULTATION,
            Action.AMBULATORY_PROCEDURES,
            Action.MEDICAL_NOTE,
            Action.FINISHED,
        }
    ),
}


def user_roles(user) -> set[str]:
    if not user.is_authenticated or not user.is_active:
        return set()
    return set(user.groups.filter(name__in=Role.values).values_list("name", flat=True))


def user_actions(user) -> frozenset[str]:
    if not user.is_authenticated or not user.is_active:
        return frozenset()
    if user.is_superuser:
        return frozenset(Action.values)
    actions = set()
    for role in user_roles(user):
        actions |= ROLE_ACTIONS[role]
    return frozenset(actions)


def user_can(user, action: str) -> bool:
    return action in user_actions(user)


def action_required(action: str):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not user_can(request.user, action):
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


class ActionRequiredMixin:
    required_action: str = ""

    def dispatch(self, request, *args, **kwargs):
        if not self.required_action or not user_can(request.user, self.required_action):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class RoleBackend(BaseBackend):
    """Dá ao perfil administrador todas as permissões de model, usadas pelo painel do Django."""

    def has_perm(self, user_obj, perm, obj=None):
        return user_can(user_obj, Action.ADMIN_PANEL)

    def has_module_perms(self, user_obj, app_label):
        return user_can(user_obj, Action.ADMIN_PANEL)
