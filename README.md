Team members:

- Daniyar Kshibekov
- Askar Matayev
- Dana Koshkinbayeva
- Ruslan Nagimov

On what this project's backend will be written: Django (Python)

┌──────────────────────────────────────────────────────────────────────────────┐
│ SCP Backend — Domain & API Blueprint                                         │
│ (MVP + Product Improvements)                                                 │
│ Paste-ready for README.md — console style                                    │
└──────────────────────────────────────────────────────────────────────────────┘

SUMMARY
  A closed B2B platform connecting Suppliers (food producers/distributors) with
  institutional Consumers (restaurants/hotels). Catalog visibility, chat, and
  ordering are gated by an explicit Supplier↔Consumer link (approval required).
  MVP excludes payments, logistics, subscriptions, ratings, analytics.

SCOPE (WHAT THE BACKEND MUST ENABLE)
  • Link model: Consumer requests access, Supplier approves → unlock Catalog, Chat, Orders
  • Catalog: categories, products, prices, MOQ, inventory
  • Bulk Orders: create/accept/reject (+ immutable price snapshot)
  • Chat: after link only; text + file/audio attachments
  • Complaints: always from an order; Sales → Manager escalation
  • Incidents: log + status workflow; export
  • Data Retention: no deletions; archive to read-only after X years
  • (Later) Platform Admin, KYB, moderation, analytics, subscriptions, payments, logistics, ratings

================================================================================
MVP DOMAIN MODEL — ENTITIES (CLASSES) & RESPONSIBILITIES
================================================================================

IDENTITY & ACCESS
  User
    - One human account; email/login/localization/active status.
  Supplier
    - Supplier company profile; active flag; settings (later: payout, KYB refs).
  Consumer
    - Consumer company profile (restaurant/hotel); active flag.
  SupplierMember
    - Joins a User to a Supplier with a role {Owner, Manager, Sales}; on/off status.
  ConsumerMember
    - Joins a User to a Consumer (staff accounts); on/off status.
  SupplierRole (enum)
    - Owner: full control (users, catalog, escalation oversight, account deletion).
    - Manager: catalog, inventory, orders, escalations (no account deletion).
    - Sales: frontline comms, first-line complaint handling (cannot approve links).

LINKING (ACCESS GATE)
  SupplierConsumerLink
    - SupplierId, ConsumerId, Status ∈ {Pending, Accepted, Removed, Blocked}
    - Invariant: Catalog/Chat/Orders require Status = Accepted
  LinkStatus (enum): Pending | Accepted | Removed | Blocked

CATALOG
  Category
    - Hierarchical tree (parentId nullable): Dairy / Meat / Fish / Produce / etc.
  Product
    - Supplier-scoped SKU; CategoryId; name; unit (kg, L, pack); MOQ; price; flags;
      marketing/media refs; availability.
  InventoryItem
    - ProductId; on-hand quantity (decimal); last updated.

ORDERING (BULK)
  Order
    - Aggregate root: SupplierId, ConsumerId, Status, CreatedAt, Total
    - Holds lines with historical price snapshot (immutably stored in lines)
  OrderLine
    - OrderId, ProductId, Qty, UnitPrice (snapshotted at order time), LineTotal
  OrderStatus (enum): Submitted | Accepted | Rejected | Cancelled

MESSAGING & COMPLAINTS
  ChatThread
    - One thread per Supplier↔Consumer (or per order as policy decides); only after link Accepted
  ChatMessage
    - ThreadId; SenderUserId; text; AttachmentId?; timestamps; read receipts
  Attachment
    - Metadata only (key/url, mime, size, checksums); binary lives in object storage
  Complaint
    - Always linked to an Order; RaisedByUserId; Status; Description; timestamps
  ComplaintStatus (enum): Open | Escalated | Resolved

INCIDENT MANAGEMENT
  Incident
    - Service-level issue log (often created from an order); OwnerUserId; Status; timestamps
  IncidentEvent
    - Append-only history: note, who, when
  IncidentStatus (enum): Open | InProgress | Resolved

RETENTION / ARCHIVE
  ArchiveJob
    - Scheduled/triggered job that moves old records into read-only storage/partition
  ArchivedRecordRef
    - Optional indirection/reference when using separate archive schema/db

================================================================================
MVP SERVICE LAYER — CORE USE CASES
================================================================================

LinkService
  • requestLink(consumer, supplier)
  • accept/reject/remove/block (Owner/Manager only)
  • guards: deny Catalog/Chat/Orders unless link.Accepted

