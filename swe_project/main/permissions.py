from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.db.models import Q
from .models import Supplier, SupplierStaff, SupplierConsumerLink, Consumer

class IsAuthenticatedOrReadOnlyWrite(BasePermission):
    def has_permission(self, request, view):
        return True if request.method in SAFE_METHODS else bool(request.user and request.user.is_authenticated)

class IsSupplierManagerish(BasePermission):

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        supplier = getattr(obj, "supplier", None)
        if supplier is None:
            return False
        is_owner = supplier.user_id == request.user.id
        in_staff = SupplierStaff.objects.filter(supplier=supplier, user=request.user).exists()
        return is_owner or in_staff

class IsLinkParticipant(BasePermission):

    def _is_participant(self, user, link):
        if not user or not user.is_authenticated:
            return False
        is_consumer = (link.consumer.user_id == user.id)
        is_owner = (link.supplier.user_id == user.id)
        in_staff = SupplierStaff.objects.filter(supplier=link.supplier, user=user).exists()
        return is_consumer or is_owner or in_staff

    def has_permission(self, request, view):
        if view.action == "create":
            link_id = request.data.get("link")
            if not link_id:
                return False
            link = SupplierConsumerLink.objects.filter(id=link_id, status=SupplierConsumerLink.Status.APPROVED).first()
            return bool(link) and self._is_participant(request.user, link)
        return True

    def has_object_permission(self, request, view, obj):
        link = getattr(obj, "link", None)
        if not link:
            return False
        if link.status != SupplierConsumerLink.Status.APPROVED:
            return False
        return self._is_participant(request.user, link)

class IsChatAllowed(BasePermission):

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
