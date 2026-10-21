from django.contrib.auth.decorators import login_not_required
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView

from .permissions import ActionRequiredMixin


@login_not_required
@require_GET
def health(request):
    """Usado pelo Docker Compose para saber se a aplicação e o banco respondem."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok"})


class HomeView(TemplateView):
    template_name = "core/home.html"


class AreaPlaceholderView(ActionRequiredMixin, TemplateView):
    """Página vazia de uma área; o conteúdo chega nas specs 002 a 006."""

    template_name = "core/area_placeholder.html"
    title = ""
    spec = ""

    def get_context_data(self, **kwargs):
        return super().get_context_data(title=self.title, spec=self.spec, **kwargs)
