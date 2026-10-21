"""Máquina de estados do atendimento (spec 002). Todo status muda só por aqui."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.clinical.models import ExamRequest, MedicalCertificate, PrescribedMedication
from apps.core.models import Cid10, Establishment
from apps.patients.models import Patient

from .models import CareSession, Consultation, TelemedicineRecord, Triage

Status = CareSession.Status
Destination = CareSession.Destination
Referral = Consultation.Referral


class CareSessionError(Exception):
    """Operação recusada pela regra do atendimento; a mensagem vai para a tela."""


# Evento → (status de onde pode sair, status para onde vai)
TRANSITIONS = {
    "triage": (Status.AWAITING_TRIAGE, Status.AWAITING_CONSULTATION),
    Referral.AMBULATORY: (Status.AWAITING_CONSULTATION, Status.AMBULATORY),
    Referral.INFIRMARY: (Status.AWAITING_CONSULTATION, Status.AWAITING_ADMISSION),
    Referral.DISCHARGE: (Status.AWAITING_CONSULTATION, Status.FINISHED),
}

TRANSFER_STATUS = {
    Destination.AMBULATORY: Status.AMBULATORY,
    Destination.INFIRMARY: Status.AWAITING_ADMISSION,
    Destination.DIAGNOSTIC_EXAM: Status.FINISHED,
    Destination.TELEMEDICINE: Status.FINISHED,
}


@dataclass
class TransferData:
    """O que vem na guia de transferência, conforme o destino."""

    physician: object | None = None
    cid10: Cid10 | None = None
    diagnosis: str = ""
    care_plan: str = ""
    medications: list[PrescribedMedication] = field(default_factory=list)
    exams: list[ExamRequest] = field(default_factory=list)
    telemedicine: list[TelemedicineRecord] = field(default_factory=list)


def default_establishment(user) -> Establishment:
    if user.establishment_id:
        return user.establishment
    establishments = list(Establishment.objects.all()[:2])
    if len(establishments) != 1:
        raise CareSessionError(
            _("Cadastre o estabelecimento e vincule-o ao seu usuário antes de abrir atendimentos.")
        )
    return establishments[0]


def open_session_of(patient: Patient) -> CareSession | None:
    return patient.care_sessions.exclude(status=Status.FINISHED).first()


def lock(care_session: CareSession) -> CareSession:
    return CareSession.objects.select_for_update().get(pk=care_session.pk)


def ensure_status(care_session: CareSession, expected: str) -> None:
    if care_session.status != expected:
        raise CareSessionError(
            _("O atendimento está em “%(current)s”; esta etapa exige “%(expected)s”.")
            % {
                "current": care_session.get_status_display(),
                "expected": Status(expected).label,
            }
        )


def apply_transition(care_session: CareSession, event: str) -> None:
    source, target = TRANSITIONS[event]
    ensure_status(care_session, source)
    care_session.status = target
    if target == Status.FINISHED:
        care_session.finished_at = timezone.now()
    care_session.save(update_fields=["status", "finished_at"])


def _save_medications(care_session, consultation, medications: Iterable[PrescribedMedication]):
    for item in medications:
        item.care_session = care_session
        item.consultation = consultation
        item.save()


def _save_exams(care_session, consultation, exams: Iterable[ExamRequest], user):
    for item in exams:
        item.care_session = care_session
        item.consultation = consultation
        item.requested_by = user
        item.save()


@transaction.atomic
def open_care_session(
    *,
    patient: Patient,
    user,
    origin: str,
    arrived_at: datetime,
    complaint: str,
    destination: str = "",
    transfer: TransferData | None = None,
) -> CareSession:
    if arrived_at > timezone.now():
        raise CareSessionError(_("A chegada não pode estar no futuro."))
    current = open_session_of(patient)
    if current:
        raise CareSessionError(
            _("O paciente já tem um atendimento aberto (%(status)s).")
            % {"status": current.get_status_display()}
        )
    if origin == CareSession.Origin.NEW:
        destination, status = "", Status.AWAITING_TRIAGE
    else:
        if destination not in TRANSFER_STATUS:
            raise CareSessionError(_("Escolha o destino da transferência."))
        status = TRANSFER_STATUS[destination]
        transfer = transfer or TransferData()
        _validate_transfer(destination, transfer)

    care_session = CareSession(
        patient=patient,
        establishment=default_establishment(user),
        origin=origin,
        transfer_destination=destination,
        status=status,
        arrived_at=arrived_at,
        complaint=complaint,
        created_by=user,
        finished_at=timezone.now() if status == Status.FINISHED else None,
    )
    try:
        with transaction.atomic():
            care_session.save()
    except IntegrityError as error:
        raise CareSessionError(_("O paciente já tem um atendimento aberto.")) from error

    if origin == CareSession.Origin.TRANSFER:
        _save_transfer(care_session, destination, transfer, user)
    return care_session


def _validate_transfer(destination: str, transfer: TransferData) -> None:
    if destination in (Destination.AMBULATORY, Destination.INFIRMARY):
        if not (transfer.physician and transfer.cid10 and transfer.diagnosis):
            raise CareSessionError(
                _("Informe o médico responsável, o CID-10 e o diagnóstico da guia.")
            )
    elif destination == Destination.DIAGNOSTIC_EXAM and not transfer.exams:
        raise CareSessionError(_("Informe pelo menos um exame."))
    elif destination == Destination.TELEMEDICINE and not transfer.telemedicine:
        raise CareSessionError(_("Informe pelo menos uma data e quantidade de telemedicina."))


def _save_transfer(care_session, destination, transfer: TransferData, user) -> None:
    consultation = None
    if destination in (Destination.AMBULATORY, Destination.INFIRMARY):
        consultation = Consultation.objects.create(
            care_session=care_session,
            kind=Consultation.Kind.TRANSFER,
            physician=transfer.physician,
            cid10=transfer.cid10,
            diagnosis=transfer.diagnosis,
            care_plan=transfer.care_plan,
            referral=destination,
            recorded_by=user,
        )
        _save_medications(care_session, consultation, transfer.medications)
    _save_exams(care_session, consultation, transfer.exams, user)
    for record in transfer.telemedicine:
        record.care_session = care_session
        record.recorded_by = user
        record.save()


@transaction.atomic
def record_triage(care_session: CareSession, triage: Triage, user) -> Triage:
    care_session = lock(care_session)
    ensure_status(care_session, Status.AWAITING_TRIAGE)
    triage.care_session = care_session
    triage.recorded_by = user
    if not triage.has_allergy:
        triage.allergy_description = ""
    triage.save()
    apply_transition(care_session, "triage")
    return triage


@transaction.atomic
def record_consultation(
    care_session: CareSession,
    consultation: Consultation,
    user,
    *,
    medications: Iterable[PrescribedMedication] = (),
    exams: Iterable[ExamRequest] = (),
    certificate_days: int | None = None,
    certificate_cid10: Cid10 | None = None,
) -> Consultation:
    care_session = lock(care_session)
    ensure_status(care_session, Status.AWAITING_CONSULTATION)
    if certificate_days and consultation.referral != Referral.DISCHARGE:
        raise CareSessionError(_("O atestado só é emitido na alta."))
    consultation.care_session = care_session
    consultation.kind = Consultation.Kind.ENTRY
    consultation.recorded_by = user
    consultation.save()
    _save_medications(care_session, consultation, medications)
    _save_exams(care_session, consultation, exams, user)
    if certificate_days:
        MedicalCertificate.objects.create(
            care_session=care_session,
            days=certificate_days,
            cid10=certificate_cid10,
            physician=consultation.physician,
        )
    apply_transition(care_session, consultation.referral)
    return consultation
