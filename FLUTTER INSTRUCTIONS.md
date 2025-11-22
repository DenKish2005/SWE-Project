################################################################################
# Supplier–Consumer Platform (Django REST) — Console Quickstart for Flutter dev
# Copy–paste this whole block into INSTRUCTIONS.md (keeps everything in one place)
################################################################################

# ───────────────────────────────────────────────────────────────────────────────
# 0) Prerequisites
# ───────────────────────────────────────────────────────────────────────────────
# • Docker + Docker Compose installed
# • (Optional) jq installed for parsing JSON in shell: https://stedolan.github.io/jq/

# ───────────────────────────────────────────────────────────────────────────────
# 1) Run the backend
# ───────────────────────────────────────────────────────────────────────────────
docker compose up -d
# First run will:
#   - start PostgreSQL
#   - run Django migrations
#   - serve API on http://localhost:8000

# Health check (should return {"status":"ok"})
curl -s http://localhost:8000/health/ | jq .

# OpenAPI docs (Swagger UI):
#   http://localhost:8000/docs
# Raw schema:
#   http://localhost:8000/schema/

# ───────────────────────────────────────────────────────────────────────────────
# 2) Create demo users (one supplier owner, one consumer)
#    (You can also create users in http://localhost:8000/admin but this is faster.)
# ───────────────────────────────────────────────────────────────────────────────
docker compose exec -T web python swe_project/manage.py shell -c "
from django.contrib.auth.models import User
for name in ['supplier','consumer','platformadmin']:
    u, created = User.objects.get_or_create(username=name, email=f'{name}@example.com')
    u.set_password('pass'); u.is_staff = (name=='platformadmin'); u.save()
print('Users ready: supplier/pass, consumer/pass, platformadmin/pass')
"

# ───────────────────────────────────────────────────────────────────────────────
# 3) Auth — get JWT tokens
# ───────────────────────────────────────────────────────────────────────────────
API=http://localhost:8000

# Supplier owner token
curl -s -X POST $API/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"supplier","password":"pass"}' | tee /tmp/supplier_token.json

SUPPLIER_JWT=$(cat /tmp/supplier_token.json | jq -r .access)

# Consumer token
curl -s -X POST $API/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"consumer","password":"pass"}' | tee /tmp/consumer_token.json

CONSUMER_JWT=$(cat /tmp/consumer_token.json | jq -r .access)

# Platform admin (for KYB/analytics examples)
curl -s -X POST $API/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"platformadmin","password":"pass"}' | tee /tmp/admin_token.json

ADMIN_JWT=$(cat /tmp/admin_token.json | jq -r .access)

# ───────────────────────────────────────────────────────────────────────────────
# 4) Minimal data setup via API
# ───────────────────────────────────────────────────────────────────────────────

# 4.1 Create Category
cat > /tmp/category.json << 'EOF'
{ "name": "Food", "description": "All food", "is_moderated": true }
EOF
curl -s -X POST $API/api/categories/ \
  -H "Authorization: Bearer $SUPPLIER_JWT" -H "Content-Type: application/json" \
  -d @/tmp/category.json | tee /tmp/category_created.json
CATEGORY_ID=$(jq -r .id /tmp/category_created.json)

# 4.2 Create Supplier (owned by 'supplier' user id = look up from admin if needed)
#     Fast way: ask the API which user we are (no endpoint) → we pass user id manually.
#     Below we query it from Django quickly and reuse:
SUPPLIER_USER_ID=$(docker compose exec -T web python - <<'PY'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','swe_project.settings'); django.setup()
from django.contrib.auth.models import User
print(User.objects.get(username='supplier').id)
PY
)
echo "SUPPLIER_USER_ID=$SUPPLIER_USER_ID"

