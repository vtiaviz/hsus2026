from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.core.models import Cid10, Establishment
from apps.patients.models import Patient


class CareSession(models.Model):
    """O atendimento: raiz de todo registro clínico (constituição, princípio IV)."""

    class Origin(models.TextChoices):
        NEW = "new", _("Novo")
        TRANSFER = "transfer", _("Transferência")

    class Destination(models.TextChoices):
        AMBULATORY = "ambulatory", _("Ambulatório")
        INFIRMARY = "infirmary", _("Enfermaria")
        DIAGNOSTIC_EXAM = "diagnostic_exam", _("Exame de apoio diagnóstico")
        TELEMEDICINE = "telemedicine", _("Telemedicina")

    class Status(models.TextChoices):
        AWAITING_TRIAGE = "awaiting_triage", _("Aguardando triagem")
        AWAITING_CONSULTATION = "awaiting_consultation", _("Aguardando consulta")
        AMBULATORY = "ambulatory", _("No ambulatório")
        AWAITING_ADMISSION = "awaiting_admission", _("Aguardando admissão")
        FINISHED = "finished", _("Finalizado")

    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name="care_sessions", verbose_name=_("paciente")
    )
    establishment = models.ForeignKey(
        Establishment, on_delete=models.PROTECT, verbose_name=_("estabelecimento")
    )
    origin = models.CharField(_("origem"), max_length=10, choices=Origin.choices)
    transfer_destination = models.CharField(
        _("destino da transferência"), max_length=20, choices=Destination.choices, blank=True
    )
    status = models.CharField(_("status"), max_length=25, choices=Status.choices)
    arrived_at = models.DateTimeField(_("chegada"))
    complaint = models.CharField(_("relato"), max_length=250)
    finished_at = models.DateTimeField(_("saída"), null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("aberto por"),
    )
    created_at = models.DateTimeField(_("aberto em"), auto_now_add=True)

    class Meta:
        verbose_name = _("atendimento")
        verbose_name_plural = _("atendimentos")
        ordering = ["arrived_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["patient"],
                condition=~Q(status="finished"),
                name="one_open_care_session_per_patient",
            ),
            models.CheckConstraint(
                condition=Q(origin="new", transfer_destination="")
                | (Q(origin="transfer") & ~Q(transfer_destination="")),
                name="transfer_has_destination",
            ),
        ]

    def __str__(self):
        return f"#{self.pk} {self.patient}"

    @property
    def is_finished(self) -> bool:
        return self.status == self.Status.FINISHED


class Triage(models.Model):
    class Risk(models.TextChoices):
        LOW = "low", _("Baixa")
        MEDIUM = "medium", _("Média")
        HIGH = "high", _("Alta")
        VERY_HIGH = "very_high", _("Muito alta")

    care_session = models.OneToOneField(
        CareSession, on_delete=models.PROTECT, related_name="triage", verbose_name=_("atendimento")
    )
    systolic = models.PositiveSmallIntegerField(
        _("PA sistólica (mmHg)"), validators=[MinValueValidator(40), MaxValueValidator(300)]
    )
    diastolic = models.PositiveSmallIntegerField(
        _("PA diastólica (mmHg)"), validators=[MinValueValidator(20), MaxValueValidator(200)]
    )
    temperature = models.DecimalField(
        _("temperatura (°C)"),
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(30), MaxValueValidator(45)],
    )
    heart_rate = models.PositiveSmallIntegerField(
        _("frequência cardíaca (bpm)"), validators=[MinValueValidator(20), MaxValueValidator(250)]
    )
    oxygen_saturation = models.PositiveSmallIntegerField(
        _("saturação de O2 (%)"), validators=[MinValueValidator(50), MaxValueValidator(100)]
    )
    has_allergy = models.BooleanField(_("tem alergia"), default=False)
    allergy_description = models.CharField(_("alergias"), max_length=250, blank=True)
    risk = models.CharField(_("classificação de risco"), max_length=10, choices=Risk.choices)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("registrado por"),
    )
    recorded_at = models.DateTimeField(_("registrado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("triagem")
        verbose_name_plural = _("triagens")

    def __str__(self):
        return f"Triagem {self.care_session}"

    @property
    def blood_pressure(self) -> str:
        return f"{self.systolic}x{self.diastolic}"


class Consultation(models.Model):
    """Consulta de entrada, ou dados da guia de um paciente transferido."""

    class Kind(models.TextChoices):
        ENTRY = "entry", _("Consulta de entrada")
        TRANSFER = "transfer", _("Guia de transferência")

    class Referral(models.TextChoices):
        AMBULATORY = "ambulatory", _("Ambulatório")
        INFIRMARY = "infirmary", _("Enfermaria")
        DISCHARGE = "discharge", _("Alta")

    care_session = models.OneToOneField(
        CareSession,
        on_delete=models.PROTECT,
        related_name="consultation",
        verbose_name=_("atendimento"),
    )
    kind = models.CharField(_("tipo"), max_length=10, choices=Kind.choices)
    physician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("médico responsável"),
    )
    cid10 = models.ForeignKey(Cid10, on_delete=models.PROTECT, verbose_name=_("CID-10"))
    diagnosis = models.TextField(_("diagnóstico"), max_length=1000)
    care_plan = models.TextField(_("plano de cuidado"), max_length=1000, blank=True)
    referral = models.CharField(_("encaminhamento"), max_length=10, choices=Referral.choices)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("registrado por"),
    )
    recorded_at = models.DateTimeField(_("registrado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("consulta")
        verbose_name_plural = _("consultas")

    def __str__(self):
        return f"Consulta {self.care_session}"


class TelemedicineRecord(models.Model):
    care_session = models.ForeignKey(
        CareSession,
        on_delete=models.PROTECT,
        related_name="telemedicine_records",
        verbose_name=_("atendimento"),
    )
    date = models.DateField(_("data"))
    quantity = models.PositiveSmallIntegerField(_("quantidade"), validators=[MinValueValidator(1)])
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("registrado por"),
    )
    recorded_at = models.DateTimeField(_("registrado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("registro de telemedicina")
        verbose_name_plural = _("registros de telemedicina")
        ordering = ["date"]

    def __str__(self):
        return f"{self.date:%d/%m/%Y}: {self.quantity}"
