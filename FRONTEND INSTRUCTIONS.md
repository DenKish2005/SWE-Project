# ===============================================================
# SWE Supplier–Consumer Platform — Frontend Integration (Console)
# ===============================================================
# Copy-paste friendly cheat-sheet for connecting your web/mobile app.
# All requests are JSON unless noted (file upload = multipart/form-data).

# ---- 0) Base URLs (dev Docker compose) --------------------------------------
BASE="http://localhost:8000"
API="$BASE/api"
DOCS="$BASE/docs"          # OpenAPI UI
SCHEMA="$BASE/schema"      # Raw schema (if you need codegen)
HEALTH="$BASE/health"

curl -s $HEALTH
# => {"status":"ok"}

# ---- 1) Auth (JWT) ----------------------------------------------------------
# Get tokens
curl -s -X POST "$BASE/auth/token/" \
  -H "Content-Type: application/json" \
  -d '{"username":"<login>","password":"<password>"}'
# => {"access":"<JWT_ACCESS>","refresh":"<JWT_REFRESH>"}

# Refresh
curl -s -X POST "$BASE/auth/token/refresh/" \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<JWT_REFRESH>"}'
# => {"access":"<NEW_ACCESS>"}

# Use in every request:
AUTH="Authorization: Bearer <JWT_ACCESS>"

# Pagination = DRF default:
#   ?page=1 (response: count, next, previous, results)
# Search/Ordering (where supported):
#   ?search=..., ?ordering=price or -price

# ===============================================================
# A) CATEGORIES
# ===============================================================
# List (+search by name)
curl -s "$API/categories/?search=meat" -H "$AUTH"

# Create (admin/platform-moderated in real setups; here any authed by default)
curl -s -X POST "$API/categories/" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"name":"Meat","description":"All meat","parent":null,"is_moderated":true}'

# ===============================================================
# B) LINKS (Consumer <-> Supplier access gate)
#    Status: Pending -> Approved / Rejected / Blocked / Removed
#    A Consumer MUST have an APPROVED link to see supplier catalog or chat.
# ===============================================================
# Create link (as Consumer)
curl -s -X POST "$API/links/" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"consumer":1,"supplier":5}'

# Approve / Reject / Block / Remove (Supplier Owner/Manager)
curl -s -X POST "$API/links/12/approve/" -H "$AUTH"
curl -s -X POST "$API/links/12/reject/"  -H "$AUTH"
curl -s -X POST "$API/links/12/block/"   -H "$AUTH"
curl -s -X POST "$API/links/12/remove/"  -H "$AUTH"

# ===============================================================
# C) ITEMS (Supplier catalog)
#    Visibility rules:
#      - Supplier staff (owner/manager/sales) see own items
#      - Consumers see items ONLY for APPROVED links
#    Filters: ?supplier=, ?category=, ?is_available=true|false
#    Search:  ?search=<name or description>
#    Order:   ?ordering=price|weight|created_at (prefix - for desc)
# ===============================================================
curl -s "$API/items/?supplier=5&is_available=true&search=sugar&ordering=price" -H "$AUTH"

# Create / Update (Supplier owner/manager)
curl -s -X POST "$API/items/" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
        "supplier":5,"name":"Sugar 1kg","description":"Fine",
        "price":"100.00","weight":"1.000","category":2,
        "unit":"kg","discount_percent":"0","min_order_qty":1,
        "stock_level":150,"is_available":true
      }'

# ===============================================================
# D) ORDERS
#    DeliveryType: "pickup" | "delivery"
#    Status flow: Submitted -> Accepted/Rejected -> Completed
#    Body contains nested "items".
#    Server validates: link must be APPROVED, party ids must match link,
#                      min_order_qty per product; totals auto-recalc.
# ===============================================================
# Create (Consumer with APPROVED link)
curl -s -X POST "$API/orders/" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
        "consumer":1,
        "supplier":5,
        "link":12,
        "delivery_type":"delivery",
        "delivery_address":"Astana, Street 1",
        "notes":"Please deliver AM",
        "items":[
          {"product":101,"quantity":3},     # discount optional
          {"product":102,"quantity":1,"discount":"5.00"}
        ]
      }'
# => { ..., "order_number":"O-XXXXXXXXXX", "total_amount":"...", "items":[...] }

# Supplier actions
curl -s -X POST "$API/orders/44/accept/"   -H "$AUTH"
curl -s -X POST "$API/orders/44/reject/"   -H "$AUTH"
curl -s -X POST "$API/orders/44/complete/" -H "$AUTH"

