import pytest
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone

from apps.clinical.models import ExamType, MedicalCertificate
from apps.core.permissions import Role
from apps.core.tests.factories import (
    MODEL_BACKEND,
    Cid10Factory,
    EstablishmentFactory,
    MunicipalityFactory,
    make_cns,
    make_cpf,
    user_with_roles,
)
from apps.patients.models import Patient, PatientAccessLog
from apps.patients.tests.factories import PatientFactory
from apps.reception.models import CareSession, Consultation, Triage

from .factories import CareSessionFactory, MedicationFactory, TriageFactory

pytestmark = pytest.mark.django_db

Status = CareSession.Status


def login(client, *roles, **kwargs):
    user = user_with_roles(*roles, **kwargs)
    client.force_login(user, backend=MODEL_BACKEND)
    return user


def management(prefix, total=0):
    return {
        f"{prefix}-TOTAL_FORMS": str(total),
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }


def open_session_data(**overrides):
    now = timezone.localtime() - timezone.timedelta(minutes=5)
    data = {
        "session-arrival_date": now.strftime("%Y-%m-%d"),
        "session-arrival_time": now.strftime("%H:%M"),
        "session-complaint": "Febre e tosse",
        "session-origin": "new",
        "patient-cns": make_cns(),
        "patient-cpf": make_cpf(),
        "patient-medical_record_number": "",
        "patient-name": "Paciente Fictício",
        "patient-mother_name": "Mãe Fictícia",
        "patient-sex": "M",
        "patient-race": "03",
        "patient-birth_date": "1970-03-02",
        "patient-phone": "94991112222",
        "patient-street_type": "Rua",
        "patient-street": "Projetada",
        "patient-neighborhood": "Centro",
        "patient-zipcode": "68521000",
        "patient-municipality": MunicipalityFactory().pk,
        **management("medications"),
        **management("exams"),
    }
    return data | overrides


@pytest.fixture(autouse=True)
def establishment():
    return EstablishmentFactory()


class TestIdentification:
    def test_search_by_cns_shows_patient(self, client):
        login(client, Role.ATTENDANT)
        patient = PatientFactory()
        response = client.get(reverse("reception:identification"), {"q": patient.cns})
        assert response.status_code == 200
        assert list(response.context["results"]) == [patient]
        assert reverse("reception:open_session", args=[patient.pk]).encode() in response.content

    def test_search_without_results(self, client):
        login(client, Role.ATTENDANT)
        response = client.get(reverse("reception:identification"), {"q": "Ninguém"})
        assert "Nenhum paciente encontrado" in response.content.decode()

    def test_existing_patient_form_is_prefilled(self, client):
        login(client, Role.ATTENDANT)
        patient = PatientFactory()
        response = client.get(reverse("reception:open_session", args=[patient.pk]))
        assert response.context["patient_form"].instance == patient
        assert patient.name in response.content.decode()

    def test_opening_with_existing_patient_creates_no_duplicate(self, client):
        login(client, Role.ATTENDANT)
        patient = PatientFactory()
        data = open_session_data(
            **{
                "patient-cns": patient.cns,
                "patient-cpf": patient.cpf,
                "patient-medical_record_number": patient.medical_record_number,
                "patient-name": patient.name,
            }
        )
        response = client.post(reverse("reception:open_session", args=[patient.pk]), data)
        care_session = CareSession.objects.get()
        assert response.status_code == 302
        assert response.url == reverse("reception:session_detail", args=[care_session.pk])
        assert Patient.objects.count() == 1
        assert care_session.patient == patient
        assert care_session.status == Status.AWAITING_TRIAGE

    def test_new_patient_and_session(self, client):
        user = login(client, Role.ATTENDANT)
        response = client.post(reverse("reception:open_session_new"), open_session_data())
        assert response.status_code == 302
        patient = Patient.objects.get()
        assert patient.created_by == user
        assert patient.medical_record_number == "1"
        detail = client.get(response.url)
        assert "Aguardando triagem" in detail.content.decode()

    def test_duplicate_cns_offers_existing_record(self, client):
        login(client, Role.ATTENDANT)
        existing = PatientFactory()
        data = open_session_data(**{"patient-cns": existing.cns})
        response = client.post(reverse("reception:open_session_new"), data)
        assert response.status_code == 200
        assert reverse("reception:open_session", args=[existing.pk]) in response.content.decode()
        assert not CareSession.objects.exists()

    def test_patient_with_open_session_is_refused(self, client):
        login(client, Role.ATTENDANT)
        care_session = CareSessionFactory()
        url = reverse("reception:open_session", args=[care_session.patient.pk])
        assert "já tem um atendimento aberto" in client.get(url).content.decode()
        patient = care_session.patient
        data = open_session_data(
            **{
                "patient-cns": patient.cns,
                "patient-cpf": patient.cpf,
                "patient-medical_record_number": patient.medical_record_number,
            }
        )
        client.post(url, data)
        assert CareSession.objects.count() == 1

    def test_service_refusal_rolls_back_patient_changes(self, client, establishment):
        login(client, Role.ATTENDANT)
        EstablishmentFactory()  # dois estabelecimentos e usuário sem vínculo: o service recusa
        response = client.post(reverse("reception:open_session_new"), open_session_data())
        assert response.status_code == 200
        assert "Cadastre o estabelecimento" in response.content.decode()
        assert not Patient.objects.exists()

    def test_future_arrival_is_refused(self, client):
        login(client, Role.ATTENDANT)
        later = timezone.localtime() + timezone.timedelta(days=1)
        data = open_session_data(**{"session-arrival_date": later.strftime("%Y-%m-%d")})
        response = client.post(reverse("reception:open_session_new"), data)
        assert response.status_code == 200
        assert not CareSession.objects.exists()


