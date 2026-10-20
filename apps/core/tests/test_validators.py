import pytest
from django.core.exceptions import ValidationError

from apps.core.validators import (
    is_valid_cns,
    is_valid_cpf,
    validate_cns,
    validate_cpf,
    validate_digits,
)

from .factories import make_cns, make_cpf


@pytest.mark.parametrize("cpf", ["52998224725", "529.982.247-25"])
def test_valid_cpf(cpf):
    assert is_valid_cpf(cpf)


@pytest.mark.parametrize("cpf", ["52998224726", "11111111111", "123", ""])
def test_invalid_cpf(cpf):
    assert not is_valid_cpf(cpf)


def test_generated_documents_are_valid():
    for _ in range(50):
        assert is_valid_cpf(make_cpf())
        assert is_valid_cns(make_cns())


@pytest.mark.parametrize("cns", ["123", "", "300000000000000", "100000000000001"])
def test_invalid_cns(cns):
    assert not is_valid_cns(cns)


def test_validate_functions_raise():
    with pytest.raises(ValidationError):
        validate_cpf("52998224726")
    with pytest.raises(ValidationError):
        validate_cns("123")
    with pytest.raises(ValidationError):
        validate_digits("12a")
    validate_digits("123")