CatalogService
  • CRUD categories/products (Supplier-scoped)
  • setPrice/MOQ/discounts, updateInventory(productId, delta/absolute)
  • visibility: only linked Consumers can view Supplier’s catalog

OrderService
  • createOrder(consumer, supplier, lines) → validate: link=Accepted, MOQ, availability
  • acceptOrder / rejectOrder (Manager/Owner only)
  • snapshot line prices; recompute totals; emit domain events

ChatService
  • openThread on link.Accepted (lazy creation on first message)
  • postMessage(text|attachment); read receipts; typing indicators (optional)
  • deep links to products/orders in message payload

ComplaintService
  • createComplaint(orderId, byUser)
  • Sales handles first; escalateToManager(); resolve()
  • emits notifications on escalation/resolution

IncidentService
  • openIncident(orderId?, byUser); addEvent(); setStatus()
  • export incidents (csv/json) for audits

RetentionService
  • runArchivePolicy(cutoffDate)
  • enforce read-only semantics on archived data

Integrations
  • NotificationService (email/push): link decisions, order events, complaint escalation,
    incident closure
  • FileStorageService: put/get object; signed urls; virus scan hooks (optional)
  • AuthZService: enforce RBAC on routes/commands (Owner/Manager/Sales)

================================================================================
MVP REST API — PRIMARY ENDPOINTS (SUGGESTED SHAPES)
================================================================================

/auth
  POST /login                                   → JWT/OAuth2 token
  GET  /me                                      → current user & memberships

/links
  POST /links                                   → consumer requests link with supplier
  POST /links/{id}/accept | /reject | /remove   → owner/manager only
  POST /links/{id}/block                        → owner/manager only
  GET  /links?role=supplier|consumer&status=... → list

/catalog
  GET  /categories                              → visible categories (linked only)
  GET  /products?category=...                   → consumer-visible products
  POST /products                                → supplier create (manager/owner)
  PATCH /products/{id}                          → supplier update
  PATCH /inventory/{productId}                  → supplier inventory update

/orders
  POST /orders                                  → consumer create (requires link=Accepted)
  GET  /orders?scope=consumer|supplier          → list by role
  GET  /orders/{id}                             → details (with lines)
  POST /orders/{id}/accept | /reject | /cancel  → owner/manager; cancel rules as policy

/complaints
  POST /orders/{id}/complaints                  → create complaint (from order)
  POST /complaints/{id}/escalate                → sales → manager
  POST /complaints/{id}/resolve                 → manager/owner
  GET  /complaints?orderId=...&status=...       → list

/chat
  POST /threads                                 → (optional) open thread explicitly
  GET  /threads?scope=consumer|supplier         → list
  POST /threads/{id}/messages                   → send message
  POST /attachments                             → upload metadata, get storage URL

/incidents
  POST /incidents                               → open
  PATCH /incidents/{id}                         → status/owner/update
  GET  /incidents/export                        → csv/json export

/maintenance
  POST /retention/run                           → manual archive trigger (admin op)

================================================================================
INVARIANTS / BUSINESS RULES (ENFORCE EVERYWHERE)
================================================================================
  [1] Gatekeeping: Catalog, Chat, and Orders require link.Status == Accepted.
  [2] Only Supplier Owner/Manager can accept/reject/block a link request.
  [3] Order creation: validate link, MOQ, product active, & availability snapshot checks.
  [4] Order lines store immutable UnitPrice snapshot (no retroactive price drift).
  [5] Complaint must reference an Order. Flow: Sales handles first → escalate to Manager.
  [6] Incidents: tracked with statuses; history is append-only; export required.
  [7] No destructive deletion of business records. Archive to read-only after X years.
  [8] Files are never stored in RDBMS; only metadata/keys in DB; binaries in object storage.
  [9] All reads/writes are Supplier-scoped for isolation in the closed network model.
 [10] RBAC mirrors roles: Owner (full), Manager (ops), Sales (frontline comms).

================================================================================
SUGGESTED BOUNDED CONTEXTS / MODULES
================================================================================
  • Identity & Access     → Users, Members, Roles, AuthZ
  • Linking               → SupplierConsumerLink + LinkService
  • Catalog               → Category, Product, Inventory
  • Ordering              → Order, OrderLine
  • Messaging             → ChatThread, ChatMessage, Attachment
  • Complaints            → Complaint (+ integrates with Messaging/Ordering)
  • Incidents             → Incident, IncidentEvent
  • Retention             → Archive policy & jobs
  • (Later) Admin & KYB   → Platform admin, KYB cases/docs, moderation
  • (Later) Monetization  → Subscriptions, invoices
  • (Later) Payments      → Payments, payouts, refunds
  • (Later) Logistics     → Shipments, slots, carriers
  • (Later) Ratings       → Reviews, aggregates
  • (Later) Analytics     → KPI snapshots, series

