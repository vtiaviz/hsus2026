import random

import factory

from apps.core.models import Bed, Cbo, Establishment, Municipality, User, Ward


def make_cpf() -> str:
    digits = [random.randint(0, 9) for _ in range(9)]
    for size in (9, 10):
        total = sum(d * w for d, w in zip(digits, range(size + 1, 1, -1), strict=True))
        digits.append((total * 10) % 11 % 10)
    return "".join(map(str, digits))


def make_cns() -> str:
    """CNS definitivo (começa com 1 ou 2) gerado pela regra de módulo 11."""
    while True:
        base = [random.choice([1, 2])] + [random.randint(0, 9) for _ in range(10)]
        total = sum(d * w for d, w in zip(base, range(15, 4, -1), strict=True))
        remainder = total % 11
        check = 11 - remainder if remainder else 0
        if check == 10:
            continue
        if check == 11:
            check = 0
        return "".join(map(str, base)) + "000" + str(check)


class MunicipalityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Municipality
        django_get_or_create = ["ibge_code"]

    ibge_code = "1501758"
    name = "Brejo Grande do Araguaia"
    state = "PA"


class CboFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Cbo
        django_get_or_create = ["code"]

    code = "225125"
    title = "Médico clínico"


class EstablishmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Establishment

    name = factory.Sequence(lambda n: f"Hospital Municipal {n}")
    cnes = factory.Sequence(lambda n: f"{2312166 + n:07d}")
    municipality = factory.SubFactory(MunicipalityFactory)
    issuing_body = "M150175801"


class WardFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ward

    establishment = factory.SubFactory(EstablishmentFactory)
    name = factory.Sequence(lambda n: f"Ala {n}")


class BedFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Bed

    ward = factory.SubFactory(WardFactory)
    number = factory.Sequence(lambda n: f"{n + 1:02d}")


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"usuario{n}")
    full_name = factory.Faker("name", locale="pt_BR")
    cpf = factory.LazyFunction(make_cpf)
    cns = factory.LazyFunction(make_cns)
    password = factory.PostGenerationMethodCall("set_password", "senha-de-teste-123")
