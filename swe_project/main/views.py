from rest_framework import viewsets
from .models import Item, Request
from .serializers import ItemSerializer, RequestSerializer

# ViewSets for CRUD
class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

class RequestViewSet(viewsets.ModelViewSet):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer