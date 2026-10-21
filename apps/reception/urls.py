from django.urls import path

from apps.core.permissions import Action
from apps.core.views import AreaPlaceholderView

app_name = "reception"

urlpatterns = [
    path(
        "identification/",
        AreaPlaceholderView.as_view(
            required_action=Action.IDENTIFICATION, title="Identificação", spec="002"
        ),
        name="identification",
    ),
    path(
        "triage/",
        AreaPlaceholderView.as_view(required_action=Action.TRIAGE, title="Triagem", spec="002"),
        name="triage",
    ),
    path(
        "consultation/",
        AreaPlaceholderView.as_view(
            required_action=Action.CONSULTATION, title="Consulta", spec="002"
        ),
        name="consultation",
    ),
]