cat > /tmp/supplier.json << EOF
{ "user": $SUPPLIER_USER_ID, "company_name": "Acme Foods", "city": "Almaty" }
EOF
curl -s -X POST $API/api/suppliers/ \
  -H "Authorization: Bearer $SUPPLIER_JWT" -H "Content-Type: application/json" \
  -d @/tmp/supplier.json | tee /tmp/supplier_created.json
SUPPLIER_ID=$(jq -r .id /tmp/supplier_created.json)

# 4.3 Create Consumer bound to 'consumer' user
CONSUMER_USER_ID=$(docker compose exec -T web python - <<'PY'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','swe_project.settings'); django.setup()
from django.contrib.auth.models import User
print(User.objects.get(username='consumer').id)
PY
)
echo "CONSUMER_USER_ID=$CONSUMER_USER_ID"

cat > /tmp/consumer.json << EOF
{ "user": $CONSUMER_USER_ID, "business_name": "Cafe Moon", "business_type": "restaurant", "city": "Astana" }
EOF
curl -s -X POST $API/api/consumers/ \
  -H "Authorization: Bearer $CONSUMER_JWT" -H "Content-Type: application/json" \
  -d @/tmp/consumer.json | tee /tmp/consumer_created.json
CONSUMER_ID=$(jq -r .id /tmp/consumer_created.json)

# 4.4 Supplier creates a couple of Items
cat > /tmp/item1.json << EOF
{
  "supplier": $SUPPLIER_ID,
  "name": "Sugar 1kg",
  "description": "White sugar",
  "price": "100.00",
  "weight": "1.000",
  "stock_level": 50,
  "min_order_qty": 1,
  "category": $CATEGORY_ID,
  "is_available": true
}
EOF
curl -s -X POST $API/api/items/ \
  -H "Authorization: Bearer $SUPPLIER_JWT" -H "Content-Type: application/json" \
  -d @/tmp/item1.json | tee /tmp/item1_created.json
ITEM1_ID=$(jq -r .id /tmp/item1_created.json)

# 4.5 Consumer requests a Link to this Supplier (PENDING → APPROVED)
cat > /tmp/link_req.json << EOF
{ "consumer": $CONSUMER_ID, "supplier": $SUPPLIER_ID }
EOF
curl -s -X POST $API/api/links/ \
  -H "Authorization: Bearer $CONSUMER_JWT" -H "Content-Type: application/json" \
  -d @/tmp/link_req.json | tee /tmp/link_created.json
LINK_ID=$(jq -r .id /tmp/link_created.json)

# Approve the link (supplier side)
curl -s -X POST $API/api/links/$LINK_ID/approve/ \
  -H "Authorization: Bearer $SUPPLIER_JWT" | jq .

# Now consumer can see supplier items
curl -s -X GET "$API/api/items/?supplier=$SUPPLIER_ID" \
  -H "Authorization: Bearer $CONSUMER_JWT" | jq .

# ───────────────────────────────────────────────────────────────────────────────
# 5) Orders (create → accept → complete)
# ───────────────────────────────────────────────────────────────────────────────

# 5.1 Create an Order (consumer)
cat > /tmp/order.json << EOF
{
  "consumer": $CONSUMER_ID,
  "supplier": $SUPPLIER_ID,
  "link": $LINK_ID,
  "delivery_type": "delivery",
  "delivery_address": "Street 1",
  "notes": "Leave at door",
  "items": [
    { "product": $ITEM1_ID, "quantity": 2, "discount": "0.00", "name_snapshot": "", "unit_price": "0.00", "subtotal":"0.00" }
  ]
}
EOF
curl -s -X POST $API/api/orders/ \
  -H "Authorization: Bearer $CONSUMER_JWT" -H "Content-Type: application/json" \
  -d @/tmp/order.json | tee /tmp/order_created.json
ORDER_ID=$(jq -r .id /tmp/order_created.json)

# 5.2 Supplier accepts the Order (stock will decrement)
curl -s -X POST $API/api/orders/$ORDER_ID/accept/ \
  -H "Authorization: Bearer $SUPPLIER_JWT" | jq .

