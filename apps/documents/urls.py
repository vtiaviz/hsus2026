from django.urls import path

from apps.core.permissions import Action
from apps.core.views import AreaPlaceholderView

app_name = "documents"

urlpatterns = [
    path(
        "",
        AreaPlaceholderView.as_view(
            required_action=Action.FINISHED, title="Atendimentos finalizados", spec="006"
        ),
        name="finished",
    ),
]
