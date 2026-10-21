from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from apps.core.permissions import Action, user_can

admin.site.site_header = "H-SUS · Administração"
admin.site.site_title = "H-SUS"
admin.site.has_permission = lambda request: user_can(request.user, Action.ADMIN_PANEL)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("reception/", include("apps.reception.urls")),
    path("ambulatory/", include("apps.ambulatory.urls")),
    path("infirmary/", include("apps.infirmary.urls")),
    path("finished/", include("apps.documents.urls")),
    path("", include("apps.core.urls")),
]
