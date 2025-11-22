from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ItemViewSet, CategoryViewSet, MessageViewSet,
    SupplierViewSet, ConsumerViewSet, SupplierStaffViewSet,
    SupplierConsumerLinkViewSet, OrderViewSet, IncidentViewSet, NotificationViewSet,
    KYBViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'items', ItemViewSet)
router.register(r'messages', MessageViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'consumers', ConsumerViewSet)
router.register(r'staff', SupplierStaffViewSet)
router.register(r'links', SupplierConsumerLinkViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'incidents', IncidentViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'platadmin/kyb', KYBViewSet)

urlpatterns = [ path('', include(router.urls)), ]
