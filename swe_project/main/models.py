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
    consumerID = models.IntegerField()
    supplierID = models.IntegerField()
    status = models.CharField(max_length=50)
    requestDate = models.DateField(auto_now_add=True)
    consumerComment = models.TextField()

    def __str__(self):
        return f"{self.consumerID} → {self.supplierID} ({self.status})"