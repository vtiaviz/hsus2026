import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError

from apps.core.models import Cid10, DischargeReason

from .factories import (
    BedFactory,
    EstablishmentFactory,
    MunicipalityFactory,
    UserFactory,
    WardFactory,
)

pytestmark = pytest.mark.django_db


def test_establishment_cnes_is_unique():
    EstablishmentFactory(cnes="2312166")
    with pytest.raises(IntegrityError):
        EstablishmentFactory(cnes="2312166")


def test_bed_number_is_unique_per_ward():
    bed = BedFactory(number="01")
    BedFactory(number="01")  # outra ala, mesmo número: permitido
    with pytest.raises(IntegrityError):
        BedFactory(ward=bed.ward, number="01")


def test_ward_name_is_unique_per_establishment():
    ward = WardFactory(name="Ala Masculina")
    WardFactory(name="Ala Masculina")
    with pytest.raises(IntegrityError):
        WardFactory(establishment=ward.establishment, name="Ala Masculina")


def test_ward_with_beds_cannot_be_deleted():
    bed = BedFactory()
    with pytest.raises(ProtectedError):
        bed.ward.delete()


def test_municipality_sus_code_has_six_digits():
    municipality = MunicipalityFactory(ibge_code="1501758")
    assert municipality.sus_code == "150175"
    assert str(municipality) == "Brejo Grande do Araguaia/PA"


def test_cid10_formatted_code():
    assert Cid10(code="J189", description="Pneumonia").formatted_code == "J18.9"
    assert Cid10(code="J18", description="Pneumonia").formatted_code == "J18"
    assert str(Cid10(code="J189", description="Pneumonia")) == "J18.9 - Pneumonia"


def test_discharge_reason_ends_care_except_stay():
    assert DischargeReason(code="12", kind=DischargeReason.Kind.DISCHARGE).ends_care
    assert not DischargeReason(code="21", kind=DischargeReason.Kind.STAY).ends_care


def test_string_representations():
    bed = BedFactory(ward__name="Ala Feminina", number="03")
    assert str(bed) == "Ala Feminina - leito 03"
    assert "CNES" in str(bed.ward.establishment)
    user = UserFactory(full_name="Maria Souza")
    assert str(user) == "Maria Souza"
    assert user.check_password("senha-de-teste-123")
