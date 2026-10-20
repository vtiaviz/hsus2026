from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .validators import validate_cns, validate_cpf, validate_digits


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        abstract = True


# Tabelas de referência oficiais. São carregadas pelos comandos import_*,
# nunca editadas pela interface.


class Municipality(models.Model):
    ibge_code = models.CharField(
        _("código IBGE"), max_length=7, primary_key=True, validators=[validate_digits]
    )
    name = models.CharField(_("nome"), max_length=100)
    state = models.CharField(_("UF"), max_length=2)

    class Meta:
        verbose_name = _("município")
        verbose_name_plural = _("municípios")
        ordering = ["state", "name"]

    def __str__(self):
        return f"{self.name}/{self.state}"

    @property
    def sus_code(self) -> str:
        """O SUS usa o código IBGE de 6 dígitos (sem o dígito verificador)."""
        return self.ibge_code[:6]


class Cid10(models.Model):
    code = models.CharField(_("código"), max_length=4, primary_key=True)
    description = models.CharField(_("descrição"), max_length=255)

    class Meta:
        verbose_name = _("CID-10")
        verbose_name_plural = _("CID-10")
        ordering = ["code"]

    def __str__(self):
        return f"{self.formatted_code} - {self.description}"

    @property
    def formatted_code(self) -> str:
        return f"{self.code[:3]}.{self.code[3:]}" if len(self.code) == 4 else self.code


class SigtapProcedure(models.Model):
    code = models.CharField(
        _("código"), max_length=10, primary_key=True, validators=[validate_digits]
    )
    name = models.CharField(_("nome"), max_length=250)
    competence = models.CharField(_("competência"), max_length=6, help_text=_("AAAAMM"))

    class Meta:
        verbose_name = _("procedimento SIGTAP")
        verbose_name_plural = _("procedimentos SIGTAP")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Cbo(models.Model):
    code = models.CharField(
        _("código"), max_length=6, primary_key=True, validators=[validate_digits]
    )
    title = models.CharField(_("título"), max_length=255)

    class Meta:
        verbose_name = _("ocupação (CBO)")
        verbose_name_plural = _("ocupações (CBO)")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.title}"


class DischargeReason(models.Model):
    class Kind(models.TextChoices):
        DISCHARGE = "discharge", _("Alta")
        STAY = "stay", _("Permanência")
        TRANSFER = "transfer", _("Transferência")
        DEATH = "death", _("Óbito")
        ADMINISTRATIVE = "administrative", _("Encerramento administrativo")
        CHILDBIRTH = "childbirth", _("Parto")

    code = models.CharField(
        _("código"), max_length=2, primary_key=True, validators=[validate_digits]
    )
    description = models.CharField(_("descrição"), max_length=150)
    kind = models.CharField(_("tipo"), max_length=20, choices=Kind.choices)

    class Meta:
        verbose_name = _("motivo de saída/permanência")
        verbose_name_plural = _("motivos de saída/permanência")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.description}"

    @property
    def ends_care(self) -> bool:
        return self.kind != self.Kind.STAY


# Estabelecimento e estrutura física


class Establishment(TimeStampedModel):
    name = models.CharField(_("nome"), max_length=150)
    cnes = models.CharField(_("CNES"), max_length=7, unique=True, validators=[validate_digits])
    municipality = models.ForeignKey(
        Municipality, on_delete=models.PROTECT, verbose_name=_("município")
    )
    issuing_body = models.CharField(
        _("órgão emissor da AIH"), max_length=10, blank=True, help_text=_("Ex.: M150175801")
    )

    class Meta:
        verbose_name = _("estabelecimento")
        verbose_name_plural = _("estabelecimentos")

    def __str__(self):
        return f"{self.name} (CNES {self.cnes})"


class Ward(TimeStampedModel):
    establishment = models.ForeignKey(
        Establishment,
        on_delete=models.PROTECT,
        related_name="wards",
        verbose_name=_("estabelecimento"),
    )
    name = models.CharField(_("nome"), max_length=60)
    is_active = models.BooleanField(_("ativa"), default=True)

    class Meta:
        verbose_name = _("ala")
        verbose_name_plural = _("alas")
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["establishment", "name"], name="unique_ward_name")
        ]

    def __str__(self):
        return self.name


class Bed(TimeStampedModel):
    ward = models.ForeignKey(
        Ward, on_delete=models.PROTECT, related_name="beds", verbose_name=_("ala")
    )
    number = models.CharField(_("número"), max_length=10)
    is_active = models.BooleanField(_("ativo"), default=True)

    class Meta:
        verbose_name = _("leito")
        verbose_name_plural = _("leitos")
        ordering = ["ward__name", "number"]
        constraints = [models.UniqueConstraint(fields=["ward", "number"], name="unique_bed_number")]

    def __str__(self):
        return f"{self.ward} - leito {self.number}"


# Usuário


class User(AbstractUser):
    full_name = models.CharField(_("nome completo"), max_length=150, blank=True)
    cpf = models.CharField(
        _("CPF"), max_length=11, unique=True, null=True, blank=True, validators=[validate_cpf]
    )
    cns = models.CharField(
        _("CNS"), max_length=15, unique=True, null=True, blank=True, validators=[validate_cns]
    )
    cbo = models.ForeignKey(
        Cbo, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("CBO")
    )
    council_registry = models.CharField(
        _("registro no conselho"), max_length=20, blank=True, help_text=_("Ex.: CRM-PA 12345")
    )
    establishment = models.ForeignKey(
        Establishment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="users",
        verbose_name=_("estabelecimento"),
    )

    class Meta:
        verbose_name = _("usuário")
        verbose_name_plural = _("usuários")

    def __str__(self):
        return self.full_name or self.username
