from django.urls import path

from . import views

app_name = "reception"

urlpatterns = [
    path("identification/", views.IdentificationView.as_view(), name="identification"),
    path("identification/new/", views.OpenCareSessionView.as_view(), name="open_session_new"),
    path(
        "identification/patients/<int:patient_pk>/",
        views.OpenCareSessionView.as_view(),
        name="open_session",
    ),
    path("sessions/<int:pk>/", views.CareSessionDetailView.as_view(), name="session_detail"),
    path("triage/", views.TriageQueueView.as_view(), name="triage"),
    path("triage/<int:pk>/", views.TriageView.as_view(), name="triage_form"),
    path("consultation/", views.ConsultationQueueView.as_view(), name="consultation"),
    path("consultation/<int:pk>/", views.ConsultationView.as_view(), name="consultation_form"),
    path("sessions/<int:pk>/discharge/", views.DischargeView.as_view(), name="discharge"),
    path(
        "sessions/<int:pk>/prescription/",
        views.PrescriptionPrintView.as_view(),
        name="print_prescription",
    ),
    path(
        "sessions/<int:pk>/certificate/",
        views.CertificatePrintView.as_view(),
        name="print_certificate",
    ),
]
