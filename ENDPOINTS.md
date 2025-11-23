BASE URL
http://localhost:8000

API prefix
/api/

1.1 Получить токен
curl -X POST http://localhost:8000/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"YOUR_LOGIN","password":"YOUR_PASS"}'

Ответ:
{
  "access": "...",
  "refresh": "..."
}

1.2 Сохранить access
TOKEN=PASTE_ACCESS_HERE

1.3 Делать запросы от имени юзера
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/items/

Supplier Owner или Supplier Staff
видят только свои suppliers, свои items, свои links, свои orders, свои incidents, свои messages

Consumer
видит только себя в /consumers/
видит items только если есть APPROVED link на supplier
видит messages только по APPROVED links где он участник
может создать link и order только в рамках approved link

Platform admin (is_staff или is_superuser)
видит все без фильтров


Эндпоинты по группам

Auth

POST /auth/token/
POST /auth/token/refresh/
GET  /health/
GET  /schema/
GET  /docs/

Categories

GET    /api/categories/
POST   /api/categories/
GET    /api/categories/{id}/
PUT    /api/categories/{id}/
PATCH  /api/categories/{id}/
DELETE /api/categories/{id}/

Items

GET    /api/items/
POST   /api/items/
GET    /api/items/{id}/
PUT    /api/items/{id}/
PATCH  /api/items/{id}/
DELETE /api/items/{id}/

Query params
/api/items/?category={category_id}
/api/items/?supplier={supplier_id}
/api/items/?search=milk
/api/items/?ordering=price
/api/items/?ordering=-weight

Requests (старая модель)

GET    /api/requests/
POST   /api/requests/
GET    /api/requests/{id}/
PUT    /api/requests/{id}/
PATCH  /api/requests/{id}/
DELETE /api/requests/{id}/

Links (новая правильная модель)

GET    /api/links/
POST   /api/links/
GET    /api/links/{id}/
PUT    /api/links/{id}/
PATCH  /api/links/{id}/
DELETE /api/links/{id}/

Actions
POST /api/links/{id}/approve/
POST /api/links/{id}/reject/

Пример создания линка от consumer
POST /api/links/
body:
{
  "consumer": 1,
  "supplier": 2
}


Messages (чат)

GET    /api/messages/
POST   /api/messages/
GET    /api/messages/{id}/
PUT    /api/messages/{id}/
PATCH  /api/messages/{id}/
DELETE /api/messages/{id}/

Query params
/api/messages/?link={link_id}

Создание сообщения
POST /api/messages/
body:
{
  "link": 1,
  "order": null,
  "senderType": "consumer",
  "text": "hi"
}

Suppliers

GET    /api/suppliers/
POST   /api/suppliers/
GET    /api/suppliers/{id}/
PUT    /api/suppliers/{id}/
PATCH  /api/suppliers/{id}/
DELETE /api/suppliers/{id}/

Consumers

GET    /api/consumers/
POST   /api/consumers/
GET    /api/consumers/{id}/
PUT    /api/consumers/{id}/
PATCH  /api/consumers/{id}/
DELETE /api/consumers/{id}/

Staff

GET    /api/staff/
POST   /api/staff/
GET    /api/staff/{id}/
PUT    /api/staff/{id}/
PATCH  /api/staff/{id}/
DELETE /api/staff/{id}/

Orders

GET    /api/orders/
POST   /api/orders/
GET    /api/orders/{id}/
PUT    /api/orders/{id}/
PATCH  /api/orders/{id}/
DELETE /api/orders/{id}/

Action
POST /api/orders/{id}/accept/

Incidents

GET    /api/incidents/
POST   /api/incidents/
GET    /api/incidents/{id}/
PUT    /api/incidents/{id}/
PATCH  /api/incidents/{id}/
DELETE /api/incidents/{id}/

Notifications (read only)

GET /api/notifications/
GET /api/notifications/{id}/


Быстрые user wise примеры
Consumer хочет увидеть каталог

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/items/
Если нет approved link, придет пустой список

Supplier Owner принимает заказ

curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/orders/5/accept/


Consumer пишет в чат по approved link

curl -X POST http://localhost:8000/api/messages/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"link":1,"senderType":"consumer","text":"hello"}'


Если link не approved, получишь 400 из permission IsLinkParticipant
