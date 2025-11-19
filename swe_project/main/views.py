from rest_framework import viewsets
from rest_framework import filters
from .models import Item, Request, Category, Message
from .serializers import ItemSerializer, RequestSerializer, CategorySerializer, MessageSerializer
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .permissions import IsChatAllowed
from rest_framework import permissions

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all().order_by('created_at')
    serializer_class = MessageSerializer
    permission_classes = [permissions.AllowAny, IsChatAllowed]
    filter_backends = [filters.OrderingFilter]
    ordering = ['created_at']

    def create(self, request, *args, **kwargs):
        request_id = request.data.get("request")
        if not request_id:
            return Response({"error": "request field is required"}, status=400)
        try:
            req = Request.objects.get(id=request_id)
        except Request.DoesNotExist:
            return Response({"error": "Request not found"}, status=404)
        if req.status != Request.Status.APPROVED:
            return Response({"error": "Chat allowed only for Approved requests"}, status=400)
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        rid = self.request.query_params.get('request')
        if rid:
            qs = qs.filter(request_id=rid)
        return qs


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['price', 'weight']
    search_fields = ['name', 'description']

    def get_queryset(self):
        qs = super().get_queryset()
        category_id = self.request.query_params.get('category')
        supplier_id = self.request.query_params.get('supplier')
        if category_id:
            qs = qs.filter(category_id=category_id)
        if supplier_id:
            qs = qs.filter(supplierID=supplier_id)
        return qs
    
    @action(detail=False, methods=['get'], url_path='suppliers-by-name')
    def suppliers_by_name(self, request):
        name = request.query_params.get('name')
        if not name:
            return Response({"error": "name query param is required"}, status=400)

        items = (
            Item.objects
            .filter(name__icontains=name)
            .values('supplierID')
            .distinct()
        )
        suppliers = [row['supplierID'] for row in items]
        return Response({"suppliers": suppliers})


class RequestViewSet(viewsets.ModelViewSet):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer

    def perform_create(self, serializer):
        serializer.save(status=Request.Status.PENDING)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        req = self.get_object()
        req.status = Request.Status.APPROVED
        req.save()
        return Response({"message": "Request approved."})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        req = self.get_object()
        req.status = Request.Status.REJECTED
        req.save()
        return Response({"message": "Request rejected."})

