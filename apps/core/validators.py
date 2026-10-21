import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def only_digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def is_valid_cpf(value: str) -> bool:
    cpf = only_digits(value)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for size in (9, 10):
        total = sum(
            int(digit) * weight
            for digit, weight in zip(cpf[:size], range(size + 1, 1, -1), strict=True)
        )
        check = (total * 10) % 11 % 10
        if check != int(cpf[size]):
            return False
    return True


def is_valid_cns(value: str) -> bool:
    """CNS tem 15 dígitos; a soma ponderada (pesos 15 a 1) deve ser múltipla de 11."""
    cns = only_digits(value)
    if len(cns) != 15 or cns[0] not in "12789":
        return False
    total = sum(int(digit) * weight for digit, weight in zip(cns, range(15, 0, -1), strict=True))
    return total % 11 == 0


def validate_cpf(value: str) -> None:
    if not is_valid_cpf(value):
        raise ValidationError(_("CPF inválido."), code="invalid_cpf")


def validate_cns(value: str) -> None:
    if not is_valid_cns(value):
        raise ValidationError(_("CNS inválido."), code="invalid_cns")


def validate_digits(value: str) -> None:
    if not value.isdigit():
        raise ValidationError(_("Use apenas números."), code="not_digits")
