from django.contrib import admin
from .models import Item, Request, Category, Message

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("id","name","supplierID","price","quantity","category")
    list_filter = ("category",)
    search_fields = ("name","description")

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ("id","consumerID","supplierID","status","requestDate")
    list_filter = ("status",)
    search_fields = ("consumerComment",)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id","request","senderType","created_at")
    list_filter = ("senderType",)