# 5.3 Supplier completes the Order
curl -s -X POST $API/api/orders/$ORDER_ID/complete/ \
  -H "Authorization: Bearer $SUPPLIER_JWT" | jq .

# ───────────────────────────────────────────────────────────────────────────────
# 6) Chat and attachments
# ───────────────────────────────────────────────────────────────────────────────

# 6.1 Send a text message (either side; must be LINK participant)
cat > /tmp/msg.json << EOF
{ "link": $LINK_ID, "sender_type": "consumer", "text": "Hello! any discount?" }
EOF
curl -s -X POST $API/api/messages/ \
  -H "Authorization: Bearer $CONSUMER_JWT" -H "Content-Type: application/json" \
  -d @/tmp/msg.json | tee /tmp/msg_created.json
MSG_ID=$(jq -r .id /tmp/msg_created.json)

# 6.2 Upload an attachment to that message (multipart)
echo "Notes file" > /tmp/note.txt
curl -s -X POST $API/api/messages/$MSG_ID/attachments/ \
  -H "Authorization: Bearer $CONSUMER_JWT" \
  -F "file=@/tmp/note.txt" | jq .

# 6.3 Read chat history for the link
curl -s "$API/api/messages/?link=$LINK_ID&ordering=created_at" \
  -H "Authorization: Bearer $SUPPLIER_JWT" | jq .

# ───────────────────────────────────────────────────────────────────────────────
# 7) Incidents (complaints) & Notifications
# ───────────────────────────────────────────────────────────────────────────────

# 7.1 Consumer logs an incident
cat > /tmp/incident.json << EOF
{
  "order": $ORDER_ID,
  "consumer": $CONSUMER_ID,
  "supplier": $SUPPLIER_ID,
  "type": "delivery",
  "priority": "high",
  "description": "Order arrived late"
}
EOF
curl -s -X POST $API/api/incidents/ \
  -H "Authorization: Bearer $CONSUMER_JWT" -H "Content-Type: application/json" \
  -d @/tmp/incident.json | tee /tmp/incident_created.json
INCIDENT_ID=$(jq -r .id /tmp/incident_created.json)

# 7.2 Supplier escalates or resolves (examples)
curl -s -X POST $API/api/incidents/$INCIDENT_ID/escalate/ \
  -H "Authorization: Bearer $SUPPLIER_JWT" | jq .
curl -s -X POST $API/api/incidents/$INCIDENT_ID/resolve/ \
  -H "Authorization: Bearer $SUPPLIER_JWT" \
  -H "Content-Type: application/json" \
  -d '{"resolution":"Refund 10%"}' | jq .

# 7.3 Consumer checks notifications and marks as read
curl -s $API/api/notifications/ \
  -H "Authorization: Bearer $CONSUMER_JWT" | tee /tmp/notifs.json
FIRST_NOTIF=$(jq -r '.[0].id // empty' /tmp/notifs.json)
if [ -n "$FIRST_NOTIF" ]; then
  curl -s -X POST $API/api/notifications/$FIRST_NOTIF/read/ \
    -H "Authorization: Bearer $CONSUMER_JWT" | jq .
fi

# ───────────────────────────────────────────────────────────────────────────────
# 8) Platform Admin (KYB) — optional
#    Requires platformadmin/pass (is_staff=True) or a user with UserProfile.role=platform_admin
# ───────────────────────────────────────────────────────────────────────────────

# Create a KYB record (admin)
cat > /tmp/kyb.json << EOF
{ "supplier": $SUPPLIER_ID, "status": "pending" }
EOF
curl -s -X POST $API/api/platadmin/kyb/ \
  -H "Authorization: Bearer $ADMIN_JWT" -H "Content-Type: application/json" \
  -d @/tmp/kyb.json | jq .

# List KYB records (admin)
curl -s $API/api/platadmin/kyb/ -H "Authorization: Bearer $ADMIN_JWT" | jq .

