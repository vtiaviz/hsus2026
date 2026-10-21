import datetime

import pytest
from django.utils import timezone

from apps.clinical.models import ExamRequest, ExamType, MedicalCertificate, PrescribedMedication
from apps.core.permissions import Role
from apps.core.tests.factories import (
    Cid10Factory,
    EstablishmentFactory,
    UserFactory,
    user_with_roles,
)
from apps.patients.tests.factories import PatientFactory
from apps.reception import selectors, services
from apps.reception.models import CareSession, Consultation, TelemedicineRecord, Triage

from .factories import CareSessionFactory, MedicationFactory, TriageFactory

pytestmark = pytest.mark.django_db

Status = CareSession.Status
Destination = CareSession.Destination
Referral = Consultation.Referral


@pytest.fixture
def attendant():
    return user_with_roles(Role.ATTENDANT, establishment=EstablishmentFactory())


@pytest.fixture
def physician():
    return user_with_roles(Role.PHYSICIAN, full_name="Dra. Fictícia")


def open_session(user, patient=None, **kwargs):
    defaults = {
        "patient": patient or PatientFactory(),
        "user": user,
        "origin": CareSession.Origin.NEW,
        "arrived_at": timezone.now() - datetime.timedelta(minutes=5),
        "complaint": "Dor de cabeça",
    }
    return services.open_care_session(**(defaults | kwargs))


def medication_item():
    return PrescribedMedication(
        medication=MedicationFactory(),
        dosage="500 mg",
        form="comprimido",
        route="oral",
        times=1,
        interval_hours=8,
        duration=5,
        duration_unit="day",
    )


def test_new_patient_goes_to_triage(attendant):
    care_session = open_session(attendant)
    assert care_session.status == Status.AWAITING_TRIAGE
    assert care_session.establishment == attendant.establishment
    assert list(selectors.triage_queue()) == [care_session]


def test_arrival_in_the_future_is_refused(attendant):
    with pytest.raises(services.CareSessionError):
        open_session(attendant, arrived_at=timezone.now() + datetime.timedelta(hours=1))


def test_second_open_session_for_same_patient_is_refused(attendant):
    care_session = open_session(attendant)
    with pytest.raises(services.CareSessionError, match="Aguardando triagem"):
        open_session(attendant, patient=care_session.patient)


def test_finished_session_allows_a_new_one(attendant):
    finished = CareSessionFactory(status=Status.FINISHED)
    assert open_session(attendant, patient=finished.patient).status == Status.AWAITING_TRIAGE


def test_establishment_falls_back_to_the_only_one():
    establishment = EstablishmentFactory()
    assert services.default_establishment(UserFactory()) == establishment


def test_establishment_is_required_when_ambiguous():
    EstablishmentFactory()
    EstablishmentFactory()
    with pytest.raises(services.CareSessionError):
        services.default_establishment(UserFactory())


class TestTransfer:
    def test_to_infirmary_goes_to_admission_queue_with_guide(self, attendant, physician):
        care_session = open_session(
            attendant,
            origin=CareSession.Origin.TRANSFER,
            destination=Destination.INFIRMARY,
            transfer=services.TransferData(
                physician=physician,
                cid10=Cid10Factory(),
                diagnosis="Pneumonia",
                medications=[medication_item()],
                exams=[ExamRequest(exam_type=ExamType.objects.get(name="Hemograma"))],
            ),
        )
        assert care_session.status == Status.AWAITING_ADMISSION
        guide = care_session.consultation
        assert (guide.kind, guide.physician, guide.recorded_by) == (
            Consultation.Kind.TRANSFER,
            physician,
            attendant,
        )
        assert guide.prescribed_medications.count() == 1
        assert care_session.exam_requests.get().requested_by == attendant
        assert list(selectors.sessions_with_status(Status.AWAITING_ADMISSION)) == [care_session]

    def test_to_ambulatory(self, attendant, physician):
        care_session = open_session(
            attendant,
            origin=CareSession.Origin.TRANSFER,
            destination=Destination.AMBULATORY,
            transfer=services.TransferData(
                physician=physician, cid10=Cid10Factory(), diagnosis="Pneumonia"
            ),
        )
        assert care_session.status == Status.AMBULATORY

    def test_guide_is_required_for_ambulatory_and_infirmary(self, attendant):
        with pytest.raises(services.CareSessionError, match="médico responsável"):
            open_session(
                attendant, origin=CareSession.Origin.TRANSFER, destination=Destination.INFIRMARY
            )

    def test_destination_is_required(self, attendant):
        with pytest.raises(services.CareSessionError, match="destino"):
            open_session(attendant, origin=CareSession.Origin.TRANSFER)

    def test_diagnostic_exam_records_requests_and_finishes(self, attendant):
        exam = ExamRequest(exam_type=ExamType.objects.get(name="ECG"), external_id="LAB-123")
        care_session = open_session(
            attendant,
            origin=CareSession.Origin.TRANSFER,
            destination=Destination.DIAGNOSTIC_EXAM,
            transfer=services.TransferData(exams=[exam]),
        )
        assert care_session.status == Status.FINISHED
        assert care_session.finished_at is not None
        assert care_session.exam_requests.get().external_id == "LAB-123"

    def test_diagnostic_exam_needs_an_exam(self, attendant):
        with pytest.raises(services.CareSessionError, match="exame"):
            open_session(
                attendant,
                origin=CareSession.Origin.TRANSFER,
                destination=Destination.DIAGNOSTIC_EXAM,
            )

    def test_telemedicine_records_dates_and_quantities(self, attendant):
        records = [
            TelemedicineRecord(date=datetime.date(2026, 10, 1), quantity=2),
            TelemedicineRecord(date=datetime.date(2026, 10, 8), quantity=1),
        ]
        care_session = open_session(
            attendant,
            origin=CareSession.Origin.TRANSFER,
            destination=Destination.TELEMEDICINE,
            transfer=services.TransferData(telemedicine=records),
        )
        assert care_session.status == Status.FINISHED
        assert [r.quantity for r in care_session.telemedicine_records.all()] == [2, 1]

    def test_telemedicine_needs_a_record(self, attendant):
        with pytest.raises(services.CareSessionError, match="telemedicina"):
            open_session(
                attendant,
                origin=CareSession.Origin.TRANSFER,
                destination=Destination.TELEMEDICINE,
            )

    def test_transfer_session_refuses_triage(self, attendant, physician):
        care_session = open_session(
            attendant,
            origin=CareSession.Origin.TRANSFER,
            destination=Destination.AMBULATORY,
            transfer=services.TransferData(
                physician=physician, cid10=Cid10Factory(), diagnosis="Pneumonia"
            ),
        )
        with pytest.raises(services.CareSessionError):
            services.record_triage(care_session, TriageFactory.build(), UserFactory())


