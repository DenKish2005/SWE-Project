from django.db.models import Q
from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Item, Category, Message,
    Supplier, Consumer, SupplierStaff, SupplierConsumerLink,
    Order, Incident, Notification
)
from .serializers import (
    ItemSerializer, CategorySerializer, MessageSerializer,
    SupplierSerializer, ConsumerSerializer, SupplierStaffSerializer,
    LinkSerializer, OrderSerializer, IncidentSerializer, NotificationSerializer
)
from .permissions import IsAuthenticatedOrReadOnlyWrite, IsSupplierManagerish, IsLinkParticipant

# ---- helpers ----
def my_suppliers_qs(user):
    if not user.is_authenticated:
        return Supplier.objects.none()
    return Supplier.objects.filter(Q(user=user) | Q(staff__user=user)).distinct()

def my_consumer(user):
    if not user.is_authenticated:
        return None
    return Consumer.objects.filter(user=user).first()


# ---- Categories ----
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# ---- Items (видимость завязана на Link) ----
class ItemViewSet(viewsets.ModelViewSet):
    serializer_class = ItemSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['price', 'weight']
    search_fields = ['name', 'description']
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Item.objects.select_related("supplier", "category")

        if user.is_staff or user.is_superuser:
            pass 
        else:
            suppliers_for_me = my_suppliers_qs(user)
            if suppliers_for_me.exists():
                
                qs = qs.filter(supplier__in=suppliers_for_me)
            else:
                
                cons = my_consumer(user)
                if not cons:
                    return Item.objects.none()
                approved_supplier_ids = SupplierConsumerLink.objects.filter(
                    consumer=cons,
                    status=SupplierConsumerLink.Status.APPROVED
                ).values_list('supplier_id', flat=True)
                qs = qs.filter(supplier_id__in=approved_supplier_ids)

        
        category_id = self.request.query_params.get('category')
        supplier_id = self.request.query_params.get('supplier')
        if category_id:
            qs = qs.filter(category_id=category_id)
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)
        return qs

    def perform_create(self, serializer):
        
        user = self.request.user
        supplier = serializer.validated_data.get("supplier")
        if supplier not in list(my_suppliers_qs(user)):
            return Response({"detail": "You can create items only for your supplier."},
                            status=status.HTTP_403_FORBIDDEN)
        obj = serializer.save()
        
        if hasattr(obj, "supplierID"):
            obj.supplierID = obj.supplier_id
            obj.save(update_fields=["supplierID"])

    def perform_update(self, serializer):
        
        instance = self.get_object()
        if instance.supplier not in list(my_suppliers_qs(self.request.user)):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        obj = serializer.save()
        if hasattr(obj, "supplierID"):
            obj.supplierID = obj.supplier_id
            obj.save(update_fields=["supplierID"])


# ---- Supplier/Consumer/Staff ----
class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return super().get_queryset()
        return my_suppliers_qs(user)

class ConsumerViewSet(viewsets.ModelViewSet):
    queryset = Consumer.objects.all()
    serializer_class = ConsumerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return super().get_queryset()
        return Consumer.objects.filter(user=user)

class SupplierStaffViewSet(viewsets.ModelViewSet):
    queryset = SupplierStaff.objects.all()
    serializer_class = SupplierStaffSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return super().get_queryset()
        
        return SupplierStaff.objects.filter(supplier__in=my_suppliers_qs(user))


# ---- Links (approve/reject) ----
class SupplierConsumerLinkViewSet(viewsets.ModelViewSet):
    queryset = SupplierConsumerLink.objects.all()
    serializer_class = LinkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return super().get_queryset()
        return SupplierConsumerLink.objects.filter(
            Q(consumer__user=user) | Q(supplier__in=my_suppliers_qs(user))
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        link = self.get_object()
        
        if link.supplier not in list(my_suppliers_qs(request.user)):
            return Response({"detail": "Only supplier side can approve."}, status=403)
        link.status = SupplierConsumerLink.Status.APPROVED
        link.save(update_fields=["status"])
        return Response({"status": link.status})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        link = self.get_object()
        if link.supplier not in list(my_suppliers_qs(request.user)):
            return Response({"detail": "Only supplier side can reject."}, status=403)
        link.status = SupplierConsumerLink.Status.REJECTED
        link.save(update_fields=["status"])
        return Response({"status": link.status})


# ---- Chat ----
class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsLinkParticipant]
    filter_backends = [filters.OrderingFilter]
    ordering = ['created_at']

    def get_queryset(self):
        user = self.request.user
        qs = Message.objects.select_related("link", "link__supplier", "link__consumer")

        if user.is_staff or user.is_superuser:
            pass
        else:
            sup_qs = my_suppliers_qs(user)
            if sup_qs.exists():
                qs = qs.filter(link__supplier__in=sup_qs, link__status=SupplierConsumerLink.Status.APPROVED)
            else:
                cons = my_consumer(user)
                if not cons:
                    return Message.objects.none()
                qs = qs.filter(link__consumer=cons, link__status=SupplierConsumerLink.Status.APPROVED)

        
        link_id = self.request.query_params.get("link")
        if link_id:
            qs = qs.filter(link_id=link_id)
        return qs


# ---- Orders / Incidents / Notifications ----
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related("consumer","supplier").prefetch_related("items")
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        order = self.get_object()
        
        if order.supplier not in list(my_suppliers_qs(request.user)) and not request.user.is_staff:
            return Response({"detail":"Forbidden"}, status=403)
        order.status = Order.Status.ACCEPTED
        order.save(update_fields=["status"])
        Notification.create_for_order(order, "Order accepted")
        return Response({"status": order.status})

class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated]

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
