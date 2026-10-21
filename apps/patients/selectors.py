import re

from django.db.models import QuerySet

from apps.core.validators import only_digits

from .models import Patient

SEARCH_LIMIT = 20


def search_patients(query: str, mother: str = "") -> QuerySet[Patient]:
    """CNS (15 dígitos), CPF (11) ou prontuário, com ou sem máscara; senão nome e mãe sem acento.

    O lookup `unaccent` vem de `django.contrib.postgres`.
    """
    query = (query or "").strip()
    mother = (mother or "").strip()
    patients = Patient.objects.select_related("municipality")
    if re.fullmatch(r"[\d.\-\s]+", query):
        digits = only_digits(query)
        if len(digits) == 15:
            return patients.filter(cns=digits)
        if len(digits) == 11:
            return patients.filter(cpf=digits)
        return patients.filter(medical_record_number=digits)
    if not query and not mother:
        return patients.none()
    if query:
        patients = patients.filter(name__unaccent__icontains=query)
    if mother:
        patients = patients.filter(mother_name__unaccent__icontains=mother)
    return patients.order_by("name")[:SEARCH_LIMIT]
