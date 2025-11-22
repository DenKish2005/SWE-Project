from .models import AuditLog
def audit(user, action, obj, payload=None):
    AuditLog.objects.create(
        user=user, action=action,
        target_type=obj.__class__.__name__, target_id=str(obj.pk),
        payload=payload or {}
    )