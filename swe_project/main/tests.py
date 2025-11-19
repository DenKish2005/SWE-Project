from django.test import TestCase
from rest_framework.test import APIClient
from .models import Category, Item, Request as Link

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