# ───────────────────────────────────────────────────────────────────────────────
# 9) What the Flutter app needs (TL;DR)
# ───────────────────────────────────────────────────────────────────────────────
# Base URL:
#   http://localhost:8000
# Auth:
#   POST /auth/token/  { "username": "...", "password": "..." } → { "access": "...", "refresh": "..." }
#   Use header: Authorization: Bearer <access>
# Key endpoints you’ll likely call:
#   GET  /api/items/?category=&supplier=&is_available=true
#   POST /api/links/  (consumer requests link)
#   POST /api/links/{id}/approve|reject|block|remove/  (supplier side)
#   POST /api/orders/  (with "items": [{product, quantity, discount?}])
#   POST /api/orders/{id}/accept|reject|complete/
#   GET/POST /api/messages/  (+  POST /api/messages/{id}/attachments  multipart file)
#   GET  /api/notifications/  (+  POST /api/notifications/{id}/read/)
#   GET/POST /api/incidents/  (+  POST /api/incidents/{id}/resolve|escalate|assign)
# Errors are JSON-wrapped as:
#   { "error": { "type": "<ExceptionClass>", "detail": { ... } } }

# ───────────────────────────────────────────────────────────────────────────────
# 10) Flutter snippet (Dio) — copy into your project (pseudo-minimal)
# ───────────────────────────────────────────────────────────────────────────────
cat > /tmp/flutter_dio_example.dart << 'EOF'
import 'package:dio/dio.dart';

class Api {
  final Dio dio;
  Api(String baseUrl, {String? token})
      : dio = Dio(BaseOptions(baseUrl: baseUrl, headers: {
          if (token != null) 'Authorization': 'Bearer $token',
        }));

  static Future<String> login(String baseUrl, String u, String p) async {
    final r = await Dio().post('$baseUrl/auth/token/',
        data: {'username': u, 'password': p});
    return r.data['access'];
  }

  Future<Response> listItems({int? supplierId, int? categoryId}) {
    final qp = {
      if (supplierId != null) 'supplier': '$supplierId',
      if (categoryId != null) 'category': '$categoryId',
      'is_available': 'true',
    };
    return dio.get('/api/items/', queryParameters: qp);
  }

  Future<Response> createOrder(Map<String, dynamic> payload) {
    return dio.post('/api/orders/', data: payload);
  }

  Future<Response> sendMessage(int linkId, String text, String who) {
    return dio.post('/api/messages/', data: {
      'link': linkId,
      'sender_type': who, // 'consumer' | 'sales' | 'manager' | 'owner'
      'text': text,
    });
  }

  Future<Response> uploadAttachment(int messageId, String filePath) async {
    final form = FormData.fromMap({
      'file': await MultipartFile.fromFile(filePath),
    });
    return dio.post('/api/messages/$messageId/attachments/', data: form);
  }
}
EOF
echo "Flutter example saved to /tmp/flutter_dio_example.dart"

# ───────────────────────────────────────────────────────────────────────────────
# 11) Useful filters & tips
# ───────────────────────────────────────────────────────────────────────────────
# Items:
#   /api/items/?supplier=<ID>&category=<ID>&is_available=true
# Messages:
#   /api/messages/?link=<LINK_ID>&ordering=created_at   (or =-created_at for newest first)
# Pagination:
#   Standard DRF page params: ?page=2
# Rate limits (defaults):
#   anon: 60/min, user: 120/min
# CORS:
#   Allowed for all origins in dev (see settings.py), so Flutter Web/Mobile can hit the API directly.

# ───────────────────────────────────────────────────────────────────────────────
# 12) Shutdown / cleanup
# ───────────────────────────────────────────────────────────────────────────────
# Stop containers
# docker compose down
# Reset DB + media (danger!)
# docker compose down -v && rm -rf media

################################################################################
# End of console guide
################################################################################
