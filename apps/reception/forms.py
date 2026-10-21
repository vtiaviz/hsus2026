from datetime import datetime

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.forms import Cid10Field

from .models import CareSession, Consultation, Triage
from .selectors import physicians


class CareSessionForm(forms.Form):
    arrival_date = forms.DateField(
        label=_("Data"), widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
    )
    arrival_time = forms.TimeField(
        label=_("Hora"), widget=forms.TimeInput(attrs={"type": "time"}, format="%H:%M")
    )
    complaint = forms.CharField(label=_("Relato"), max_length=250)
    origin = forms.ChoiceField(
        label=_("Origem"),
        choices=CareSession.Origin.choices,
        initial=CareSession.Origin.NEW,
        widget=forms.RadioSelect,
    )
    transfer_destination = forms.ChoiceField(
        label=_("Destino da transferência"),
        choices=CareSession.Destination.choices,
        required=False,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        now = timezone.localtime()
        self.fields["arrival_date"].initial = now.date()
        self.fields["arrival_time"].initial = now.time().replace(second=0, microsecond=0)

    def clean(self):
        cleaned = super().clean()
        if "arrival_date" in cleaned and "arrival_time" in cleaned:
            arrived_at = timezone.make_aware(
                datetime.combine(cleaned["arrival_date"], cleaned["arrival_time"])
            )
            if arrived_at > timezone.now():
                self.add_error("arrival_time", _("A chegada não pode estar no futuro."))
            cleaned["arrived_at"] = arrived_at
        if cleaned.get("origin") == CareSession.Origin.TRANSFER:
            if not cleaned.get("transfer_destination"):
                self.add_error("transfer_destination", _("Escolha o destino da transferência."))
        else:
            cleaned["transfer_destination"] = ""
        return cleaned

    @property
    def destination(self) -> str:
        return self.cleaned_data.get("transfer_destination", "")


class PhysicianChoiceMixin:
    def setup_physician(self, user):
        self.fields["physician"].queryset = physicians()
        self.fields["physician"].label_from_instance = lambda u: u.full_name or u.username
        if not self.is_bound and user in self.fields["physician"].queryset:
            self.fields["physician"].initial = user.pk


class TransferForm(PhysicianChoiceMixin, forms.ModelForm):
    """Dados da guia de transferência, exigidos pelo service conforme o destino."""

    cid10 = Cid10Field(required=False)

    class Meta:
        model = Consultation
        fields = ["physician", "cid10", "diagnosis", "care_plan"]
        widgets = {
            "diagnosis": forms.Textarea(attrs={"rows": 2}),
            "care_plan": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.fields:
            self.fields[name].required = False
        self.setup_physician(user)

    def _post_clean(self):
        # Os campos só são obrigatórios em alguns destinos; o service confere.
        pass


class TriageForm(forms.ModelForm):
    class Meta:
        model = Triage
        fields = [
            "systolic",
            "diastolic",
            "temperature",
            "heart_rate",
            "oxygen_saturation",
            "has_allergy",
            "allergy_description",
            "risk",
        ]
        widgets = {"risk": forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["risk"].choices = Triage.Risk.choices  # rádio sem a opção vazia

    def clean(self):
        cleaned = super().clean()
        systolic, diastolic = cleaned.get("systolic"), cleaned.get("diastolic")
        if systolic and diastolic and diastolic >= systolic:
            self.add_error("diastolic", _("A diastólica precisa ser menor que a sistólica."))
        if cleaned.get("has_allergy") and not cleaned.get("allergy_description"):
            self.add_error("allergy_description", _("Descreva a alergia."))
        return cleaned


class ConsultationForm(PhysicianChoiceMixin, forms.ModelForm):
    cid10 = Cid10Field()
    certificate_days = forms.IntegerField(
        label=_("Dias de afastamento"), min_value=1, max_value=365, required=False
    )
    certificate_with_cid = forms.BooleanField(
        label=_("Incluir o CID-10 no atestado"), required=False
    )

    class Meta:
        model = Consultation
        fields = ["physician", "cid10", "diagnosis", "care_plan", "referral"]
        widgets = {
            "diagnosis": forms.Textarea(attrs={"rows": 3}),
            "care_plan": forms.Textarea(attrs={"rows": 3}),
            "referral": forms.RadioSelect,
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["referral"].choices = Consultation.Referral.choices  # rádio sem a opção vazia
        self.setup_physician(user)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("certificate_days") and (
            cleaned.get("referral") != Consultation.Referral.DISCHARGE
        ):
            self.add_error("certificate_days", _("O atestado só é emitido na alta."))
        return cleaned

    @property
    def certificate_cid10(self):
        if self.cleaned_data.get("certificate_with_cid"):
            return self.cleaned_data["cid10"]
        return None
