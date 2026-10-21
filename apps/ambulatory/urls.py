from django.urls import path
from django.utils.translation import gettext_lazy as _

from apps.core.permissions import Action
from apps.reception.models import CareSession
from apps.reception.views import StatusQueueView

app_name = "ambulatory"

urlpatterns = [
    # Por enquanto só a fila; o registro de procedimentos vem na spec 003.
    path(
        "procedures/",
        StatusQueueView.as_view(
            required_action=Action.AMBULATORY_PROCEDURES,
            title=_("Fila do ambulatório"),
            status=CareSession.Status.AMBULATORY,
            empty_message=_("O registro de procedimentos chega na spec 003."),
        ),
        name="procedures",
    ),
]
