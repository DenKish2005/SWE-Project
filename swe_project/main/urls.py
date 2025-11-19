from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ItemViewSet, RequestViewSet, CategoryViewSet, MessageViewSet
from .views import SupplierViewSet, ConsumerViewSet, SupplierStaffViewSet
from .views import SupplierConsumerLinkViewSet, OrderViewSet, IncidentViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'items', ItemViewSet)
router.register(r'requests', RequestViewSet)
router.register(r'messages', MessageViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'consumers', ConsumerViewSet)
router.register(r'staff', SupplierStaffViewSet)
router.register(r'links', SupplierConsumerLinkViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'incidents', IncidentViewSet)
router.register(r'notifications', NotificationViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
