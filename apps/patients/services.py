from django.db import IntegrityError, transaction
from django.db.models import IntegerField, Max
from django.db.models.functions import Cast

from .models import Patient, PatientAccessLog


class DuplicatePatientError(Exception):
    """Outro paciente já usa o CNS, o CPF ou o prontuário informado."""


def next_medical_record_number() -> str:
    numbers = Patient.objects.exclude(medical_record_number="").annotate(
        as_number=Cast("medical_record_number", IntegerField())
    )
    highest = numbers.aggregate(highest=Max("as_number"))["highest"] or 0
    return str(highest + 1)


def save_patient(patient: Patient, user) -> Patient:
    """Cadastra ou atualiza o paciente; gera o prontuário quando vem vazio."""
    if patient.pk is None:
        patient.created_by = user
    generated = not patient.medical_record_number
    for _attempt in range(3):
        if generated:
            patient.medical_record_number = next_medical_record_number()
        try:
            with transaction.atomic():
                patient.save()
            return patient
        except IntegrityError as error:
            # Outro atendente pode ter levado o mesmo número gerado; tenta o próximo.
            if not generated or "medical_record_number" not in str(error):
                raise DuplicatePatientError(str(error)) from error
    raise DuplicatePatientError("prontuário")


def log_access(*, user, patient: Patient, care_session=None, view_name: str) -> None:
    PatientAccessLog.objects.create(
        user=user, patient=patient, care_session=care_session, view_name=view_name
    )
