from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from apps.clinical.forms import ExamRequestFormSet, MedicationFormSet, unsaved_items
from apps.core.permissions import Action, ActionRequiredMixin
from apps.patients.forms import PatientForm, PatientSearchForm
from apps.patients.models import Patient
from apps.patients.selectors import search_patients
from apps.patients.services import DuplicatePatientError, log_access, save_patient

from . import selectors, services
from .forms import (
    CareSessionForm,
    ConsultationForm,
    TransferForm,
    TriageForm,
)
from .models import CareSession, Consultation

Status = CareSession.Status


# Identificação


class IdentificationView(ActionRequiredMixin, TemplateView):
    required_action = Action.IDENTIFICATION
    template_name = "reception/identification.html"

    def get_context_data(self, **kwargs):
        form = PatientSearchForm(self.request.GET or None)
        results = None
        if form.is_valid() and (form.cleaned_data["q"] or form.cleaned_data["mother"]):
            results = search_patients(form.cleaned_data["q"], form.cleaned_data["mother"])
        return super().get_context_data(form=form, results=results, **kwargs)


class OpenCareSessionView(ActionRequiredMixin, View):
    """Cadastro (ou confirmação) do paciente e abertura do atendimento numa tela só."""

    required_action = Action.IDENTIFICATION
    template_name = "reception/open_session.html"

    def dispatch(self, request, *args, **kwargs):
        patient_pk = kwargs.get("patient_pk")
        self.patient = get_object_or_404(Patient, pk=patient_pk) if patient_pk else None
        return super().dispatch(request, *args, **kwargs)

    def build_forms(self, data=None):
        return {
            "patient_form": PatientForm(data, instance=self.patient, prefix="patient"),
            "session_form": CareSessionForm(data, prefix="session"),
            "transfer_form": TransferForm(data, prefix="transfer", user=self.request.user),
            "medication_formset": MedicationFormSet(data, prefix="medications"),
            "exam_formset": ExamRequestFormSet(data, prefix="exams"),
        }

    def render(self, forms, status=200):
        context = {
            **forms,
            "patient": self.patient,
            "open_session": self.patient and services.open_session_of(self.patient),
        }
        return render(self.request, self.template_name, context, status=status)

    def get(self, request, *args, **kwargs):
        return self.render(self.build_forms())

    def post(self, request, *args, **kwargs):
        forms = self.build_forms(request.POST)
        if not all(form.is_valid() for form in forms.values()):
            return self.render(forms)
        try:
            with transaction.atomic():
                care_session = self.save(forms)
        except (services.CareSessionError, DuplicatePatientError) as error:
            forms["session_form"].add_error(None, str(error))
            return self.render(forms)
        messages.success(request, _("Atendimento aberto."))
        return redirect("reception:session_detail", pk=care_session.pk)

    def save(self, forms) -> CareSession:
        patient = save_patient(forms["patient_form"].save(commit=False), self.request.user)
        return services.open_care_session(
            patient=patient,
            user=self.request.user,
            origin=forms["session_form"].cleaned_data["origin"],
            destination=forms["session_form"].destination,
            arrived_at=forms["session_form"].cleaned_data["arrived_at"],
            complaint=forms["session_form"].cleaned_data["complaint"],
            transfer=self.transfer_data(forms),
        )

    def transfer_data(self, forms) -> services.TransferData:
        transfer = forms["transfer_form"].cleaned_data
        destination = forms["session_form"].destination
        Destination = CareSession.Destination
        with_guide = destination in (Destination.AMBULATORY, Destination.INFIRMARY)
        return services.TransferData(
            physician=transfer.get("physician"),
            cid10=transfer.get("cid10"),
            diagnosis=transfer.get("diagnosis", ""),
            care_plan=transfer.get("care_plan", ""),
            medications=unsaved_items(forms["medication_formset"]) if with_guide else [],
            exams=unsaved_items(forms["exam_formset"])
            if with_guide or destination == Destination.DIAGNOSTIC_EXAM
            else [],
        )


class CareSessionDetailView(ActionRequiredMixin, DetailView):
    required_action = Action.IDENTIFICATION
    model = CareSession
    template_name = "reception/session_detail.html"
    context_object_name = "care_session"

    def get_queryset(self):
        return CareSession.objects.select_related("patient", "consultation")

    def get_context_data(self, **kwargs):
        return super().get_context_data(labsus_url=settings.LABSUS_URL, **kwargs)


# Filas


class StatusQueueView(ActionRequiredMixin, ListView):
    """Fila genérica de atendimentos num status; usada também pelo Ambulatório e pela Enfermaria."""

    template_name = "reception/queue.html"
    context_object_name = "sessions"
    title = ""
    status = ""
    detail_url_name = ""
    empty_message = ""

    def get_queryset(self):
        return selectors.sessions_with_status(self.status)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            title=self.title,
            detail_url_name=self.detail_url_name,
            empty_message=self.empty_message,
            **kwargs,
        )


class TriageQueueView(StatusQueueView):
    required_action = Action.TRIAGE
    title = _("Triagem")
    detail_url_name = "reception:triage_form"

    def get_queryset(self):
        return selectors.triage_queue()


class ConsultationQueueView(StatusQueueView):
    required_action = Action.CONSULTATION
    title = _("Consulta")
    detail_url_name = "reception:consultation_form"

    def get_queryset(self):
        return selectors.consultation_queue()


