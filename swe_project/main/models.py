from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Q, F
from django.utils import timezone
import uuid

# ---------- Пользовательские роли ----------
class UserProfile(models.Model):
    class Role(models.TextChoices):
        CONSUMER = "consumer", "Consumer"
        SUPPLIER_OWNER = "owner", "Owner"
        SUPPLIER_MANAGER = "manager", "Manager"
        SALES = "sales", "Sales"
        PLATFORM_ADMIN = "platform_admin", "Platform Admin" 

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=32, choices=Role.choices)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


# ---------- Справочники ----------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)      
    parent = models.ForeignKey('self', null=True, blank=True,
                               on_delete=models.SET_NULL)    
    is_moderated = models.BooleanField(default=True)    
    created_at = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return self.name


# ---------- Сущности домена ----------
class Supplier(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    company_name = models.CharField(max_length=255)
    city = models.CharField(max_length=100, blank=True)
    business_license = models.CharField(max_length=100, blank=True) 
    address = models.CharField(max_length=255, blank=True)       
    payment_method = models.CharField(max_length=50, blank=True)    
    created_at = models.DateTimeField(auto_now_add=True)     

    def __str__(self):
        return self.company_name


class Consumer(models.Model):
    class BusinessType(models.TextChoices):
        RESTAURANT = "restaurant", "Restaurant"
        HOTEL = "hotel", "Hotel"
        OTHER = "other", "Other"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=255, blank=True)
    business_type = models.CharField(max_length=20, choices=BusinessType.choices, default=BusinessType.OTHER)
    city = models.CharField(max_length=100, blank=True) 
    address = models.CharField(max_length=255, blank=True) 
    payment_method = models.CharField(max_length=50, blank=True)  

    def __str__(self):
        return self.business_name or f"Consumer#{self.pk}"


class SupplierStaff(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="staff")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=32, choices=UserProfile.Role.choices)

    def __str__(self):
        return f"{self.user.username} @ {self.supplier.company_name} ({self.role})"


class SupplierConsumerLink(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        APPROVED = "Approved", "Approved"
        REJECTED = "Rejected", "Rejected"
        BLOCKED = "Blocked", "Blocked"  
        REMOVED = "Removed", "Removed"  

    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, db_index=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            
            models.UniqueConstraint(
                fields=["consumer", "supplier", "status"],
                name="uniq_active_link",
                condition=Q(status__in=["Pending", "Approved"])
            ),
        ]

    def __str__(self):
        return f"{self.consumer_id}->{self.supplier_id} [{self.status}]"


class Item(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="items", db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    description = models.CharField(max_length=500, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    weight = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0)], default=0)
    quantity = models.PositiveIntegerField(default=0) 
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)

    
    unit = models.CharField(max_length=20, default="pcs")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    min_order_qty = models.PositiveIntegerField(default=1)
    stock_level = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["supplier", "name"], name="uniq_supplier_itemname"),
        ]

    def __str__(self):
        return self.name


class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = "Draft", "Draft"
        SUBMITTED = "Submitted", "Submitted"
        ACCEPTED = "Accepted", "Accepted"
        REJECTED = "Rejected", "Rejected"
        COMPLETED = "Completed", "Completed"

    class DeliveryType(models.TextChoices):
        PICKUP = "pickup", "Pickup"
        DELIVERY = "delivery", "Delivery"

    consumer = models.ForeignKey(Consumer, on_delete=models.PROTECT)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, null=True, blank=True)
    link = models.ForeignKey(SupplierConsumerLink, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED, db_index=True)

    order_number = models.CharField(max_length=32, unique=True, default="", blank=True) 
    delivery_type = models.CharField(max_length=20, choices=DeliveryType.choices, default=DeliveryType.DELIVERY) 
    delivery_address = models.TextField(blank=True) 
    notes = models.TextField(blank=True)   

    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    accepted_at = models.DateTimeField(null=True, blank=True)                  
    completed_at = models.DateTimeField(null=True, blank=True)          
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def ensure_number(self):
        if not self.order_number:
            self.order_number = f"O-{uuid.uuid4().hex[:10].upper()}"

    def recalc_total(self):
        total = sum(i.subtotal for i in self.items.all())
        self.total_amount = total

    def save(self, *args, **kwargs):
        self.ensure_number()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Item, on_delete=models.PROTECT)
    name_snapshot = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)     

    def save(self, *args, **kwargs):
        self.subtotal = (self.unit_price * self.quantity) - self.discount
        super().save(*args, **kwargs)


class Message(models.Model):
    class Sender(models.TextChoices):
        CONSUMER = "consumer", "Consumer"
        SALES = "sales", "Sales"
        MANAGER = "manager", "Manager"
        OWNER = "owner", "Owner"
        SYSTEM = "system", "System"

    order = models.ForeignKey('Order', null=True, blank=True, on_delete=models.SET_NULL)
    link = models.ForeignKey('SupplierConsumerLink', on_delete=models.CASCADE, db_index=True)
    sender_type = models.CharField(max_length=20, choices=Sender.choices)
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['link', 'created_at'])]

    def __str__(self):
        return f"{self.sender_type}: {self.text[:30]}"


class Attachment(models.Model): 
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="chat_attachments/")
    mime_type = models.CharField(max_length=100, blank=True)
    original_name = models.CharField(max_length=255, blank=True)
    size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Incident(models.Model):
    class Status(models.TextChoices):
        OPEN = "Open", "Open"
        RESOLVED = "Resolved", "Resolved"
        ESCALATED = "Escalated", "Escalated"
        CLOSED = "Closed", "Closed"

    class Type(models.TextChoices): 
        QUALITY = "quality", "Quality"
        DELIVERY = "delivery", "Delivery"
        BILLING = "billing", "Billing"
        OTHER = "other", "Other"

    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL)
    consumer = models.ForeignKey(Consumer, on_delete=models.PROTECT)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)

    type = models.CharField(max_length=20, choices=Type.choices, default=Type.OTHER) 
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=20, default="normal")
    description = models.TextField()
    resolution = models.TextField(blank=True)

    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reported_incidents", null=True)  # NEW
    assigned_to = models.ForeignKey(SupplierStaff, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_incidents") # NEW
    escalated_to = models.ForeignKey(SupplierStaff, on_delete=models.SET_NULL, null=True, blank=True, related_name="escalated_incidents")# NEW
    resolved_at = models.DateTimeField(null=True, blank=True) 

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Notification(models.Model):
    class Type(models.TextChoices):
        INFO = "info", "Info"
        LINK = "link", "Link changed"
        ORDER = "order", "Order changed"
        INCIDENT = "incident", "Incident changed"
        CHAT = "chat", "Chat message"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.INFO) 
    title = models.CharField(max_length=255)
    link_url = models.CharField(max_length=500, blank=True) 
    context = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    @staticmethod
    def create_for_order(order, title):
        Notification.objects.create(
            user=order.consumer.user, type=Notification.Type.ORDER,
            title=title, context={"order_id": order.id}
        )


# ---------- Platform Admin (опционально) ----------
class SupplierKYB(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    supplier = models.OneToOneField(Supplier, on_delete=models.CASCADE)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    document = models.FileField(upload_to="kyb_docs/", null=True, blank=True)
    comment = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)


# ---------- Аудит ----------
class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=64)
    target_type = models.CharField(max_length=64)
    target_id = models.CharField(max_length=64)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
