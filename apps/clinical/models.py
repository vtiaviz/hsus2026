from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import Cid10, TimeStampedModel

# Catálogos mantidos pelo admin


class Medication(TimeStampedModel):
    name = models.CharField(_("nome"), max_length=150, unique=True)
    is_active = models.BooleanField(_("ativo"), default=True)

    class Meta:
        verbose_name = _("medicamento")
        verbose_name_plural = _("medicamentos")
        ordering = ["name"]

    def __str__(self):
        return self.name


class ExamType(TimeStampedModel):
    name = models.CharField(_("nome"), max_length=150, unique=True)
    is_active = models.BooleanField(_("ativo"), default=True)

    class Meta:
        verbose_name = _("tipo de exame")
        verbose_name_plural = _("tipos de exame")
        ordering = ["name"]

    def __str__(self):
        return self.name


# Registros clínicos, sempre ligados a um atendimento


class PrescribedMedication(models.Model):
    class Interval(models.IntegerChoices):
        EVERY_6H = 6, "6/6 h"
        EVERY_8H = 8, "8/8 h"
        EVERY_12H = 12, "12/12 h"
        EVERY_24H = 24, "24/24 h"

    class DurationUnit(models.TextChoices):
        DAY = "day", _("dia(s)")
        WEEK = "week", _("semana(s)")
        MONTH = "month", _("mês(es)")

    care_session = models.ForeignKey(
        "reception.CareSession",
        on_delete=models.PROTECT,
        related_name="prescribed_medications",
        verbose_name=_("atendimento"),
    )
    consultation = models.ForeignKey(
        "reception.Consultation",
        on_delete=models.PROTECT,
        related_name="prescribed_medications",
        verbose_name=_("consulta"),
    )
    medication = models.ForeignKey(
        Medication, on_delete=models.PROTECT, verbose_name=_("medicamento")
    )
    dosage = models.CharField(_("dosagem"), max_length=40)
    form = models.CharField(_("forma"), max_length=40)
    route = models.CharField(_("via"), max_length=40)
    times = models.PositiveSmallIntegerField(_("vezes"))
    interval_hours = models.PositiveSmallIntegerField(_("intervalo"), choices=Interval.choices)
    duration = models.PositiveSmallIntegerField(_("duração"))
    duration_unit = models.CharField(
        _("unidade da duração"), max_length=5, choices=DurationUnit.choices
    )

    class Meta:
        verbose_name = _("medicamento prescrito")
        verbose_name_plural = _("medicamentos prescritos")
        ordering = ["pk"]

    def __str__(self):
        return f"{self.medication} {self.dosage}"

    @property
    def posology(self) -> str:
        return (
            f"{self.times} x {self.get_interval_hours_display()}, "
            f"durante {self.duration} {self.get_duration_unit_display()}"
        )


class ExamRequest(models.Model):
    care_session = models.ForeignKey(
        "reception.CareSession",
        on_delete=models.PROTECT,
        related_name="exam_requests",
        verbose_name=_("atendimento"),
    )
    consultation = models.ForeignKey(
        "reception.Consultation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="exam_requests",
        verbose_name=_("consulta"),
    )
    exam_type = models.ForeignKey(ExamType, on_delete=models.PROTECT, verbose_name=_("exame"))
    external_id = models.CharField(
        _("identificador no LabSUS"), max_length=40, blank=True, help_text=_("Opcional.")
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("registrado por"),
    )
    requested_at = models.DateTimeField(_("registrado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("pedido de exame")
        verbose_name_plural = _("pedidos de exame")
        ordering = ["pk"]

    def __str__(self):
        return str(self.exam_type)


class MedicalCertificate(models.Model):
    """Atestado emitido na alta (etapa de encerramento)."""

    care_session = models.OneToOneField(
        "reception.CareSession",
        on_delete=models.PROTECT,
        related_name="certificate",
        verbose_name=_("atendimento"),
    )
    days = models.PositiveSmallIntegerField(_("dias de afastamento"))
    cid10 = models.ForeignKey(
        Cid10,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("CID-10 no atestado"),
    )
    physician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("médico"),
    )
    issued_at = models.DateTimeField(_("emitido em"), auto_now_add=True)

    class Meta:
        verbose_name = _("atestado")
        verbose_name_plural = _("atestados")

    def __str__(self):
        return f"{self.days} dia(s) - {self.care_session}"
