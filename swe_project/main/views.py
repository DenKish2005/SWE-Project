from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import (
    Item, Category, Message, Attachment,
    Supplier, Consumer, SupplierStaff, SupplierConsumerLink,
    Order, Incident, Notification, UserProfile, SupplierKYB
)
from .serializers import (
    ItemSerializer, CategorySerializer, MessageSerializer, AttachmentSerializer,
    SupplierSerializer, ConsumerSerializer, SupplierStaffSerializer,
    LinkSerializer, OrderSerializer, IncidentSerializer, NotificationSerializer
)
from .permissions import (
    IsAuthenticatedOrReadOnlyWrite, IsOwnerOrManagerOfSupplier, IsLinkParticipant,
    IsSalesOfSupplier, IsPlatformAdmin
)

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from .serializers import SupplierKYBSerializer

# ---- helpers ----
def my_suppliers_qs(user):
    if not user.is_authenticated:
        return Supplier.objects.none()
    return Supplier.objects.filter(Q(user=user) | Q(staff__user=user)).distinct()

def my_consumer(user):
    if not user.is_authenticated:
        return None
    return Consumer.objects.filter(user=user).first()

def system_chat(link, text, order=None):
    Message.objects.create(link=link, order=order, sender_type=Message.Sender.SYSTEM, text=text)

def notify(user, ntype, title, link_url="", ctx=None):
    Notification.objects.create(user=user, type=ntype, title=title, link_url=link_url, context=(ctx or {}))

# ---- Categories ----
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

# ---- Items (видимость завязана на Link) ----
class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['price', 'weight', 'created_at']
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
                    consumer=cons, status=SupplierConsumerLink.Status.APPROVED
                ).values_list('supplier_id', flat=True)
                qs = qs.filter(supplier_id__in=approved_supplier_ids)

        
        category_id = self.request.query_params.get('category')
        supplier_id = self.request.query_params.get('supplier')
        is_available = self.request.query_params.get('is_available')
        if category_id: qs = qs.filter(category_id=category_id)
        if supplier_id: qs = qs.filter(supplier_id=supplier_id)
        if is_available is not None: qs = qs.filter(is_available=is_available.lower()=="true")
        return qs
    
    def perform_create(self, serializer):
        supplier = serializer.validated_data.get("supplier")
        if supplier not in list(my_suppliers_qs(self.request.user)):
            raise PermissionDenied("You can create items only for your supplier.")
        serializer.save()

    def perform_update(self, serializer):
        if self.get_object().supplier not in list(my_suppliers_qs(self.request.user)):
            raise PermissionDenied("Forbidden")
        serializer.save()

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

# ---- Links (approve/reject/block/remove) ----
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
        link.approved_at = timezone.now()
        link.save(update_fields=["status", "approved_at"])
        system_chat(link, "Link approved")
        notify(link.consumer.user, Notification.Type.LINK, "Link approved", ctx={"link_id": link.id})
        return Response({"status": link.status})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        link = self.get_object()
        if link.supplier not in list(my_suppliers_qs(request.user)):
            return Response({"detail": "Only supplier side can reject."}, status=403)
        link.status = SupplierConsumerLink.Status.REJECTED
        link.rejected_at = timezone.now()
        link.save(update_fields=["status", "rejected_at"])
        system_chat(link, "Link rejected")
        notify(link.consumer.user, Notification.Type.LINK, "Link rejected", ctx={"link_id": link.id})
        return Response({"status": link.status})

    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        link = self.get_object()
        if link.supplier not in list(my_suppliers_qs(request.user)):
            return Response({"detail": "Only supplier side can block."}, status=403)
        link.status = SupplierConsumerLink.Status.BLOCKED
        link.save(update_fields=["status"])
        system_chat(link, "Link blocked")
        return Response({"status": link.status})

    @action(detail=True, methods=['post'])
    def remove(self, request, pk=None):
        link = self.get_object()
        if link.supplier not in list(my_suppliers_qs(request.user)):
            return Response({"detail": "Only supplier side can remove."}, status=403)
        link.status = SupplierConsumerLink.Status.REMOVED
        link.save(update_fields=["status"])
        system_chat(link, "Link removed")
        return Response({"status": link.status})

# ---- Chat + Attachments ----
class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
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
        if link_id: qs = qs.filter(link_id=link_id)
        return qs

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser])
    def attachments(self, request, pk=None):
        msg = self.get_object()
        file = request.FILES["file"]
        att = Attachment.objects.create(
            message=msg, file=file, original_name=file.name, size=file.size, mime_type=file.content_type or ""
        )
        return Response(AttachmentSerializer(att).data, status=201)

