import datetime

import factory

from apps.core.tests.factories import MunicipalityFactory, UserFactory, make_cns, make_cpf
from apps.patients.models import Patient, Race, Sex


class PatientFactory(factory.django.DjangoModelFactory):
    """Paciente fictício com CNS e CPF válidos (nunca dados reais)."""

    class Meta:
        model = Patient

    cns = factory.LazyFunction(make_cns)
    cpf = factory.LazyFunction(make_cpf)
    medical_record_number = factory.Sequence(lambda n: str(1000 + n))
    name = factory.Faker("name", locale="pt_BR")
    mother_name = factory.Faker("name_female", locale="pt_BR")
    sex = Sex.FEMALE
    race = Race.BROWN
    birth_date = datetime.date(1985, 5, 20)
    phone = "94991234567"
    street_type = "Rua"
    street = factory.Faker("street_name", locale="pt_BR")
    number = "10"
    neighborhood = "Centro"
    zipcode = "68521000"
    municipality = factory.SubFactory(MunicipalityFactory)
    created_by = factory.SubFactory(UserFactory)
