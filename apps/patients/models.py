from datetime import date

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.core.models import Municipality, TimeStampedModel
from apps.core.validators import validate_cns, validate_cpf, validate_digits


class Sex(models.TextChoices):
    MALE = "M", _("Masculino")
    FEMALE = "F", _("Feminino")


class Race(models.TextChoices):
    """Raça/cor com os códigos do SUS."""

    WHITE = "01", _("Branca")
    BLACK = "02", _("Preta")
    BROWN = "03", _("Parda")
    YELLOW = "04", _("Amarela")
    INDIGENOUS = "05", _("Indígena")
    UNKNOWN = "99", _("Sem informação")


class Patient(TimeStampedModel):
    cns = models.CharField(
        _("CNS"), max_length=15, unique=True, null=True, blank=True, validators=[validate_cns]
    )
    cpf = models.CharField(
        _("CPF"), max_length=11, unique=True, null=True, blank=True, validators=[validate_cpf]
    )
    medical_record_number = models.CharField(
        _("prontuário"),
        max_length=15,
        unique=True,
        blank=True,
        validators=[validate_digits],
        help_text=_("Deixe em branco para o sistema gerar o próximo número."),
    )
    name = models.CharField(_("nome"), max_length=100)
    mother_name = models.CharField(_("nome da mãe"), max_length=100)
    sex = models.CharField(_("sexo"), max_length=1, choices=Sex.choices)
    race = models.CharField(_("raça/cor"), max_length=2, choices=Race.choices)
    birth_date = models.DateField(_("nascimento"))
    phone = models.CharField(_("telefone"), max_length=11, validators=[validate_digits])
    street_type = models.CharField(_("tipo de logradouro"), max_length=30)
    street = models.CharField(_("logradouro"), max_length=100)
    number = models.CharField(
        _("número"), max_length=10, blank=True, help_text=_("Em branco: sem número.")
    )
    complement = models.CharField(_("complemento"), max_length=60, blank=True)
    neighborhood = models.CharField(_("bairro"), max_length=60)
    zipcode = models.CharField(_("CEP"), max_length=8, validators=[validate_digits])
    municipality = models.ForeignKey(
        Municipality, on_delete=models.PROTECT, verbose_name=_("município de residência")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("cadastrado por"),
    )

    class Meta:
        verbose_name = _("paciente")
        verbose_name_plural = _("pacientes")
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(cns__isnull=False) | Q(cpf__isnull=False),
                name="patient_has_cns_or_cpf",
            )
        ]

    def __str__(self):
        return self.name

    def age(self, on: date | None = None) -> int:
        on = on or date.today()
        before_birthday = (on.month, on.day) < (self.birth_date.month, self.birth_date.day)
        return on.year - self.birth_date.year - before_birthday


class PatientAccessLog(models.Model):
    """Quem abriu o prontuário de qual paciente, e quando (constituição, princípio VI)."""

    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name="access_logs", verbose_name=_("paciente")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("usuário"),
    )
    care_session = models.ForeignKey(
        "reception.CareSession",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("atendimento"),
    )
    view_name = models.CharField(_("tela"), max_length=60)
    accessed_at = models.DateTimeField(_("acessado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("acesso a prontuário")
        verbose_name_plural = _("acessos a prontuário")
        ordering = ["-accessed_at"]

    def __str__(self):
        return f"{self.user} → {self.patient} ({self.view_name})"
