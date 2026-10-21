from django import forms

from .models import ExamRequest, ExamType, Medication, PrescribedMedication


class PrescribedMedicationForm(forms.ModelForm):
    class Meta:
        model = PrescribedMedication
        fields = [
            "medication",
            "dosage",
            "form",
            "route",
            "times",
            "interval_hours",
            "duration",
            "duration_unit",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["medication"].queryset = Medication.objects.filter(is_active=True)


class ExamRequestForm(forms.ModelForm):
    class Meta:
        model = ExamRequest
        fields = ["exam_type", "external_id"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["exam_type"].queryset = ExamType.objects.filter(is_active=True)


MedicationFormSet = forms.formset_factory(PrescribedMedicationForm, extra=1)
ExamRequestFormSet = forms.formset_factory(ExamRequestForm, extra=1)


def unsaved_items(formset) -> list:
    """Linhas preenchidas do formset, ainda sem gravar (o service grava)."""
    return [form.save(commit=False) for form in formset.forms if form.has_changed()]
