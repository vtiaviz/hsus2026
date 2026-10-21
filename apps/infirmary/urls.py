from django.urls import path
from django.utils.translation import gettext_lazy as _

from apps.core.permissions import Action
from apps.core.views import AreaPlaceholderView
from apps.reception.models import CareSession
from apps.reception.views import StatusQueueView

app_name = "infirmary"

urlpatterns = [
    path(
        "admission/",
        StatusQueueView.as_view(
            required_action=Action.ADMISSION,
            title=_("Fila de admissão"),
            status=CareSession.Status.AWAITING_ADMISSION,
            empty_message=_("O formulário de admissão chega na spec 004."),
        ),
        name="admission",
    ),
    path(
        "nursing-notes/",
        AreaPlaceholderView.as_view(
            required_action=Action.NURSING_NOTE, title="Evolução de enfermagem", spec="005"
        ),
        name="nursing_note",
    ),
    path(
        "medical-notes/",
        AreaPlaceholderView.as_view(
            required_action=Action.MEDICAL_NOTE, title="Evolução médica", spec="005"
        ),
        name="medical_note",
    ),
]
