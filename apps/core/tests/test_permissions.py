import pytest
from django.contrib.auth.models import AnonymousUser, Group
from django.urls import reverse

from apps.core.navigation import SIDEBAR, sidebar_for
from apps.core.permissions import ROLE_ACTIONS, Action, Role, user_actions, user_can

from .factories import MODEL_BACKEND, UserFactory, user_with_roles

pytestmark = pytest.mark.django_db

# Matriz da spec 001, copiada aqui de propósito: se alguém mudar ROLE_ACTIONS sem mudar a spec,
# este teste falha.
SPEC_MATRIX = {
    Action.IDENTIFICATION: {Role.ADMIN, Role.ATTENDANT},
    Action.TRIAGE: {Role.ADMIN, Role.NURSING_TECHNICIAN, Role.NURSE},
    Action.CONSULTATION: {Role.ADMIN, Role.PHYSICIAN},
    Action.AMBULATORY_PROCEDURES: {Role.ADMIN, Role.NURSING_TECHNICIAN, Role.NURSE, Role.PHYSICIAN},
    Action.ADMISSION: {Role.ADMIN, Role.NURSE},
    Action.NURSING_NOTE: {Role.ADMIN, Role.NURSING_TECHNICIAN, Role.NURSE},
    Action.MEDICAL_NOTE: {Role.ADMIN, Role.PHYSICIAN},
    Action.FINISHED: {Role.ADMIN, Role.ATTENDANT, Role.PHYSICIAN},
    Action.ADMIN_PANEL: {Role.ADMIN},
}

ACTION_URLS = {item.action: item.url_name for section in SIDEBAR for item in section.items} | {
    Action.ADMIN_PANEL: "admin:index"
}

CELLS = [(role, action) for role in Role.values for action in Action.values]


def test_roles_exist_as_groups():
    assert set(Group.objects.values_list("name", flat=True)) >= set(Role.values)


def test_matrix_matches_spec():
    for action, roles in SPEC_MATRIX.items():
        assert {role for role, actions in ROLE_ACTIONS.items() if action in actions} == roles


def test_every_action_has_a_url():
    assert set(ACTION_URLS) == set(Action.values)


@pytest.mark.parametrize(("role", "action"), CELLS)
def test_matrix_cell_against_url(client, role, action):
    client.force_login(user_with_roles(role), backend=MODEL_BACKEND)
    response = client.get(reverse(ACTION_URLS[action]))
    if role in SPEC_MATRIX[action]:
        assert response.status_code == 200
    elif action == Action.ADMIN_PANEL:
        # O painel do Django manda quem não tem permissão para a própria tela de login dele.
        assert response.status_code == 302
        assert response.url.startswith(reverse("admin:login"))
    else:
        assert response.status_code == 403


def test_forbidden_page_is_in_portuguese(client):
    client.force_login(user_with_roles(Role.ATTENDANT), backend=MODEL_BACKEND)
    response = client.get(reverse("infirmary:medical_note"))
    assert response.status_code == 403
    assert "Acesso negado" in response.content.decode()


def test_multiple_roles_add_up():
    user = user_with_roles(Role.NURSE, Role.ATTENDANT)
    assert user_can(user, Action.ADMISSION)
    assert user_can(user, Action.IDENTIFICATION)
    assert not user_can(user, Action.MEDICAL_NOTE)


def test_superuser_without_role_can_do_everything():
    user = UserFactory(is_superuser=True)
    assert user_actions(user) == frozenset(Action.values)


def test_user_without_role_or_inactive_or_anonymous_has_nothing():
    assert user_actions(UserFactory()) == frozenset()
    assert user_actions(user_with_roles(Role.ADMIN, is_active=False)) == frozenset()
    assert user_actions(AnonymousUser()) == frozenset()


def test_sidebar_shows_only_permitted_items():
    sections = sidebar_for(user_with_roles(Role.ATTENDANT))
    labels = {str(section.label): [item.url_name for item in section.items] for section in sections}
    assert labels == {
        "Entrada": ["reception:identification"],
        "Finalizados": ["documents:finished"],
    }


def test_sidebar_rendered_for_physician(client):
    client.force_login(user_with_roles(Role.PHYSICIAN), backend=MODEL_BACKEND)
    html = client.get(reverse("core:home")).content.decode()
    assert reverse("infirmary:medical_note") in html
    assert reverse("infirmary:admission") not in html
    assert reverse("admin:index") not in html


def test_user_without_role_sees_warning(client):
    client.force_login(UserFactory(), backend=MODEL_BACKEND)
    html = client.get(reverse("core:home")).content.decode()
    assert "ainda não tem perfil" in html


def test_admin_role_can_use_admin_panel(client):
    client.force_login(user_with_roles(Role.ADMIN), backend=MODEL_BACKEND)
    assert client.get(reverse("admin:core_establishment_changelist")).status_code == 200
    html = client.get(reverse("core:home")).content.decode()
    assert "Administração" in html


def test_role_labels():
    user = user_with_roles(Role.PHYSICIAN, Role.NURSE)
    assert user.role_labels == ["Enfermeiro", "Médico"]


def test_action_required_decorator():
    from django.core.exceptions import PermissionDenied
    from django.http import HttpResponse
    from django.test import RequestFactory

    from apps.core.permissions import action_required, user_roles

    @action_required(Action.ADMISSION)
    def view(request):
        return HttpResponse("ok")

    request = RequestFactory().get("/")
    request.user = user_with_roles(Role.NURSE)
    assert view(request).status_code == 200
    request.user = user_with_roles(Role.PHYSICIAN)
    with pytest.raises(PermissionDenied):
        view(request)
    assert user_roles(AnonymousUser()) == set()
