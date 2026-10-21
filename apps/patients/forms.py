from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.core.forms import digits_or_none

from .models import Patient


class PatientSearchForm(forms.Form):
    q = forms.CharField(label=_("CNS, CPF, prontuário ou nome"), max_length=100, required=False)
    mother = forms.CharField(label=_("Nome da mãe"), max_length=100, required=False)


class PatientForm(forms.ModelForm):
    # Aceitam máscara; o clean_* tira os separadores e o model valida os dígitos.
    cns = forms.CharField(label=_("CNS"), max_length=20, required=False)
    cpf = forms.CharField(label=_("CPF"), max_length=14, required=False)
    phone = forms.CharField(label=_("Telefone"), max_length=16)
    zipcode = forms.CharField(label=_("CEP"), max_length=9)

    class Meta:
        model = Patient
        fields = [
            "cns",
            "cpf",
            "medical_record_number",
            "name",
            "mother_name",
            "sex",
            "race",
            "birth_date",
            "phone",
            "street_type",
            "street",
            "number",
            "complement",
            "neighborhood",
            "zipcode",
            "municipality",
        ]
        widgets = {"birth_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.existing_patient = None
        self.fields["municipality"].queryset = self.fields["municipality"].queryset.order_by(
            "state", "name"
        )

    def clean_cns(self):
        return digits_or_none(self.cleaned_data["cns"])

    def clean_cpf(self):
        return digits_or_none(self.cleaned_data["cpf"])

    def clean_phone(self):
        return digits_or_none(self.cleaned_data["phone"]) or ""

    def clean_zipcode(self):
        return digits_or_none(self.cleaned_data["zipcode"]) or ""

    def clean_birth_date(self):
        birth_date = self.cleaned_data["birth_date"]
        if birth_date > date.today():
            raise forms.ValidationError(_("O nascimento não pode estar no futuro."))
        return birth_date

    def clean(self):
        cleaned = super().clean()
        if "cns" in cleaned and "cpf" in cleaned and not (cleaned["cns"] or cleaned["cpf"]):
            raise forms.ValidationError(_("Informe o CNS ou o CPF."))
        return cleaned

    def validate_unique(self):
        others = Patient.objects.exclude(pk=self.instance.pk)
        for field in ("cns", "cpf"):
            value = self.cleaned_data.get(field)
            existing = value and others.filter(**{field: value}).first()
            if existing:
                self.existing_patient = existing
                self.add_error(
                    field,
                    _("Já existe paciente com este %(field)s: %(name)s.")
                    % {"field": field.upper(), "name": existing.name},
                )
        # CNS e CPF já foram conferidos acima, com a mensagem que aponta o paciente existente.
        exclude = self._get_validation_exclusions() | {"cns", "cpf"}
        try:
            self.instance.validate_unique(exclude=exclude)
        except ValidationError as error:
            self._update_errors(error)
