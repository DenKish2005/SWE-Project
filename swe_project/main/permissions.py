from rest_framework.permissions import BasePermission
from .models import Request as Link

class IsChatAllowed(BasePermission):
    """
    Разрешает создавать сообщения только если линк Approved.
    """
    def has_permission(self, request, view):
        if view.action != "create":
            return True
        req_id = request.data.get("request")
        if not req_id:
            return False
        try:
            link = Link.objects.get(id=req_id)
        except Link.DoesNotExist:
            return False
        return link.status == Link.Status.APPROVED
