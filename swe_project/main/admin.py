from django.contrib import admin
from .models import Item, Category, Message, Attachment, Supplier, Consumer, SupplierStaff, SupplierConsumerLink, Order, OrderItem, Incident, Notification, SupplierKYB

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "supplier", "price", "stock_level", "category", "is_available")
    list_filter = ("category", "is_available")
    search_fields = ("name", "description")

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent", "is_moderated", "created_at")
    search_fields = ("name",)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "link", "order", "sender_type", "created_at")
    list_filter = ("sender_type",)

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "mime_type", "size", "created_at")

admin.site.register((Supplier, Consumer, SupplierStaff, SupplierConsumerLink, 
                     Order, OrderItem, Incident, Notification, SupplierKYB))