class TestTransferViews:
    def post(self, client, destination, **extra):
        data = open_session_data(
            **{"session-origin": "transfer", "session-transfer_destination": destination},
            **extra,
        )
        return client.post(reverse("reception:open_session_new"), data)

    def test_infirmary_goes_to_admission_queue(self, client):
        login(client, Role.ATTENDANT)
        physician = user_with_roles(Role.PHYSICIAN)
        Cid10Factory()
        response = self.post(
            client,
            "infirmary",
            **{
                "transfer-physician": physician.pk,
                "transfer-cid10": "J18.9",
                "transfer-diagnosis": "Pneumonia",
                **management("medications", 1),
                "medications-0-medication": MedicationFactory().pk,
                "medications-0-dosage": "500 mg",
                "medications-0-form": "comprimido",
                "medications-0-route": "oral",
                "medications-0-times": "1",
                "medications-0-interval_hours": "8",
                "medications-0-duration": "5",
                "medications-0-duration_unit": "day",
            },
        )
        assert response.status_code == 302
        care_session = CareSession.objects.get()
        assert care_session.status == Status.AWAITING_ADMISSION
        assert care_session.prescribed_medications.count() == 1
        nurse_client = client.__class__()
        login(nurse_client, Role.NURSE)
        queue = nurse_client.get(reverse("infirmary:admission"))
        assert list(queue.context["sessions"]) == [care_session]

    def test_infirmary_without_guide_shows_error(self, client):
        login(client, Role.ATTENDANT)
        response = self.post(client, "infirmary")
        assert response.status_code == 200
        assert "médico responsável" in response.content.decode()
        assert not Patient.objects.exists()

    def test_diagnostic_exam_shows_labsus_link(self, client, settings):
        settings.LABSUS_URL = "https://labsus.example.org"
        login(client, Role.ATTENDANT)
        response = self.post(
            client,
            "diagnostic_exam",
            **{
                **management("exams", 1),
                "exams-0-exam_type": ExamType.objects.get(name="Hemograma").pk,
                "exams-0-external_id": "L-1",
            },
        )
        detail = client.get(response.url)
        assert "https://labsus.example.org" in detail.content.decode()
        assert CareSession.objects.get().status == Status.FINISHED

    def test_telemedicine_registers_patient_and_session(self, client):
        login(client, Role.ATTENDANT)
        page = client.get(reverse("reception:open_session_new")).content.decode()
        assert ">Registrar</button>" in page
        response = self.post(client, "telemedicine")
        assert response.status_code == 302
        care_session = CareSession.objects.get()
        assert care_session.status == Status.FINISHED
        assert care_session.transfer_destination == "telemedicine"
        assert Patient.objects.count() == 1


