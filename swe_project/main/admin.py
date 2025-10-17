from django.contrib import admin
from .models import Item, Request

admin.site.register(Item)
admin.site.register(Request)