from rest_framework import viewsets
from rest_framework import filters
from .models import Item, Request, Category
from .serializers import ItemSerializer, RequestSerializer, CategorySerializer
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['price', 'weight']
    search_fields = ['name', 'description']

class RequestViewSet(viewsets.ModelViewSet):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        req = self.get_object()
        req.status = "Approved"
        req.save()
        return Response({"message": "Request approved."})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        req = self.get_object()
        req.status = "Rejected"
        req.save()
        return Response({"message": "Request rejected."})

