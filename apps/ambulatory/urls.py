from django.urls import path

from apps.core.permissions import Action
from apps.core.views import AreaPlaceholderView

app_name = "ambulatory"

urlpatterns = [
    path(
        "procedures/",
        AreaPlaceholderView.as_view(
            required_action=Action.AMBULATORY_PROCEDURES,
            title="Procedimentos ambulatoriais",
            spec="003",
        ),
        name="procedures",
    ),
]