class TestTriageViews:
    def test_queue_and_save(self, client):
        user = login(client, Role.NURSING_TECHNICIAN)
        care_session = CareSessionFactory()
        queue = client.get(reverse("reception:triage"))
        assert list(queue.context["sessions"]) == [care_session]
        url = reverse("reception:triage_form", args=[care_session.pk])
        assert client.get(url).status_code == 200
        response = client.post(
            url,
            {
                "systolic": "130",
                "diastolic": "85",
                "temperature": "37.8",
                "heart_rate": "88",
                "oxygen_saturation": "96",
                "has_allergy": "on",
                "allergy_description": "Dipirona",
                "risk": "high",
            },
        )
        assert response.status_code == 302
        care_session.refresh_from_db()
        assert care_session.status == Status.AWAITING_CONSULTATION
        assert care_session.triage.recorded_by == user
        assert PatientAccessLog.objects.filter(view_name="triage", user=user).exists()

    @pytest.mark.parametrize(
        ("field_values", "field"),
        [
            ({"oxygen_saturation": "120"}, "oxygen_saturation"),
            ({"systolic": "80", "diastolic": "90"}, "diastolic"),
            ({"has_allergy": "on", "allergy_description": ""}, "allergy_description"),
        ],
    )
    def test_invalid_values_are_refused(self, client, field_values, field):
        login(client, Role.NURSE)
        care_session = CareSessionFactory()
        data = {
            "systolic": "120",
            "diastolic": "80",
            "temperature": "36.5",
            "heart_rate": "80",
            "oxygen_saturation": "98",
            "risk": "low",
        } | field_values
        response = client.post(reverse("reception:triage_form", args=[care_session.pk]), data)
        assert response.status_code == 200
        assert field in response.context["form"].errors
        assert not Triage.objects.exists()

    def test_transfer_session_cannot_be_triaged(self, client):
        login(client, Role.NURSE)
        care_session = CareSessionFactory(
            origin="transfer", transfer_destination="ambulatory", status=Status.AMBULATORY
        )
        response = client.get(reverse("reception:triage_form", args=[care_session.pk]))
        assert response.status_code == 302
        assert response.url == reverse("reception:triage")

    def test_attendant_cannot_triage(self, client):
        login(client, Role.ATTENDANT)
        care_session = CareSessionFactory()
        response = client.get(reverse("reception:triage_form", args=[care_session.pk]))
        assert response.status_code == 403


def consultation_data(referral, **extra):
    return {
        "cid10": "J18.9",
        "diagnosis": "Pneumonia comunitária",
        "care_plan": "Repouso e hidratação",
        "referral": referral,
        **management("medications"),
        **management("exams"),
    } | extra