================================================================================
ASCII ER SKETCH (MVP CORE)
================================================================================
  [User] 1—* [SupplierMember] *—1 [Supplier]
  [User] 1—* [ConsumerMember] *—1 [Consumer]

  [Supplier] 1—* [Product] *—1 [Category]
  [Product] 1—1 [InventoryItem]

  [Supplier] 1—* [SupplierConsumerLink] *—1 [Consumer]  (Status=Accepted gates access)

  [Order] *—1 [Supplier] ; [Order] *—1 [Consumer]
  [Order] 1—* [OrderLine] *—1 [Product]  (UnitPrice snapshotted)

  [ChatThread] *—1 [Supplier] ; *—1 [Consumer]
  [ChatThread] 1—* [ChatMessage] *—0..1 [Attachment]

  [Complaint] *—1 [Order] ; states: Open→Escalated→Resolved
  [Incident]  *—1 [Order]? ; states: Open→InProgress→Resolved ; 1—* [IncidentEvent]

================================================================================
NON-FUNCTIONAL / INFRASTRUCTURE (MVP)
================================================================================
  • DB: PostgreSQL (consider schemas/partitions for archive)
  • API: REST (Django/FastAPI, Spring, Go, or ASP.NET Core equivalent)
  • Object Storage: S3-compatible or cloud blob store; signed URLs
  • Push: FCM/APNs (notifications for key events)
  • AuthN/Z: JWT/OAuth2; RBAC enforcement per route/command
  • Observability: structured logs, request IDs, basic metrics (p95 latency, error rate)
  • Migrations: versioned (Flyway/Liquibase/EF Migrations)
  • Environments: Local (dev/demo) → Staging → Production
  • CI/CD: build, test, lint, migrate, deploy (GitHub Actions/Jenkins)
  • Security basics: input validation, rate limiting, file type/size/AV scan, least privilege

================================================================================
DELIVERY ORDER — PRACTICAL BUILD CHECKLIST (MVP)
================================================================================
  [1] Identity & Access        → Users, Members, RBAC middleware
  [2] Linking                  → endpoints + global access guards
  [3] Catalog                  → categories/products/inventory + visibility rules
  [4] Ordering                 → create/list/detail + accept/reject + snapshots
  [5] Messaging                → threads/messages/attachments + events
  [6] Complaints               → from order; sales-first; escalation to manager
  [7] Incidents                → log/status/history + export
  [8] Retention                → archive policy job; read-only enforcement
  [9] Notifications            → wire minimal email/push for key domain events

================================================================================
POST-MVP IMPROVEMENTS — ENTITIES & SERVICES
================================================================================

Platform Admin & Compliance
  PlatformAdmin (user type), AdminRole
  KYBCase, KYBDocument (approve/reject supplier verification)
  ModerationQueue, ModerationItem (listings/media moderation)
  AdminVerificationService, AdminModerationService

Monetization (Subscriptions)
  SubscriptionPlan (tiers), SupplierSubscription, Invoice, PaymentMethod
  SubscriptionService (activate/suspend/cancel, trials/discounts)

Payments & Payouts
  Payment, Payout, Transaction, RefundRequest
  PaymentService (PSP integration), PayoutService (supplier disbursements)

Logistics & Fulfillment
  Shipment, Carrier, DeliveryWindow, PickupSlot
  LogisticsService (later: route/slot planning, SLA tracking)

Ratings & Reviews
  Review, RatingAggregate; ReviewsService

Analytics
  AnalyticsSnapshot, KpiSeries (GMV, AOV, retention, top SKUs, first response time)
  AnalyticsService (rollups, windows, cohorts; dashboards for Supplier Owners/Admins)

================================================================================
NOTES & GOTCHAS
================================================================================
  • Don’t leak data across suppliers: always scope by (SupplierId, ConsumerId).
  • Price snapshots are mandatory: never re-price historical orders.
  • State machines: explicit enums + guards (complaints/incidents).
  • Archive ≠ soft delete: make archived data genuinely immutable.
  • Store only file metadata in DB; binaries live in object storage.
  • Emit domain events for notifications & integrations.
  • Mirror RACI in RBAC: who can approve links, accept orders, escalate, etc.

END.
