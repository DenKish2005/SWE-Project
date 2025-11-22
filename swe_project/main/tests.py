from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase
from .models import Category, Item, Supplier, Consumer, SupplierConsumerLink, Message

class VisibilityTests(APITestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Food")
        self.supp_user = User.objects.create_user(username="supp", password="p")
        self.cons_user = User.objects.create_user(username="cons", password="p")
        self.supplier = Supplier.objects.create(user=self.supp_user, company_name="Acme")
        self.consumer = Consumer.objects.create(user=self.cons_user, business_name="Cafe")
        self.item = Item.objects.create(supplier=self.supplier, name="Sugar", description="1kg",
                                        price="100.00", weight="1.000", stock_level=10, category=self.cat)

        self.client_cons = APIClient(); self.client_cons.login(username="cons", password="p")
        self.client_supp = APIClient(); self.client_supp.login(username="supp", password="p")

    def test_consumer_sees_items_only_after_approval(self):
        r = self.client_cons.get("/api/items/")
        self.assertEqual(r.json()["count"], 0)

        link = SupplierConsumerLink.objects.create(consumer=self.consumer, supplier=self.supplier)  # Pending
        r = self.client_cons.get("/api/items/"); self.assertEqual(r.json()["count"], 0)

        link.status = SupplierConsumerLink.Status.APPROVED; link.save()
        r = self.client_cons.get("/api/items/"); self.assertEqual(r.json()["count"], 1)

    def test_chat_disallowed_until_approved(self):
        link = SupplierConsumerLink.objects.create(consumer=self.consumer, supplier=self.supplier)  # Pending
        r = self.client_cons.post("/api/messages/", {"link": link.id, "sender_type":"consumer", "text":"hi"}, format="json")
        self.assertEqual(r.status_code, 403)

        link.status = SupplierConsumerLink.Status.APPROVED; link.save()
        r = self.client_cons.post("/api/messages/", {"link": link.id, "sender_type":"consumer", "text":"hi"}, format="json")
        self.assertEqual(r.status_code, 201)



