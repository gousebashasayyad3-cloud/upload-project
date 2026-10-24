from django.db import transaction

from .models import AuditEvent


@transaction.atomic
def record_audit(
    *,
    actor,
    action,
    result,
    document=None,
    details=None,
):
    """
    Record an audit event and link it to the previous event.

    Call this function from security-sensitive application operations.
    """

    previous = (
        AuditEvent.objects
        .select_for_update()
        .order_by("-timestamp", "-id")
        .first()
    )

    previous_hash = previous.event_hash if previous else ""

    event = AuditEvent(
        actor=actor if getattr(actor, "is_authenticated", False)
        else None,
        document=document,
        action=action,
        result=result,
        details=details or {},
        previous_hash=previous_hash,
    )

    event.event_hash = event.calculate_hash()

    event.save(force_insert=True)

    return event