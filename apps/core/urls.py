from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "core"

urlpatterns = [
    path("health/", views.health, name="health"),
    path("", TemplateView.as_view(template_name="core/home.html"), name="home"),
]
