import pytest
from axes.models import AccessAttempt
from django.conf import settings
from django.urls import reverse

from apps.core.permissions import Role

from .factories import MODEL_BACKEND, user_with_roles

pytestmark = pytest.mark.django_db

PASSWORD = "senha-de-teste-123"


def login(client, username, password=PASSWORD, next_url=None):
    url = reverse("login") + (f"?next={next_url}" if next_url else "")
    data = {"username": username, "password": password}
    if next_url:
        data["next"] = next_url
    return client.post(url, data)


def test_login_redirects_home(client):
    user_with_roles(Role.ATTENDANT, username="maria")
    response = login(client, "maria")
    assert response.status_code == 302
    assert response.url == reverse("core:home")


def test_login_is_case_insensitive(client):
    user_with_roles(Role.ATTENDANT, username="maria")
    assert login(client, "MARIA").status_code == 302


def test_username_unique_ignoring_case():
    from django.db import IntegrityError

    user_with_roles(username="joao")
    with pytest.raises(IntegrityError):
        user_with_roles(username="JOAO")


def test_wrong_password_and_inactive_get_same_message(client):
    user_with_roles(Role.ATTENDANT, username="ana")
    user_with_roles(Role.ATTENDANT, username="inativo", is_active=False)
    wrong = login(client, "ana", "errada")
    inactive = login(client, "inativo")
    for response in (wrong, inactive):
        assert response.status_code == 200
        assert "Usuário ou senha incorretos" in response.content.decode()


def test_anonymous_is_sent_to_login_and_back(client):
    target = reverse("reception:identification")
    response = client.get(target)
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))
    user_with_roles(Role.ATTENDANT, username="maria")
    response = login(client, "maria", next_url=target)
    assert response.url == target


def test_health_is_public(client):
    assert client.get(reverse("core:health")).status_code == 200


def test_logout_ends_session(client):
    client.force_login(user_with_roles(Role.ATTENDANT), backend=MODEL_BACKEND)
    response = client.post(reverse("logout"))
    assert response.status_code == 302
    assert client.get(reverse("core:home")).status_code == 302


def test_session_expires_after_30_minutes_idle():
    assert settings.SESSION_COOKIE_AGE == 30 * 60
    assert settings.SESSION_SAVE_EVERY_REQUEST is True


def test_lockout_after_five_failures_and_admin_unlock(client):
    user_with_roles(Role.ATTENDANT, username="pedro")
    for _ in range(5):
        login(client, "Pedro", "errada")
    locked = login(client, "pedro")
    assert locked.status_code == 429
    assert "Acesso bloqueado" in locked.content.decode()

    AccessAttempt.objects.all().delete()  # o que o admin faz ao desbloquear
    assert login(client, "pedro").status_code == 302


def test_success_resets_failures(client):
    user_with_roles(Role.ATTENDANT, username="rita")
    for _ in range(4):
        login(client, "rita", "errada")
    assert login(client, "rita").status_code == 302
    client.post(reverse("logout"))
    for _ in range(4):
        login(client, "rita", "errada")
    assert login(client, "rita").status_code == 302
