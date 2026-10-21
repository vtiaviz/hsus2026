from django.urls import path

from apps.core.permissions import Action
from apps.core.views import AreaPlaceholderView

app_name = "infirmary"

urlpatterns = [
    path(
        "admission/",
        AreaPlaceholderView.as_view(required_action=Action.ADMISSION, title="Admissão", spec="004"),
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
