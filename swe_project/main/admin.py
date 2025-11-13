from django.contrib import admin
from .models import Item, Request, Category, Message

admin.site.register(Message)
admin.site.register(Item)
admin.site.register(Request)
admin.site.register(Category)
