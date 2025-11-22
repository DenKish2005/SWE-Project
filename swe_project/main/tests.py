from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase
from .models import Category, Item, Request as Link
from .models import Supplier, Consumer, SupplierConsumerLink, Item, Category

class VisibilityTests(APITestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Food")
        self.supp_user = User.objects.create_user(username="supp", password="p")
        self.cons_user = User.objects.create_user(username="cons", password="p")
        self.supplier = Supplier.objects.create(user=self.supp_user, company_name="Acme")
        self.consumer = Consumer.objects.create(user=self.cons_user, business_name="Cafe")
        self.item = Item.objects.create(supplier=self.supplier, name="Sugar", description="1kg",
                                        price="100.00", weight="1.000", quantity=10, category=self.cat)

        self.client_cons = APIClient(); self.client_cons.login(username="cons", password="p")
        self.client_supp = APIClient(); self.client_supp.login(username="supp", password="p")

    def test_consumer_sees_items_only_after_approval(self):
        
        r = self.client_cons.get("/api/items/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["count"], 0)

        
        link = SupplierConsumerLink.objects.create(consumer=self.consumer, supplier=self.supplier)
        r = self.client_cons.get("/api/items/")
        self.assertEqual(r.json()["count"], 0)

        
        link.status = SupplierConsumerLink.Status.APPROVED
        link.save()
        r = self.client_cons.get("/api/items/")
        self.assertEqual(r.json()["count"], 1)

    def test_supplier_staff_sees_own_items(self):
        r = self.client_supp.get("/api/items/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["count"], 1)



class APISmokeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.cat = Category.objects.create(name="Fish")
        self.item = Item.objects.create(
            name="Salmon", description="Atlantic", price="2500.00",
            weight="1.000", quantity=50, supplierID=1, category=self.cat
        )
        self.link = Link.objects.create(consumerID=10, supplierID=1, status=Link.Status.APPROVED)

    def test_items_list(self):
        r = self.client.get("/api/items/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(len(r.json()["results"]) >= 1)

    def test_suppliers_by_name(self):
        r = self.client.get("/api/items/suppliers-by-name/", {"name":"sal"})
        self.assertEqual(r.status_code, 200)
        self.assertIn(1, r.json()["suppliers"])

    def test_chat_allowed_only_if_approved(self):
        self.link.status = Link.Status.PENDING
        self.link.save()
        r = self.client.post("/api/messages/", {
            "request": self.link.id, "senderType":"consumer", "text":"hi"
        }, format="json")
        self.assertEqual(r.status_code, 400)

        self.link.status = Link.Status.APPROVED
        self.link.save()
        r = self.client.post("/api/messages/", {
            "request": self.link.id, "senderType":"consumer", "text":"hi"
        }, format="json")
        self.assertEqual(r.status_code, 201)
