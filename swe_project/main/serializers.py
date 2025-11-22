from rest_framework import serializers
from .models import (
    Supplier, Consumer, SupplierStaff, SupplierConsumerLink, Category, Item,
    Order, OrderItem, Incident, Notification, Message, Attachment
)

class SupplierKYBSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierKYB
        fields = "__all__"

# ---- Category / Item ----
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = "__all__"

# ---- Link / Staff / Parties ----
class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"

class ConsumerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consumer
        fields = "__all__"

class SupplierStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierStaff
        fields = "__all__"

class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierConsumerLink
        fields = "__all__"

# ---- Orders ----
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ("id", "product", "name_snapshot", "unit_price", "quantity", "discount", "subtotal")
        read_only_fields = ("subtotal",)

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ("order_number","total_amount","accepted_at","completed_at")

    def validate(self, data):
        link = data["link"]
        if link.status != SupplierConsumerLink.Status.APPROVED:
            raise serializers.ValidationError("Link must be APPROVED.")
        if data["consumer"].id != link.consumer_id or data["supplier"].id != link.supplier_id:
            raise serializers.ValidationError("Order consumer/supplier must match link parties.")
        return data

    def create(self, validated):
        items_data = validated.pop("items", [])
        with transaction.atomic():
            order = Order.objects.create(**validated)
            for it in items_data:
                product = it["product"]
                if product.supplier_id != order.supplier_id:
                    raise serializers.ValidationError("Product does not belong to supplier.")
                if it["quantity"] < product.min_order_qty:
                    raise serializers.ValidationError(f"Quantity for {product.name} less than min_order_qty.")
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    name_snapshot=product.name,
                    unit_price=product.price,
                    quantity=it["quantity"],
                    discount=it.get("discount", 0),
                    subtotal=0,
                )
            order.refresh_from_db()
            order.recalc_total()
            order.save(update_fields=["total_amount"])
        return order

# ---- Incidents ----
class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = "__all__"

# ---- Notifications ----
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"

# ---- Chat ----
class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = "__all__"

class MessageSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)
    class Meta:
        model = Message
        fields = "__all__"