# Etapas do atendimento


class CareSessionStepView(ActionRequiredMixin, View):
    """Base da triagem e da consulta: confere o status antes de mostrar o formulário."""

    expected_status = ""
    queue_url_name = ""
    template_name = ""
    view_label = ""

    def dispatch(self, request, *args, **kwargs):
        self.care_session = get_object_or_404(
            CareSession.objects.select_related("patient"), pk=kwargs["pk"]
        )
        return super().dispatch(request, *args, **kwargs)

    def check_status(self):
        try:
            services.ensure_status(self.care_session, self.expected_status)
        except services.CareSessionError as error:
            messages.error(self.request, str(error))
            return redirect(self.queue_url_name)
        return None

    def render(self, context):
        context = {
            "care_session": self.care_session,
            "patient": self.care_session.patient,
            **context,
        }
        return render(self.request, self.template_name, context)

    def get(self, request, *args, **kwargs):
        refused = self.check_status()
        if refused:
            return refused
        log_access(
            user=request.user,
            patient=self.care_session.patient,
            care_session=self.care_session,
            view_name=self.view_label,
        )
        return self.render(self.build_forms())

    def post(self, request, *args, **kwargs):
        refused = self.check_status()
        if refused:
            return refused
        forms = self.build_forms(request.POST)
        if not all(form.is_valid() for form in forms.values()):
            return self.render(forms)
        try:
            self.save(forms)
        except services.CareSessionError as error:
            messages.error(request, str(error))
            return redirect(self.queue_url_name)
        return self.success()


class TriageView(CareSessionStepView):
    required_action = Action.TRIAGE
    expected_status = Status.AWAITING_TRIAGE
    queue_url_name = "reception:triage"
    template_name = "reception/triage.html"
    view_label = "triage"

    def build_forms(self, data=None):
        return {"form": TriageForm(data)}

    def save(self, forms):
        services.record_triage(
            self.care_session, forms["form"].save(commit=False), self.request.user
        )

    def success(self):
        messages.success(
            self.request, _("Triagem registrada. O paciente está na fila da consulta.")
        )
        return redirect(self.queue_url_name)


class ConsultationView(CareSessionStepView):
    required_action = Action.CONSULTATION
    expected_status = Status.AWAITING_CONSULTATION
    queue_url_name = "reception:consultation"
    template_name = "reception/consultation.html"
    view_label = "consultation"

    def build_forms(self, data=None):
        return {
            "form": ConsultationForm(data, user=self.request.user),
            "medication_formset": MedicationFormSet(data, prefix="medications"),
            "exam_formset": ExamRequestFormSet(data, prefix="exams"),
        }

    def render(self, context):
        return super().render({"triage": getattr(self.care_session, "triage", None), **context})

    def save(self, forms):
        form = forms["form"]
        self.consultation = services.record_consultation(
            self.care_session,
            form.save(commit=False),
            self.request.user,
            medications=unsaved_items(forms["medication_formset"]),
            exams=unsaved_items(forms["exam_formset"]),
            certificate_days=form.cleaned_data.get("certificate_days"),
            certificate_cid10=form.certificate_cid10,
        )

    def success(self):
        if self.consultation.referral == Consultation.Referral.DISCHARGE:
            messages.success(self.request, _("Alta registrada. Imprima a receita e o atestado."))
            return redirect("reception:discharge", pk=self.care_session.pk)
        messages.success(self.request, _("Consulta registrada e paciente encaminhado."))
        return redirect(self.queue_url_name)


# Encerramento: receita e atestado


class DischargedSessionMixin(ActionRequiredMixin):
    required_action = Action.CONSULTATION

    def get_care_session(self) -> CareSession:
        care_session = get_object_or_404(
            CareSession.objects.select_related("patient", "consultation__physician"),
            pk=self.kwargs["pk"],
        )
        consultation = getattr(care_session, "consultation", None)
        if not (
            care_session.is_finished
            and consultation
            and consultation.referral == Consultation.Referral.DISCHARGE
        ):
            raise Http404(_("Este atendimento não teve alta na consulta."))
        return care_session


class DischargeView(DischargedSessionMixin, TemplateView):
    template_name = "reception/discharge.html"

    def get_context_data(self, **kwargs):
        care_session = self.get_care_session()
        return super().get_context_data(
            care_session=care_session,
            has_prescription=care_session.prescribed_medications.exists(),
            certificate=getattr(care_session, "certificate", None),
            **kwargs,
        )


class PrescriptionPrintView(DischargedSessionMixin, TemplateView):
    template_name = "reception/print_prescription.html"

    def get_context_data(self, **kwargs):
        care_session = self.get_care_session()
        medications = care_session.prescribed_medications.select_related("medication")
        if not medications:
            raise Http404(_("Nenhum medicamento prescrito."))
        return super().get_context_data(
            care_session=care_session,
            patient=care_session.patient,
            physician=care_session.consultation.physician,
            medications=medications,
            **kwargs,
        )


class CertificatePrintView(DischargedSessionMixin, TemplateView):
    template_name = "reception/print_certificate.html"

    def get_context_data(self, **kwargs):
        care_session = self.get_care_session()
        certificate = getattr(care_session, "certificate", None)
        if certificate is None:
            raise Http404(_("Nenhum atestado emitido."))
        return super().get_context_data(
            care_session=care_session,
            patient=care_session.patient,
            certificate=certificate,
            **kwargs,
        )
