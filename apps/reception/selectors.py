from django.db.models import Case, IntegerField, QuerySet, Value, When

from apps.core.models import User
from apps.core.permissions import Role

from .models import CareSession, Triage

Status = CareSession.Status

RISK_ORDER = Case(
    When(triage__risk=Triage.Risk.VERY_HIGH, then=Value(0)),
    When(triage__risk=Triage.Risk.HIGH, then=Value(1)),
    When(triage__risk=Triage.Risk.MEDIUM, then=Value(2)),
    default=Value(3),
    output_field=IntegerField(),
)


def sessions_with_status(status: str) -> QuerySet[CareSession]:
    return (
        CareSession.objects.filter(status=status)
        .select_related("patient", "triage")
        .order_by("arrived_at")
    )


def triage_queue() -> QuerySet[CareSession]:
    return sessions_with_status(Status.AWAITING_TRIAGE)


def consultation_queue() -> QuerySet[CareSession]:
    """Mais grave primeiro; no mesmo risco, quem chegou antes."""
    return (
        sessions_with_status(Status.AWAITING_CONSULTATION)
        .annotate(risk_order=RISK_ORDER)
        .order_by("risk_order", "arrived_at")
    )


def physicians() -> QuerySet[User]:
    return (
        User.objects.filter(is_active=True, groups__name=Role.PHYSICIAN)
        .distinct()
        .order_by("full_name", "username")
    )
