import pytest
from django.contrib.admin.sites import site
from django.core.management import CommandError, call_command
from django.test import RequestFactory
from django.urls import reverse

from apps.core.models import Cid10
from config.settings.base import BASE_DIR

pytestmark = pytest.mark.django_db


def test_import_command_reports_total(capsys):
    call_command("import_discharge_reasons", str(BASE_DIR / "data" / "motivos_saida_sih.csv"))
    assert "26 registros importados" in capsys.readouterr().out


def test_import_command_missing_file():
    with pytest.raises(CommandError, match="não encontrado"):
        call_command("import_cid10", "/nao/existe.csv")


def test_import_command_format_error(tmp_path):
    path = tmp_path / "x.csv"
    path.write_text("FOO;BAR\n1;2\n")
    with pytest.raises(CommandError, match="Coluna obrigatória"):
        call_command("import_cid10", str(path))


def test_health_check(client):
    response = client.get(reverse("core:health"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_renders(client):
    response = client.get(reverse("core:home"))
    assert response.status_code == 200
    assert "H-SUS" in response.content.decode()


def test_reference_tables_are_read_only_in_admin(admin_user):
    request = RequestFactory().get("/")
    request.user = admin_user
    model_admin = site._registry[Cid10]
    assert not model_admin.has_add_permission(request)
    assert not model_admin.has_change_permission(request)
    assert not model_admin.has_delete_permission(request)


@pytest.mark.parametrize(
    "command", ["import_cid10", "import_sigtap", "import_cbo", "import_municipalities"]
)
def test_every_import_command_validates_path(command):
    with pytest.raises(CommandError):
        call_command(command, "/nao/existe")
