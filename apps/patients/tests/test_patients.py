import pytest

from apps.core.tests.factories import MunicipalityFactory, UserFactory, make_cns, make_cpf
from apps.patients.forms import PatientForm
from apps.patients.models import Patient
from apps.patients.selectors import search_patients
from apps.patients.services import log_access, next_medical_record_number, save_patient

from .factories import PatientFactory

pytestmark = pytest.mark.django_db


def form_data(**overrides):
    data = {
        "cns": make_cns(),
        "cpf": make_cpf(),
        "medical_record_number": "",
        "name": "Maria da Conceição",
        "mother_name": "Ana da Conceição",
        "sex": "F",
        "race": "03",
        "birth_date": "1990-01-15",
        "phone": "(94) 99123-4567",
        "street_type": "Rua",
        "street": "das Flores",
        "number": "",
        "complement": "",
        "neighborhood": "Centro",
        "zipcode": "68521-000",
        "municipality": MunicipalityFactory().pk,
    }
    return data | overrides


def test_form_accepts_masked_values_and_strips_them():
    data = form_data()
    cpf = data["cpf"]
    data["cpf"] = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    form = PatientForm(data)
    assert form.is_valid(), form.errors
    assert form.cleaned_data["cpf"] == cpf
    assert form.cleaned_data["phone"] == "94991234567"
    assert form.cleaned_data["zipcode"] == "68521000"


@pytest.mark.parametrize("field", ["cns", "cpf"])
def test_form_rejects_wrong_check_digit(field):
    valid = form_data()[field]
    wrong = valid[:-1] + str((int(valid[-1]) + 1) % 10)
    form = PatientForm(form_data(**{field: wrong}))
    assert not form.is_valid()
    assert field in form.errors


def test_form_requires_cns_or_cpf():
    form = PatientForm(form_data(cns="", cpf=""))
    assert not form.is_valid()
    assert "Informe o CNS ou o CPF." in form.non_field_errors()


def test_form_accepts_only_one_document():
    assert PatientForm(form_data(cpf="")).is_valid()
    assert PatientForm(form_data(cns="")).is_valid()


@pytest.mark.parametrize("field", ["cns", "cpf"])
def test_duplicate_document_points_to_existing_patient(field):
    existing = PatientFactory()
    form = PatientForm(form_data(**{field: getattr(existing, field)}))
    assert not form.is_valid()
    assert form.existing_patient == existing
    assert existing.name in form.errors[field][0]


def test_editing_patient_keeps_own_documents():
    patient = PatientFactory()
    data = form_data(
        cns=patient.cns, cpf=patient.cpf, medical_record_number=patient.medical_record_number
    )
    form = PatientForm(data, instance=patient)
    assert form.is_valid(), form.errors


def test_birth_date_in_future_is_rejected():
    form = PatientForm(form_data(birth_date="2999-01-01"))
    assert not form.is_valid()
    assert "birth_date" in form.errors


def test_save_patient_generates_next_medical_record_number():
    PatientFactory(medical_record_number="41")
    user = UserFactory()
    form = PatientForm(form_data())
    assert form.is_valid(), form.errors
    patient = save_patient(form.save(commit=False), user)
    assert patient.medical_record_number == "42"
    assert patient.created_by == user


def test_next_medical_record_number_starts_at_one():
    assert next_medical_record_number() == "1"


def test_save_patient_keeps_typed_medical_record_number():
    form = PatientForm(form_data(medical_record_number="9001"))
    assert form.is_valid(), form.errors
    assert save_patient(form.save(commit=False), UserFactory()).medical_record_number == "9001"


def test_age():
    import datetime

    patient = PatientFactory.build(birth_date=datetime.date(2000, 6, 10))
    assert patient.age(datetime.date(2026, 6, 9)) == 25
    assert patient.age(datetime.date(2026, 6, 10)) == 26


class TestSearch:
    def test_by_cns_with_mask(self):
        patient = PatientFactory()
        masked = f"{patient.cns[:3]} {patient.cns[3:7]} {patient.cns[7:11]} {patient.cns[11:]}"
        assert list(search_patients(masked)) == [patient]

    def test_by_cpf_with_mask(self):
        patient = PatientFactory()
        cpf = patient.cpf
        assert list(search_patients(f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}")) == [patient]

    def test_by_medical_record_number(self):
        patient = PatientFactory(medical_record_number="777")
        assert list(search_patients("777")) == [patient]

    def test_by_name_and_mother_ignoring_accents_and_case(self):
        patient = PatientFactory(name="José Antônio", mother_name="Conceição Silva")
        PatientFactory(name="José Antônio", mother_name="Outra Mãe")
        assert list(search_patients("jose antonio", "conceicao")) == [patient]

    def test_empty_query_returns_nothing(self):
        PatientFactory()
        assert list(search_patients("", "")) == []


def test_log_access():
    patient = PatientFactory()
    user = UserFactory()
    log_access(user=user, patient=patient, view_name="triage")
    log = patient.access_logs.get()
    assert (log.user, log.view_name) == (user, "triage")
    assert str(log)


def test_patient_requires_document_in_database():
    from django.db import IntegrityError, transaction

    with pytest.raises(IntegrityError), transaction.atomic():
        PatientFactory(cns=None, cpf=None)
    assert not Patient.objects.exists()


def test_save_patient_reports_duplicate_document():
    from apps.patients.services import DuplicatePatientError

    existing = PatientFactory()
    duplicate = PatientFactory.build(cns=existing.cns, created_by=existing.created_by)
    duplicate.municipality.save()
    with pytest.raises(DuplicatePatientError):
        save_patient(duplicate, existing.created_by)
