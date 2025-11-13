┌──────────────────────────────────────────────────────────────────────────────┐
│ SUPPLIER–CONSUMER BACKEND — HOW TO USE (console guide for humans)            │
│ Stack: Django 5 + Django REST Framework + PostgreSQL + Docker                │
└──────────────────────────────────────────────────────────────────────────────┘
NOTE: Some earlier uploaded docs (SRS/summary) expired on the server. If you want
me to use them again, just re-upload. This guide covers ONLY your current backend.

===============================================================================
1) RUNNING THE PROJECT
===============================================================================
# from the project root (where docker-compose.yml lives)
docker compose up --build

• API will be at:       http://localhost:8000/api/
• Admin panel:          http://localhost:8000/admin/
• Default DB:           Postgres (container "postgres_db")

Create admin user (first time only):
docker exec -it django_web bash
python swe_project/manage.py createsuperuser
exit

Stop everything:
docker compose down

===============================================================================
2) WHAT THIS BACKEND DOES (plain language)
===============================================================================
• Categories — simple list of product groups (e.g., Fish, Meat).
• Items — products. Each item has name/description/price/weight/quantity,
  supplierID (number), and optional category.
• Friend Requests — a Consumer sends a request to a Supplier (like “let’s connect”).
  Supplier approves or rejects. Statuses: Pending → Approved / Rejected.
• Chat — works ONLY when a request is Approved. Messages are tied to a request.

No login/RBAC yet (open API). It’s intentionally simple for learning and demos.

===============================================================================
3) DATA MODELS (short)
===============================================================================
Category:
  { id, name (unique) }

Item:
  { id, name, description, price, weight, quantity, supplierID, category (id|null) }

Request:
  { id, consumerID, supplierID, status: "Pending"|"Approved"|"Rejected",
    requestDate (auto), consumerComment (optional) }

Message:
  { id, request (id, must exist & be Approved to post), senderType: "consumer"|"supplier",
    text, created_at }

===============================================================================
4) ENDPOINTS (with examples you can paste)
===============================================================================
Base URL prefix for everything below:  http://localhost:8000/api/

──────────────────────────────── Categories
GET    /categories/                      → list
POST   /categories/                      → create
GET    /categories/{id}/                 → details
PATCH  /categories/{id}/                 → partial update
DELETE /categories/{id}/                 → delete

# create a category
curl -X POST http://localhost:8000/api/categories/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Fish"}'

──────────────────────────────── Items (CRUD + search/sort/filter)
GET    /items/                           → list (supports ?search=, ?ordering=, ?category=, ?supplier=)
POST   /items/                           → create
GET    /items/{id}/                      → details
PATCH  /items/{id}/                      → partial update
DELETE /items/{id}/                      → delete

Search & sort:
  • Search by name/description:    /items/?search=mouse
  • Sort by price or weight:       /items/?ordering=price      (asc)
                                   /items/?ordering=-weight    (desc)
Filter:
  • By category id:                /items/?category=1
  • By supplier id:                /items/?supplier=3

# create an item
curl -X POST http://localhost:8000/api/items/ \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Monitor",
    "description":"27-inch monitor",
    "price":19900.99,
    "weight":4.5,
    "quantity":120,
    "supplierID":3,
    "category":1
  }'

Find which suppliers sell an item by name (unique supplierIDs):
GET /items/suppliers-by-name/?name=Mouse

# example
curl "http://localhost:8000/api/items/suppliers-by-name/?name=Mouse"
→ { "suppliers": [2] }

──────────────────────────────── Friend Requests (Consumer → Supplier)
GET    /requests/                        → list all requests
POST   /requests/                        → create with status=Pending (auto)
GET    /requests/{id}/                   → details
PATCH  /requests/{id}/                   → update (e.g., comment)
DELETE /requests/{id}/                   → delete (optional)
POST   /requests/{id}/approve/           → set status to Approved
POST   /requests/{id}/reject/            → set status to Rejected

# create request (consumer → supplier)
curl -X POST http://localhost:8000/api/requests/ \
  -H "Content-Type: application/json" \
  -d '{
    "consumerID": 5,
    "supplierID": 2,
    "consumerComment": "Can we connect?"
  }'
