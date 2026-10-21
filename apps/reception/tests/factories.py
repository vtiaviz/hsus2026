import datetime

import factory
from django.utils import timezone

from apps.clinical.models import Medication
from apps.core.tests.factories import EstablishmentFactory, UserFactory
from apps.patients.tests.factories import PatientFactory
from apps.reception.models import CareSession, Triage


class CareSessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CareSession

    patient = factory.SubFactory(PatientFactory)
    establishment = factory.SubFactory(EstablishmentFactory)
    origin = CareSession.Origin.NEW
    status = CareSession.Status.AWAITING_TRIAGE
    arrived_at = factory.LazyFunction(lambda: timezone.now() - datetime.timedelta(minutes=30))
    complaint = "Febre há três dias"
    created_by = factory.SubFactory(UserFactory)


class TriageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Triage

    care_session = factory.SubFactory(
        CareSessionFactory, status=CareSession.Status.AWAITING_CONSULTATION
    )
    systolic = 120
    diastolic = 80
    temperature = "38.2"
    heart_rate = 90
    oxygen_saturation = 97
    risk = Triage.Risk.MEDIUM
    recorded_by = factory.SubFactory(UserFactory)


class MedicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Medication
        django_get_or_create = ["name"]

    name = "Dipirona 500 mg"
