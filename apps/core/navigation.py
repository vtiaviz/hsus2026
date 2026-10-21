from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from .permissions import Action, user_actions


@dataclass(frozen=True)
class NavItem:
    label: str
    url_name: str
    action: str


@dataclass(frozen=True)
class NavSection:
    label: str
    items: tuple[NavItem, ...]


SIDEBAR = (
    NavSection(
        _("Entrada"),
        (
            NavItem(_("Identificação"), "reception:identification", Action.IDENTIFICATION),
            NavItem(_("Triagem"), "reception:triage", Action.TRIAGE),
            NavItem(_("Consulta"), "reception:consultation", Action.CONSULTATION),
        ),
    ),
    NavSection(
        _("Ambulatório"),
        (NavItem(_("Procedimentos"), "ambulatory:procedures", Action.AMBULATORY_PROCEDURES),),
    ),
    NavSection(
        _("Enfermaria"),
        (
            NavItem(_("Admissão"), "infirmary:admission", Action.ADMISSION),
            NavItem(_("Evolução de enfermagem"), "infirmary:nursing_note", Action.NURSING_NOTE),
            NavItem(_("Evolução médica"), "infirmary:medical_note", Action.MEDICAL_NOTE),
        ),
    ),
    NavSection(
        _("Finalizados"),
        (NavItem(_("Atendimentos finalizados"), "documents:finished", Action.FINISHED),),
    ),
)


def sidebar_for(user) -> list[NavSection]:
    actions = user_actions(user)
    sections = []
    for section in SIDEBAR:
        items = tuple(item for item in section.items if item.action in actions)
        if items:
            sections.append(NavSection(section.label, items))
    return sections


def sidebar(request):
    """Context processor da barra lateral."""
    user = request.user
    return {
        "sidebar_sections": sidebar_for(user),
        "can_admin_panel": Action.ADMIN_PANEL in user_actions(user),
    }