→ status will be "Pending" by default

# supplier decision
curl -X POST http://localhost:8000/api/requests/1/approve/
curl -X POST http://localhost:8000/api/requests/1/reject/

──────────────────────────────── Chat (messages for APPROVED requests only)
GET    /messages/                        → list (supports ?request={id} to filter a thread)
POST   /messages/                        → create (allowed only if related request is Approved)
GET    /messages/{id}/                   → details
PATCH  /messages/{id}/                   → edit text
DELETE /messages/{id}/                   → delete

# list messages for request #1 (a “thread”)
curl "http://localhost:8000/api/messages/?request=1"

# post a message (sender could be 'consumer' or 'supplier')
curl -X POST http://localhost:8000/api/messages/ \
  -H "Content-Type: application/json" \
  -d '{
    "request": 1,
    "senderType": "consumer",
    "text": "Hello! Do you have fresh stock on Friday?"
  }'
→ If request #1 is not Approved → 400 with explanation.

===============================================================================
5) TYPICAL FLOWS (copy these steps)
===============================================================================
A) Create category → create item
  1) POST /categories/       {"name":"Fish"}
  2) POST /items/            { name, ..., "category": <id>, "supplierID": <number> }

B) Consumer searches and finds suppliers for a product by name
  1) GET /items/suppliers-by-name/?name=Salmon
     → returns an array of supplierIDs who sell it.

C) Consumer sends “friend request” to supplier
  1) POST /requests/         {"consumerID": 12, "supplierID": 3, "consumerComment":"Hi!"}
     → status = "Pending"

D) Supplier approves (or rejects)
  1) POST /requests/{id}/approve/
     → status = "Approved" (now chat is permitted)

E) Chat after approval
  1) POST /messages/         {"request": <approved_id>, "senderType":"supplier","text":"Hello!"}
  2) GET  /messages/?request=<approved_id>  → history

===============================================================================
6) STATUS CODES & ERROR MESSAGES (what to expect)
===============================================================================
• 200 OK            — successful GET, PATCH
• 201 Created       — successful POST (resource created)
• 204 No Content    — successful DELETE
• 400 Bad Request   — wrong/missing fields; chat to non-Approved request
• 404 Not Found     — id doesn’t exist
• 405 Method Not Allowed — wrong HTTP method for this URL

Chat-specific errors:
  - POST /messages/ without "request" field → 400 {"error":"request field is required"}
  - POST /messages/ with unknown request    → 404 {"error":"Request not found"}
  - POST /messages/ when request not Approved → 400 {"error":"Chat allowed only for Approved requests"}

===============================================================================
7) ADMIN PANEL (optional but handy)
===============================================================================
• Login at /admin with the superuser you created.
• You can manage Categories, Items, Requests, Messages by forms.
• Good for sanity checks and quick edits.

===============================================================================
8) WHAT’S NOT IMPLEMENTED (by design, for now)
===============================================================================
• Authentication/RBAC (endpoints are open).
• Real Supplier/Consumer tables (supplierID/consumerID are plain integers).
• Orders, payments, logistics, moderation, analytics.
• File uploads/attachments for chat.
• Pagination for large lists (DRF supports it; easy to add later).

===============================================================================
9) QUICK TROUBLESHOOTING
===============================================================================
• “Connection refused” to DB: ensure containers are up → docker compose up --build
• “No such table …”: run migrations inside web container:
    docker exec -it django_web bash
    python swe_project/manage.py makemigrations
    python swe_project/manage.py migrate
    exit
• 400 on chat: check that your request is Approved first.

===============================================================================
10) MINI CHANGELOG (what your build already supports)
===============================================================================
✔ Dockerized Django + Postgres
✔ Models: Category, Item, Request (with enum-ish statuses), Message
✔ CRUD: /categories, /items, /requests, /messages
✔ Items: search (?search=), ordering (?ordering=price / -weight), filters (?category=, ?supplier=)
✔ Special: /items/suppliers-by-name/?name=...
✔ Request workflow: create → approve/reject
✔ Chat: only if request Approved; filter by ?request=

END.