def triage_for(care_session, **kwargs):
    return TriageFactory.build(care_session=None, **kwargs)


class TestTriage:
    def test_moves_to_consultation_queue(self):
        care_session = CareSessionFactory()
        nurse = UserFactory()
        triage = services.record_triage(care_session, triage_for(care_session), nurse)
        care_session.refresh_from_db()
        assert care_session.status == Status.AWAITING_CONSULTATION
        assert triage.recorded_by == nurse

    def test_second_triage_is_refused(self):
        care_session = CareSessionFactory()
        services.record_triage(care_session, triage_for(care_session), UserFactory())
        with pytest.raises(services.CareSessionError):
            services.record_triage(care_session, triage_for(care_session), UserFactory())

    def test_allergy_description_is_cleared_without_allergy(self):
        care_session = CareSessionFactory()
        triage = services.record_triage(
            care_session,
            triage_for(care_session, has_allergy=False, allergy_description="dipirona"),
            UserFactory(),
        )
        assert triage.allergy_description == ""


def test_consultation_queue_orders_by_risk_then_arrival():
    now = timezone.now()
    low_early = TriageFactory(
        risk=Triage.Risk.LOW, care_session__arrived_at=now - datetime.timedelta(hours=2)
    ).care_session
    high_late = TriageFactory(
        risk=Triage.Risk.HIGH, care_session__arrived_at=now - datetime.timedelta(minutes=10)
    ).care_session
    very_high = TriageFactory(risk=Triage.Risk.VERY_HIGH).care_session
    medium = TriageFactory(risk=Triage.Risk.MEDIUM).care_session
    assert list(selectors.consultation_queue()) == [very_high, high_late, medium, low_early]


class TestConsultation:
    def consult(self, care_session, physician, referral, **kwargs):
        consultation = Consultation(
            physician=physician, cid10=Cid10Factory(), diagnosis="Pneumonia", referral=referral
        )
        return services.record_consultation(care_session, consultation, physician, **kwargs)

    def test_without_triage_is_refused(self, physician):
        care_session = CareSessionFactory()
        with pytest.raises(services.CareSessionError, match="Aguardando triagem"):
            self.consult(care_session, physician, Referral.AMBULATORY)

    @pytest.mark.parametrize(
        ("referral", "status"),
        [
            (Referral.AMBULATORY, Status.AMBULATORY),
            (Referral.INFIRMARY, Status.AWAITING_ADMISSION),
        ],
    )
    def test_referral_moves_session(self, physician, referral, status):
        care_session = TriageFactory().care_session
        self.consult(care_session, physician, referral)
        care_session.refresh_from_db()
        assert care_session.status == status
        assert care_session.finished_at is None

    def test_prescription_and_exams(self, physician):
        care_session = TriageFactory().care_session
        consultation = self.consult(
            care_session,
            physician,
            Referral.INFIRMARY,
            medications=[medication_item()],
            exams=[ExamRequest(exam_type=ExamType.objects.get(name="Glicemia"))],
        )
        item = consultation.prescribed_medications.get()
        assert item.care_session == care_session
        assert item.posology == "1 x 8/8 h, durante 5 dia(s)"
        assert consultation.exam_requests.get().exam_type.name == "Glicemia"

    def test_discharge_finishes_with_certificate(self, physician):
        care_session = TriageFactory().care_session
        self.consult(care_session, physician, Referral.DISCHARGE, certificate_days=3)
        care_session.refresh_from_db()
        assert care_session.status == Status.FINISHED
        assert care_session.finished_at is not None
        certificate = MedicalCertificate.objects.get(care_session=care_session)
        assert (certificate.days, certificate.physician, certificate.cid10) == (3, physician, None)

    def test_certificate_only_on_discharge(self, physician):
        care_session = TriageFactory().care_session
        with pytest.raises(services.CareSessionError, match="alta"):
            self.consult(care_session, physician, Referral.AMBULATORY, certificate_days=3)

    def test_finished_session_is_read_only(self, physician):
        care_session = TriageFactory().care_session
        self.consult(care_session, physician, Referral.DISCHARGE)
        with pytest.raises(services.CareSessionError, match="Finalizado"):
            self.consult(care_session, physician, Referral.DISCHARGE)
        with pytest.raises(services.CareSessionError, match="Finalizado"):
            services.record_triage(care_session, triage_for(care_session), physician)


def test_physicians_lists_only_active_physicians(physician):
    user_with_roles(Role.PHYSICIAN, is_active=False)
    user_with_roles(Role.NURSE)
    assert list(selectors.physicians()) == [physician]