class TestConsultationViews:
    def test_blocked_without_triage(self, client):
        login(client, Role.PHYSICIAN)
        care_session = CareSessionFactory()
        response = client.get(reverse("reception:consultation_form", args=[care_session.pk]))
        assert response.status_code == 302
        assert response.url == reverse("reception:consultation")
        assert "Aguardando triagem" in str(list(get_messages(response.wsgi_request))[0])

    def test_queue_puts_higher_risk_first(self, client):
        login(client, Role.PHYSICIAN)
        early_low = TriageFactory(
            risk="low", care_session__arrived_at=timezone.now() - timezone.timedelta(hours=3)
        ).care_session
        late_high = TriageFactory(risk="high").care_session
        response = client.get(reverse("reception:consultation"))
        assert list(response.context["sessions"]) == [late_high, early_low]

    def test_infirmary_referral_appears_in_admission_queue(self, client):
        physician = login(client, Role.PHYSICIAN)
        Cid10Factory()
        care_session = TriageFactory().care_session
        url = reverse("reception:consultation_form", args=[care_session.pk])
        page = client.get(url)
        assert page.context["form"].fields["physician"].initial == physician.pk
        data = consultation_data(
            "infirmary",
            physician=physician.pk,
            **{
                **management("exams", 1),
                "exams-0-exam_type": ExamType.objects.get(name="Ureia").pk,
            },
        )
        response = client.post(url, data)
        assert response.status_code == 302
        care_session.refresh_from_db()
        assert care_session.status == Status.AWAITING_ADMISSION
        assert care_session.exam_requests.count() == 1
        assert PatientAccessLog.objects.filter(view_name="consultation").exists()

    def test_ambulatory_referral_appears_in_ambulatory_queue(self, client):
        physician = login(client, Role.PHYSICIAN, Role.NURSE)
        Cid10Factory()
        care_session = TriageFactory().care_session
        client.post(
            reverse("reception:consultation_form", args=[care_session.pk]),
            consultation_data("ambulatory", physician=physician.pk),
        )
        queue = client.get(reverse("ambulatory:procedures"))
        assert list(queue.context["sessions"]) == [care_session]

    def test_unknown_cid_is_refused(self, client):
        physician = login(client, Role.PHYSICIAN)
        care_session = TriageFactory().care_session
        response = client.post(
            reverse("reception:consultation_form", args=[care_session.pk]),
            consultation_data("ambulatory", physician=physician.pk, cid10="Z99.99"),
        )
        assert response.status_code == 200
        assert "cid10" in response.context["form"].errors
        assert not Consultation.objects.exists()

    def test_certificate_without_discharge_is_refused(self, client):
        physician = login(client, Role.PHYSICIAN)
        Cid10Factory()
        care_session = TriageFactory().care_session
        response = client.post(
            reverse("reception:consultation_form", args=[care_session.pk]),
            consultation_data("ambulatory", physician=physician.pk, certificate_days="2"),
        )
        assert response.status_code == 200
        assert "certificate_days" in response.context["form"].errors

    def test_discharge_with_prescription_and_certificate(self, client):
        physician = login(client, Role.PHYSICIAN, council_registry="CRM-PA 0000")
        Cid10Factory()
        care_session = TriageFactory().care_session
        data = consultation_data(
            "discharge",
            physician=physician.pk,
            certificate_days="2",
            certificate_with_cid="on",
            **{
                **management("medications", 1),
                "medications-0-medication": MedicationFactory().pk,
                "medications-0-dosage": "500 mg",
                "medications-0-form": "comprimido",
                "medications-0-route": "oral",
                "medications-0-times": "1",
                "medications-0-interval_hours": "6",
                "medications-0-duration": "3",
                "medications-0-duration_unit": "day",
            },
        )
        response = client.post(reverse("reception:consultation_form", args=[care_session.pk]), data)
        assert response.url == reverse("reception:discharge", args=[care_session.pk])
        care_session.refresh_from_db()
        assert care_session.status == Status.FINISHED
        assert MedicalCertificate.objects.get().cid10.code == "J189"

        discharge = client.get(response.url).content.decode()
        assert reverse("reception:print_prescription", args=[care_session.pk]) in discharge

        prescription = client.get(reverse("reception:print_prescription", args=[care_session.pk]))
        text = prescription.content.decode()
        assert "Dipirona 500 mg" in text
        assert "1 x 6/6 h, durante 3 dia(s)" in text
        assert "CRM-PA 0000" in text

        certificate = client.get(reverse("reception:print_certificate", args=[care_session.pk]))
        assert "2 dias" in certificate.content.decode()
        assert "J18.9" in certificate.content.decode()

    def test_documents_refused_without_discharge(self, client):
        login(client, Role.PHYSICIAN)
        care_session = TriageFactory().care_session
        for name in ("discharge", "print_prescription", "print_certificate"):
            assert (
                client.get(reverse(f"reception:{name}", args=[care_session.pk])).status_code == 404
            )

    def test_discharge_without_documents(self, client):
        physician = login(client, Role.PHYSICIAN)
        Cid10Factory()
        care_session = TriageFactory().care_session
        client.post(
            reverse("reception:consultation_form", args=[care_session.pk]),
            consultation_data("discharge", physician=physician.pk),
        )
        for name in ("print_prescription", "print_certificate"):
            assert (
                client.get(reverse(f"reception:{name}", args=[care_session.pk])).status_code == 404
            )

    def test_finished_session_cannot_be_consulted_again(self, client):
        login(client, Role.PHYSICIAN)
        care_session = CareSessionFactory(status=Status.FINISHED)
        response = client.post(
            reverse("reception:consultation_form", args=[care_session.pk]),
            consultation_data("discharge"),
        )
        assert response.status_code == 302
        assert not Consultation.objects.exists()


def test_radio_groups_render_as_bootstrap_checks_without_blank_option(client):
    login(client, Role.NURSE)
    care_session = CareSessionFactory()
    html = client.get(reverse("reception:triage_form", args=[care_session.pk])).content.decode()
    assert 'name="risk" value="low" id="id_risk_0" required class="form-check-input"' in html
    assert 'name="risk" value=""' not in html
    assert "<legend" not in html
