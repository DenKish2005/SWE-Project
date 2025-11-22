from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.db.models import Q
from .models import Supplier, SupplierStaff, SupplierConsumerLink, Consumer, UserProfile

class IsAuthenticatedOrReadOnlyWrite(BasePermission):
    def has_permission(self, request, view):
        return True if request.method in SAFE_METHODS else bool(request.user and request.user.is_authenticated)

def _my_suppliers(user):
    if not user or not user.is_authenticated:
        return Supplier.objects.none()
    return Supplier.objects.filter(user=user).union(
        Supplier.objects.filter(staff__user=user)
    ).distinct()

class IsOwnerOrManagerOfSupplier(BasePermission):
    def has_object_permission(self, request, view, obj):
        supplier = getattr(obj, "supplier", None)
        if supplier is None or not request.user.is_authenticated:
            return False
        if supplier.user_id == request.user.id:
            return True
        return SupplierStaff.objects.filter(supplier=supplier, user=request.user,
                                            role__in=[UserProfile.Role.SUPPLIER_MANAGER, UserProfile.Role.SALES, UserProfile.Role.SUPPLIER_OWNER]).exists()

class IsSalesOfSupplier(BasePermission):
    def has_object_permission(self, request, view, obj):
        supplier = getattr(obj, "supplier", None)
        if supplier is None:
            return False
        return SupplierStaff.objects.filter(supplier=supplier, user=request.user,
                                            role__in=[UserProfile.Role.SALES, UserProfile.Role.SUPPLIER_MANAGER, UserProfile.Role.SUPPLIER_OWNER]).exists()

class IsPlatformAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return UserProfile.objects.filter(user=request.user, role=UserProfile.Role.PLATFORM_ADMIN).exists() or bool(request.user.is_staff)

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
        if not link or link.status != SupplierConsumerLink.Status.APPROVED:
            return False
        return self._is_participant(request.user, link)

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
