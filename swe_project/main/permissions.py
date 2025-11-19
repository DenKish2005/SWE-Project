from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import Request as Link
from .models import Supplier, SupplierStaff, UserProfile

class IsAuthenticatedOrReadOnlyWrite(BasePermission):
    def has_permission(self, request, view):
        return True if request.method in SAFE_METHODS else request.user and request.user.is_authenticated

class IsSupplierManagerish(BasePermission):
    """Owner/Manager/Sales поставщика, указанного в объекте/параметрах."""
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        supplier = getattr(obj, "supplier", None)
        if supplier is None:
            return False
        is_owner = supplier.user_id == request.user.id
        in_staff = SupplierStaff.objects.filter(supplier=supplier, user=request.user).exists()
        return is_owner or in_staff


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