# ---- Orders ----
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related("consumer","supplier").prefetch_related("items")
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_staff or user.is_superuser:
            return qs
        sup_qs = my_suppliers_qs(user)
        if sup_qs.exists():
            return qs.filter(supplier__in=sup_qs)
        cons = my_consumer(user)
        if cons:
            return qs.filter(consumer=cons)
        return qs.none()

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        order = self.get_object()
        if order.supplier not in list(my_suppliers_qs(request.user)) and not request.user.is_staff:
            return Response({"detail": "Forbidden"}, status=403)
        with transaction.atomic():
            
            for it in order.items.select_related("product"):
                Item.objects.filter(pk=it.product_id, stock_level__gte=it.quantity)\
                    .update(stock_level=F('stock_level') - it.quantity)
            order.status = Order.Status.ACCEPTED
            order.accepted_at = timezone.now()
            order.save(update_fields=["status", "accepted_at"])
        notify(order.consumer.user, Notification.Type.ORDER, "Order accepted", ctx={"order_id": order.id})
        system_chat(order.link, f"Order {order.order_number} accepted", order=order)
        return Response({"status": order.status})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        order = self.get_object()
        if order.supplier not in list(my_suppliers_qs(request.user)) and not request.user.is_staff:
            return Response({"detail": "Forbidden"}, status=403)
        order.status = Order.Status.REJECTED
        order.save(update_fields=["status"])
        notify(order.consumer.user, Notification.Type.ORDER, "Order rejected", ctx={"order_id": order.id})
        system_chat(order.link, f"Order {order.order_number} rejected", order=order)
        return Response({"status": order.status})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        order = self.get_object()
        if order.supplier not in list(my_suppliers_qs(request.user)) and not request.user.is_staff:
            return Response({"detail": "Forbidden"}, status=403)
        order.status = Order.Status.COMPLETED
        order.completed_at = timezone.now()
        order.save(update_fields=["status", "completed_at"])
        notify(order.consumer.user, Notification.Type.ORDER, "Order completed", ctx={"order_id": order.id})
        system_chat(order.link, f"Order {order.order_number} completed", order=order)
        return Response({"status": order.status})

# ---- Incidents ----
class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_staff or user.is_superuser:
            return qs
        sup_qs = my_suppliers_qs(user)
        if sup_qs.exists():
            return qs.filter(supplier__in=sup_qs)
        cons = my_consumer(user)
        if cons:
            return qs.filter(consumer=cons)
        return qs.none()

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        inc = self.get_object()
        inc.status = Incident.Status.RESOLVED
        inc.resolved_at = timezone.now()
        inc.resolution = request.data.get("resolution", inc.resolution)
        inc.save(update_fields=["status","resolved_at","resolution"])

        link = inc.order.link if inc.order_id else SupplierConsumerLink.objects.filter(
            consumer=inc.consumer, supplier=inc.supplier, status=SupplierConsumerLink.Status.APPROVED
        ).first()
        if link:
            system_chat(link, "Incident resolved")
        notify(inc.consumer.user, Notification.Type.INCIDENT, "Incident resolved", ctx={"incident_id": inc.id})
        return Response({"status": inc.status})

    @action(detail=True, methods=["post"])
    def escalate(self, request, pk=None):
        inc = self.get_object()
        inc.status = Incident.Status.ESCALATED
        inc.save(update_fields=["status"])
        link = inc.order.link if inc.order_id else SupplierConsumerLink.objects.filter(
            consumer=inc.consumer, supplier=inc.supplier, status=SupplierConsumerLink.Status.APPROVED
        ).first()
        if link:
            system_chat(link, "Incident escalated")
        notify(inc.consumer.user, Notification.Type.INCIDENT, "Incident escalated", ctx={"incident_id": inc.id})
        return Response({"status": inc.status})

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        inc = self.get_object()
        staff_id = request.data.get("staff_id")
        staff = SupplierStaff.objects.filter(pk=staff_id, supplier=inc.supplier).first()
        if not staff:
            return Response({"detail": "Staff not found or not in supplier"}, status=400)
        inc.assigned_to = staff
        inc.save(update_fields=["assigned_to"])
        return Response({"assigned_to": staff_id})

# ---- Notifications ----
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        n = self.get_object()
        n.is_read = True
        n.read_at = timezone.now()
        n.save(update_fields=["is_read", "read_at"])
        return Response({"status": "ok"})

# ---- Platform Admin (опционально) ----
class KYBViewSet(viewsets.ModelViewSet):
    queryset = SupplierKYB.objects.all()
    serializer_class = SupplierKYBSerializer
    permission_classes = [IsPlatformAdmin]

