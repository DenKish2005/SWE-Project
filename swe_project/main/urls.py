from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ItemViewSet, RequestViewSet, CategoryViewSet, MessageViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'items', ItemViewSet)
router.register(r'requests', RequestViewSet)
router.register(r'messages', MessageViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
