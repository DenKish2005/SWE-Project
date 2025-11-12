from django.db import models

class Item(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=500)
    price = models.FloatField()
    weight = models.FloatField()
    quantity = models.IntegerField()
    supplierID = models.IntegerField()

    def __str__(self):
        return self.name


class Request(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        APPROVED = "Approved", "Approved"
        REJECTED = "Rejected", "Rejected"

    consumerID = models.IntegerField()
    supplierID = models.IntegerField()
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.PENDING
    )
    requestDate = models.DateField(auto_now_add=True)
    consumerComment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.consumerID} → {self.supplierID} ({self.status})"
