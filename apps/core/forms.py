from django import forms
from django.forms.renderers import DjangoTemplates
from django.utils.translation import gettext_lazy as _

from .models import Cid10


class Cid10Field(forms.Field):
    """Recebe o código digitado (J18.9 ou J189) e devolve o registro da tabela importada."""

    default_error_messages = {"not_found": _("CID-10 não encontrado na tabela importada.")}

    def __init__(self, **kwargs):
        kwargs.setdefault("label", _("CID-10"))
        kwargs.setdefault("widget", forms.TextInput(attrs={"placeholder": "J18.9", "maxlength": 6}))
        super().__init__(**kwargs)

    def prepare_value(self, value):
        if isinstance(value, Cid10):
            return value.formatted_code
        if isinstance(value, str) and value and not any(c in value for c in ". "):
            cid = Cid10.objects.filter(pk=value).first()
            return cid.formatted_code if cid else value
        return value

    def to_python(self, value):
        code = str(value or "").replace(".", "").replace(" ", "").upper()
        if code in self.empty_values:
            return None
        cid = Cid10.objects.filter(pk=code).first()
        if cid is None:
            raise forms.ValidationError(self.error_messages["not_found"], code="not_found")
        return cid


def digits_or_none(value: str | None) -> str | None:
    """Remove máscara; vazio vira None para não colidir na chave única."""
    digits = "".join(ch for ch in value or "" if ch.isdigit())
    return digits or None


class BootstrapFormRenderer(DjangoTemplates):
    """`{{ form.campo.as_field_group }}` sai com rótulo, widget e erros no padrão do Bootstrap."""

    field_template_name = "forms/field.html"