# List (auto-scoped: suppliers see their orders; consumers see their own)
curl -s "$API/orders/?page=1" -H "$AUTH"

# ===============================================================
# E) CHAT + ATTACHMENTS
#    Only participants of an APPROVED link can send/read messages.
#    sender_type: consumer | sales | manager | owner   (system is internal)
# ===============================================================
# Send text message
curl -s -X POST "$API/messages/" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"link":12,"order":44,"sender_type":"consumer","text":"Hello! Can we add 2 more?"}'

# List messages (newest last by default ordering param)
curl -s "$API/messages/?link=12&ordering=created_at" -H "$AUTH"

# Upload attachment to a message (multipart)
curl -s -X POST "$API/messages/200/attachments/" -H "$AUTH" \
  -F "file=@/path/to/invoice.pdf"

# Attachment URL will be under "file" field; fetch via BASE + that path (served from MEDIA_URL in dev).

# ===============================================================
# F) INCIDENTS (complaints)
#    type: quality | delivery | billing | other
#    status: Open -> Escalated/Resolved -> Closed
# ===============================================================
# Create (Consumer or Staff)
curl -s -X POST "$API/incidents/" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
        "order":44,
        "consumer":1,
        "supplier":5,
        "type":"delivery",
        "priority":"high",
        "description":"Arrived late",
        "reported_by": 3
      }'

# Assign to staff (supplier side)
curl -s -X POST "$API/incidents/7/assign/" -H "$AUTH" \
  -H "Content-Type: application/json" -d '{"staff_id":25}'

# Escalate / Resolve
curl -s -X POST "$API/incidents/7/escalate/" -H "$AUTH"
curl -s -X POST "$API/incidents/7/resolve/"  -H "$AUTH" \
  -H "Content-Type: application/json" -d '{"resolution":"Refund issued"}'

# List (auto-scoped like orders)
curl -s "$API/incidents/?page=1" -H "$AUTH"

# ===============================================================
# G) NOTIFICATIONS
#    Types: info | link | order | incident | chat
# ===============================================================
# List my notifications (newest first)
curl -s "$API/notifications/" -H "$AUTH"

# Mark as read
curl -s -X POST "$API/notifications/88/read/" -H "$AUTH"

# ===============================================================
# H) PARTIES & STAFF
# ===============================================================
# Current user’s Supplier(s)
curl -s "$API/suppliers/" -H "$AUTH"

# Current user’s Consumer profile
curl -s "$API/consumers/" -H "$AUTH"

# Supplier staff (owner/manager can CRUD)
curl -s "$API/staff/?page=1" -H "$AUTH"

# ===============================================================
# I) PLATFORM ADMIN (optional KYB)
#    Requires Platform Admin role (or Django staff).
# ===============================================================
# Create/update KYB record (multipart if uploading doc)
curl -s -X POST "$API/platadmin/kyb/" -H "$AUTH" \
  -F "supplier=5" -F "status=pending" -F "document=@/path/to/license.pdf"

curl -s -X PATCH "$API/platadmin/kyb/5/" -H "$AUTH" \
  -H "Content-Type: application/json" -d '{"status":"approved","comment":"Verified"}'

# ===============================================================
# J) COMMON HEADERS / ERRORS
# ===============================================================
# Always send:
#   -H "Authorization: Bearer <JWT_ACCESS>"
# JSON:        -H "Content-Type: application/json"
# Multipart:   -H "Content-Type: multipart/form-data" (curl -F handles it)
# 401 = not authenticated, 403 = no permission, 400 = validation failed.

# ===============================================================
# K) QUICK ROLE FLOWS (TL;DR)
# ===============================================================
# Consumer:
#   1) POST /links/  -> wait until Approved
#   2) GET  /items/?supplier=<id>
#   3) POST /orders/ (with items[])
#   4) Chat: POST /messages/  (+ attachments)
#   5) If problem: POST /incidents/
#
# Supplier (owner/manager):
#   1) POST /links/{id}/approve|reject|block|remove
#   2) CRUD /items/
#   3) POST /orders/{id}/accept|reject|complete
#   4) Handle incidents: /incidents/* + assign/escalate/resolve
#
# Everyone:
#   - GET /notifications/  then POST /notifications/{id}/read/
#
# Docs:
#   OpenAPI UI -> $DOCS
