from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class Item(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    description = models.CharField(max_length=500)
    price = models.DecimalField(max_digits=12, decimal_places=2,
                                validators=[MinValueValidator(0)])
    weight = models.DecimalField(max_digits=10, decimal_places=3,
                                 validators=[MinValueValidator(0)])
    quantity = models.PositiveIntegerField()
    supplierID = models.IntegerField(db_index=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,
                                 null=True, blank=True, db_index=True)

    def __str__(self): return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['supplierID', 'name'],
                name='uniq_supplier_itemname'
            ),
        ]

class Request(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        APPROVED = "Approved", "Approved"
        REJECTED = "Rejected", "Rejected"

    consumerID = models.IntegerField(db_index=True)
    supplierID = models.IntegerField(db_index=True)
    status = models.CharField(max_length=50, choices=Status.choices,
                              default=Status.PENDING, db_index=True)
    requestDate = models.DateField(auto_now_add=True)
    consumerComment = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['consumerID', 'supplierID', 'status'],
                name='uniq_cons_sup_status_active',
                condition=Q(status__in=['Pending', 'Approved'])
            ),
        ]
        indexes = [
            models.Index(fields=['consumerID', 'supplierID']),
        ]

    def __str__(self):
        return f"{self.consumerID} → {self.supplierID} ({self.status})"

class Message(models.Model):
    link = models.ForeignKey(SupplierConsumerLink, on_delete=models.CASCADE, db_index=True)
    senderType = models.CharField(max_length=20) 
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['request', 'created_at'])]

    def __str__(self): return f"{self.senderType}: {self.text[:30]}"

class UserProfile(models.Model):
    class Role(models.TextChoices):
        CONSUMER = "consumer", "Consumer"
        SUPPLIER_OWNER = "owner", "Owner"
        SUPPLIER_MANAGER = "manager", "Manager"
        SALES = "sales", "Sales"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices)

class Supplier(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # владелец
    company_name = models.CharField(max_length=255)
    city = models.CharField(max_length=100, blank=True)

class Consumer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=255, blank=True)

class SupplierStaff(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="staff")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=UserProfile.Role.choices)

class SupplierConsumerLink(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        APPROVED = "Approved", "Approved"
        REJECTED = "Rejected", "Rejected"

    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, db_index=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['consumer', 'supplier', 'status'],
                name='uniq_active_link',
                condition=Q(status__in=['Pending', 'Approved'])
            ),
        ]
