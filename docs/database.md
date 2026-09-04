# Database Design & Data Validation

> **Purpose:** This document defines how the application's database is structured, how data moves through it, how Pydantic models validate API boundaries, and how database integrity is enforced.
>
> Core principle:
>
> ```text
> Pydantic validates requests/responses.
> Business services validate business rules.
> PostgreSQL enforces data integrity.
> ```
>
> None of these layers replaces the others.

---

# 1. Database Philosophy

The database must be designed around four requirements:

```text
1. Financial correctness
2. Merchant/customer isolation
3. Auditability
4. AI-safe structured data
```

The database is the application's source of truth for:

```text
users
merchants
customers
products
inventory
cart
quotes
policies
authorizations
orders
payments
events
audit
AI state
```

It is NOT the source of truth for Razorpay's external payment system.

For payment state:

```text
Our DB
   ↕
Razorpay
   ↕
Verified webhooks / API reconciliation
```

---

# 2. Database Technology

Use:

```text
PostgreSQL
```

ORM:

```text
SQLAlchemy
```

Migration system:

```text
Alembic
```

Validation:

```text
Pydantic v2
```

Backend:

```text
FastAPI
```

Architecture:

```text
FastAPI
   ↓
Pydantic Schema
   ↓
Service Layer
   ↓
Repository / SQLAlchemy
   ↓
PostgreSQL
```

---

# 3. Database Layering

Do not allow API routes to directly manipulate database records everywhere.

Preferred:

```text
API Route
   ↓
Pydantic Schema
   ↓
Service
   ↓
Repository
   ↓
SQLAlchemy
   ↓
PostgreSQL
```

Example:

```text
POST /products
       ↓
ProductCreate
       ↓
ProductService.create()
       ↓
ProductRepository.create()
       ↓
PostgreSQL
```

This keeps business logic out of HTTP routes.

---

# 4. Database Naming Conventions

Use:

```text
snake_case
```

Tables:

```text
users
merchants
products
cart_items
```

Primary keys:

```text
id
```

Foreign keys:

```text
user_id
merchant_id
product_id
```

Timestamps:

```text
created_at
updated_at
```

Boolean fields:

```text
is_active
is_verified
```

---

# 5. Primary Key Strategy

Use UUIDs for application-level IDs.

Example:

```text
user.id
merchant.id
product.id
cart.id
quote.id
authorization.id
```

Reason:

```text
- hard to guess
- safer for public APIs
- easy to generate
- avoids exposing sequential database IDs
```

External Razorpay IDs remain separate:

```text
razorpay_order_id
razorpay_payment_id
```

Never use a Razorpay ID as our database primary key.

---

# 6. Timestamp Strategy

Use UTC timestamps in the database.

```text
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Application displays them in the user's appropriate timezone.

Never store ambiguous local timestamps.

---

# 7. Money Storage

Never use biginting-point database values for authoritative money.

Bad:

```text
BIGINT
DOUBLE
```

Preferred:

```text
BIGINT
```

with currency:

```text
currency CHAR(3)
```

Example:

```text
₹499.00

amount = 49900
currency = INR
```

Every monetary value must clearly represent minor units.

---

# 8. Currency Validation

Pydantic:

```python
from pydantic import BaseModel, Field, field_validator

class Money(BaseModel):
    amount: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()
```

Business layer can additionally restrict:

```text
supported currencies
```

For the initial implementation:

```text
INR
```

is sufficient if that matches the demo environment.

---

# 9. User Schema

Database:

```text
users
-------------------------
id UUID PK
email VARCHAR UNIQUE
password_hash TEXT
role VARCHAR
is_active BOOLEAN
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Roles:

```text
CUSTOMER
MERCHANT
ADMIN
```

Do not allow arbitrary role strings from the frontend.

---

# 10. User Pydantic Models

## UserCreate

```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
```

## UserResponse

Never return:

```text
password_hash
```

Example:

```python
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
```

---

# 11. Password Validation

Pydantic checks:

```text
length
basic format
```

Security service handles:

```text
hashing
verification
```

The database stores only:

```text
password_hash
```

Never:

```text
password
```

---

# 12. Merchant Schema

Database:

```text
merchants
-------------------------
id UUID PK
user_id UUID FK UNIQUE
name VARCHAR
description TEXT
is_active BOOLEAN
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Relationship:

```text
users
  1
  │
  │
  1
merchants
```

---

# 13. Merchant Pydantic Models

```python
class MerchantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
```

```python
class MerchantResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
```

---

# 14. Customer Schema

Database:

```text
customers
-------------------------
id UUID PK
user_id UUID FK UNIQUE
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Relationship:

```text
users
  1
  │
  │
  1
customers
```

A customer can have:

```text
many carts
many intents
many orders
many conversations
many preferences
```

---

# 15. Product Schema

Database:

```text
products
-------------------------
id UUID PK
merchant_id UUID FK
name VARCHAR
description TEXT
category VARCHAR
price BIGINT
currency CHAR(3)
is_active BOOLEAN
metadata JSONB
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Relationship:

```text
Merchant
   │
   ├── Product
   ├── Product
   └── Product
```

---

# 16. Product Constraints

Database:

```text
price >= 0
name NOT NULL
merchant_id NOT NULL
currency NOT NULL
```

Pydantic:

```python
class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(max_length=5000)
    category: str = Field(min_length=1, max_length=100)
    price: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

---

# 17. Product Metadata

Use JSONB for flexible attributes:

```json
{
  "anc": true,
  "battery_hours": 30,
  "color": "black"
}
```

Do NOT put core financial state only in metadata.

Bad:

```json
{
  "price": 4999,
  "inventory": 10
}
```

Price/inventory need authoritative columns/tables.

---

# 18. Inventory Schema

```text
inventory
-------------------------
id UUID PK
product_id UUID FK UNIQUE
available_quantity INTEGER
reserved_quantity INTEGER
updated_at TIMESTAMPTZ
```

Constraints:

```text
available_quantity >= 0
reserved_quantity >= 0
```

Relationship:

```text
Product
   │
   1
   │
   1
Inventory
```

---

# 19. Inventory Integrity

Never allow:

```text
available_quantity < 0
reserved_quantity < 0
```

When changing inventory:

```text
transaction
   ↓
row lock / atomic update
   ↓
validate quantity
   ↓
update
   ↓
commit
```

This protects against two customers buying the final item simultaneously.

---

# 20. Intent Schema

```text
intents
-------------------------
id UUID PK
customer_id UUID FK
merchant_id UUID FK
raw_text TEXT
structured_intent JSONB
status VARCHAR
created_at TIMESTAMPTZ
```

Example:

```json
{
  "category": "headphones",
  "max_budget": 500000,
  "requirements": ["ANC"],
  "delivery_deadline_days": 3
}
```

---

# 21. AI Intent Pydantic Model

```python
class BuyerIntent(BaseModel):
    category: str | None = Field(default=None, max_length=100)
    min_budget: int | None = Field(default=None, ge=0)
    max_budget: int | None = Field(default=None, ge=0)
    requirements: list[str] = Field(default_factory=list, max_length=20)
    delivery_deadline_days: int | None = Field(default=None, ge=0, le=365)
    preferences: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_budget(self):
        if (
            self.min_budget is not None
            and self.max_budget is not None
            and self.min_budget > self.max_budget
        ):
            raise ValueError("min_budget cannot exceed max_budget")
        return self
```

This is important because LLM output is untrusted.

---

# 22. Cart Schema

```text
carts
-------------------------
id UUID PK
customer_id UUID FK
merchant_id UUID FK
status VARCHAR
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Statuses:

```text
ACTIVE
CHECKOUT
COMPLETED
ABANDONED
EXPIRED
```

---

# 23. Cart Item Schema

```text
cart_items
-------------------------
id UUID PK
cart_id UUID FK
product_id UUID FK
quantity INTEGER
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Constraints:

```text
quantity > 0
```

> **Architecture Note:** `cart_items` deliberately stores only the product reference and quantity. It does NOT store `quoted_unit_price`. Price is resolved from the authoritative product data at the exact moment the quote is created. The quote itself is the authoritative monetary snapshot.

Pydantic:

```python
class CartItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0, le=100)
```

The maximum quantity is a business-configurable limit.

---

# 24. Cart Ownership

Every cart query must verify:

```text
cart.customer_id == authenticated_customer.id
```

Do not rely on:

```text
/cart/{cart_id}
```

alone.

---

# 25. Quote Schema

```text
quotes
-------------------------
id UUID PK
cart_id UUID FK
subtotal BIGINT
discount BIGINT
shipping BIGINT
tax BIGINT
total BIGINT
currency CHAR(3)
quote_hash VARCHAR
expires_at TIMESTAMPTZ
created_at TIMESTAMPTZ
```

All amounts:

```text
>= 0
```

---

# 26. Quote Validation

The backend calculates:

```text
subtotal
discount
shipping
tax
total
```

The frontend never submits the final total as authoritative data.

Pydantic request:

```python
class QuoteCreate(BaseModel):
    cart_id: UUID
```

No:

```python
amount: int
```

is required from the client.

---

# 27. Quote Calculation Invariant

The database/business layer must guarantee:

```text
total =
subtotal
- discount
+ shipping
+ tax
```

with appropriate lower-bound rules.

Example:

```text
subtotal = 500000
discount = 50000
shipping = 10000
tax = 0

total = 460000
```

---

# 28. Quote Expiration

Quote:

```text
created_at
expires_at
```

Validation:

```python
if datetime.now(timezone.utc) >= quote.expires_at:
    raise QuoteExpiredError()
```

Expired quotes cannot authorize payment.

---

# 29. Quote Snapshot

A quote should preserve the values used to calculate the amount.

Optional JSONB:

```text
line_items_snapshot
```

Example:

```json
[
  {
    "product_id": "uuid",
    "name": "Headphones",
    "unit_price": 499900,
    "quantity": 1
  }
]
```

This allows later auditing even if the product changes.

---

# 30. Policy Schema

```text
policies
-------------------------
id UUID PK
merchant_id UUID FK UNIQUE
max_autonomous_amount BIGINT
daily_autonomous_limit BIGINT
require_approval_above BIGINT
blocked_categories JSONB
is_ai_enabled BOOLEAN
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

All amount limits:

```text
>= 0
```

---

# 31. Policy Pydantic Model

```python
class PolicyUpdate(BaseModel):
    max_autonomous_amount: int = Field(ge=0)
    daily_autonomous_limit: int = Field(ge=0)
    require_approval_above: int = Field(ge=0)
    blocked_categories: list[str] = Field(default_factory=list, max_length=100)
    is_ai_enabled: bool = True
```

Business validation:

```text
require_approval_above
must not create contradictory limits
```

---

# 32. Authorization Schema

```text
authorizations
-------------------------
id UUID PK
customer_id UUID FK
quote_id UUID FK
amount BIGINT
status VARCHAR
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Statuses:

```text
PENDING
APPROVED
REVIEW_REQUIRED
BLOCKED
EXPIRED
CANCELLED
```

---

# 33. Authorization Invariants

Before:

```text
APPROVED
```

must verify:

```text
quote valid
amount valid
merchant policy allows
customer owns cart
inventory available
authorization not expired
```

Authorization amount must equal:

```text
quote.total
```

---

# 34. Order Schema

```text
orders
-------------------------
id UUID PK
merchant_id UUID FK
customer_id UUID FK
cart_id UUID FK
authorization_id UUID FK UNIQUE
razorpay_order_id VARCHAR UNIQUE
amount BIGINT
currency CHAR(3)
status VARCHAR
receipt VARCHAR UNIQUE
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

> **Idempotency Requirement:** `orders.authorization_id` MUST have a database-level `UNIQUE` constraint or an equivalent database-backed idempotency mechanism. Application-level "check then create" alone is insufficient because concurrent requests can race and accidentally create duplicate Razorpay orders.

Statuses:

```text
CREATED
ATTEMPTED
PAID
FAILED
CANCELLED
REFUNDED
REVIEW_REQUIRED
```

---

# 35. Order Amount Invariant

At creation:

```text
orders.amount
==
authorization.amount
==
quote.total
==
Razorpay Order amount
```

This must be checked before creating the external order.

---

# 36. Payment Schema

```text
payments
-------------------------
id UUID PK
order_id UUID FK
razorpay_payment_id VARCHAR UNIQUE
status VARCHAR
method VARCHAR
amount BIGINT
currency CHAR(3)
error_code VARCHAR
error_reason TEXT
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Statuses:

```text
CREATED
AUTHORIZED
CAPTURED
FAILED
REFUNDED
```

---

# 37. Payment Invariants

For a captured payment:

```text
payment.amount
==
order.amount
```

and:

```text
payment.razorpay_payment_id
is unique
```

Never allow two local payment records with the same Razorpay payment ID.

---

# 38. Webhook Event Schema

```text
webhook_events
-------------------------
id UUID PK
event_id VARCHAR UNIQUE
event_type VARCHAR
razorpay_order_id VARCHAR
razorpay_payment_id VARCHAR
payload JSONB
signature_verified BOOLEAN
processed BOOLEAN
processing_error TEXT
received_at TIMESTAMPTZ
processed_at TIMESTAMPTZ
```

The full raw payload may be retained subject to the project's data-retention policy.

---

# 39. Webhook Processing Model

```text
Webhook
 ↓
Raw body
 ↓
Signature verification
 ↓
Create webhook_events row
 ↓
Check event_id
 ↓
Process
 ↓
Update payment/order
 ↓
processed = true
```

If duplicate:

```text
event_id exists
 ↓
Do not execute business action again
```

---

# 40. Audit Event Schema

```text
audit_events
-------------------------
id UUID PK
actor_type VARCHAR
actor_id UUID NULL
merchant_id UUID NULL
event_type VARCHAR
entity_type VARCHAR
entity_id UUID NULL
event_data JSONB
created_at TIMESTAMPTZ
```

Examples:

```text
PRODUCT_CREATED
PRODUCT_UPDATED
POLICY_UPDATED
AUTHORIZATION_APPROVED
RAZORPAY_ORDER_CREATED
PAYMENT_CAPTURED
PAYMENT_FAILED
WEBHOOK_RECEIVED
```

---

# 41. Audit Event Model

```python
class AuditEventCreate(BaseModel):
    actor_type: ActorType
    actor_id: UUID | None = None
    merchant_id: UUID | None = None
    event_type: str = Field(min_length=1, max_length=100)
    entity_type: str = Field(min_length=1, max_length=100)
    entity_id: UUID | None = None
    event_data: dict[str, Any] = Field(default_factory=dict)
```

Audit creation should happen server-side.

Clients should not be allowed to fabricate audit events.

---

# 42. Conversation Schema

P2:

```text
conversations
-------------------------
id UUID PK
customer_id UUID FK
merchant_id UUID FK
state VARCHAR
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

---

# 43. Agent Run Schema

P2:

```text
agent_runs
-------------------------
id UUID PK
conversation_id UUID FK
agent_type VARCHAR
prompt_version VARCHAR
model VARCHAR
status VARCHAR
started_at TIMESTAMPTZ
completed_at TIMESTAMPTZ
```

This makes AI actions traceable.

---

# 44. Agent Tool Call Schema

P2:

```text
agent_tool_calls
-------------------------
id UUID PK
agent_run_id UUID FK
tool_name VARCHAR
input_json JSONB
output_json JSONB
status VARCHAR
created_at TIMESTAMPTZ
```

This provides:

```text
Agent
 ↓
Tool
 ↓
Input
 ↓
Output
```

auditability.

---

# 45. Customer Preference Schema

P2:

```text
customer_preferences
-------------------------
id UUID PK
customer_id UUID FK
key VARCHAR
value JSONB
confidence NUMERIC
source VARCHAR
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Confidence must be constrained:

```text
0 <= confidence <= 1
```

---

# 46. Product Relationship Schema

P2:

```text
product_relationships
-------------------------
id UUID PK
product_id UUID FK
related_product_id UUID FK
relationship_type VARCHAR
priority INTEGER
metadata JSONB
created_at TIMESTAMPTZ
```

Prevent:

```text
product_id == related_product_id
```

unless a specific future use case requires self-relation.

---

# 47. Offer Schema

P2:

```text
offers
-------------------------
id UUID PK
merchant_id UUID FK
product_id UUID FK
cart_id UUID FK
type VARCHAR
status VARCHAR
reason TEXT
score NUMERIC
created_at TIMESTAMPTZ
```

Offer status:

```text
CREATED
SHOWN
CLICKED
ACCEPTED
DISMISSED
EXPIRED
```

---

# 48. Campaign Schema

P2:

```text
campaigns
-------------------------
id UUID PK
merchant_id UUID FK
name VARCHAR
objective TEXT
status VARCHAR
start_at TIMESTAMPTZ
end_at TIMESTAMPTZ
budget BIGINT
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

---

# 49. Experiment Schema

P2:

```text
experiments
-------------------------
id UUID PK
merchant_id UUID FK
name VARCHAR
primary_metric VARCHAR
status VARCHAR
start_at TIMESTAMPTZ
end_at TIMESTAMPTZ
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Variants:

```text
experiment_variants
-------------------------
id UUID PK
experiment_id UUID FK
name VARCHAR
configuration JSONB
```

---

# 50. Event Schema

P2:

```text
events
-------------------------
id UUID PK
event_type VARCHAR
merchant_id UUID NULL
customer_id UUID NULL
entity_type VARCHAR
entity_id UUID NULL
metadata JSONB
created_at TIMESTAMPTZ
```

Examples:

```text
product.created
cart.created
quote.created
payment.captured
offer.shown
offer.accepted
simulation.completed
```

---

# 51. Risk Evaluation Schema

P2:

```text
risk_evaluations
-------------------------
id UUID PK
transaction_id UUID FK
score NUMERIC
decision VARCHAR
reasons JSONB
created_at TIMESTAMPTZ
```

Score constraint:

```text
0 <= score <= 1
```

Decision:

```text
ALLOW
REVIEW_REQUIRED
BLOCK
```

---

# 52. SQLAlchemy Model Design

Example:

```python
class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchants.id"),
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    price: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False
    )

    metadata: Mapped[dict] = mapped_column(
        JSONB,
        default=dict
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
```

---

# 53. Database Constraints

Database constraints should enforce rules that must never be violated.

Examples:

```text
price >= 0
quantity > 0
inventory >= 0
amount >= 0
confidence between 0 and 1
unique email
unique Razorpay order ID
unique Razorpay payment ID
unique webhook event ID
```

---

# 54. Foreign Keys

Use foreign keys for relationships:

```text
products.merchant_id
 → merchants.id

cart_items.cart_id
 → carts.id

orders.customer_id
 → customers.id

payments.order_id
 → orders.id
```

This prevents orphaned records.

---

# 55. Delete Strategy

Be careful with cascading deletes.

Do NOT blindly cascade-delete:

```text
orders
payments
audit_events
webhook_events
```

Financial/audit history should normally remain preserved.

Prefer:

```text
soft delete
```

for merchant/product records where appropriate.

Example:

```text
products.is_active = false
```

instead of deleting historical products.

---

# 56. Product Deactivation

If a product has historical transactions:

```text
DELETE product
```

is usually undesirable.

Instead:

```text
is_active = false
```

Historical orders continue referencing the product.

---

# 57. Order Snapshotting

Orders should preserve important transaction-time information.

Do not rely entirely on today's product table.

Store snapshots where appropriate:

```text
product name at purchase
unit price at purchase
quantity
discount
shipping
tax
currency
```

This prevents historical transactions changing when a merchant edits a product later.

---

# 58. Quote → Order Snapshot

Example:

```text
Quote:
Product = Headphones
Price = ₹4,999
Quantity = 1
```

Order snapshot:

```json
{
  "product_name": "Headphones",
  "unit_price": 499900,
  "quantity": 1
}
```

If the merchant later changes:

```text
Headphones = ₹5,999
```

the old order still shows:

```text
₹4,999
```

---

# 59. Database Transactions

Use DB transactions for atomic local state changes.

Example:

```text
BEGIN
 ↓
Create authorization
 ↓
Reserve inventory
 ↓
Create order
 ↓
COMMIT
```

If any operation fails:

```text
ROLLBACK
```

External API calls should not unnecessarily hold open DB transactions.

---

# 60. Inventory Transaction

Example:

```sql
UPDATE inventory
SET available_quantity = available_quantity - :qty,
    reserved_quantity = reserved_quantity + :qty
WHERE product_id = :product_id
  AND available_quantity >= :qty;
```

Then check:

```text
rows_affected == 1
```

If:

```text
0
```

then inventory was insufficient.

This is safer than:

```text
SELECT quantity
→ Python check
→ UPDATE
```

without concurrency protection.

---

# 61. Quote Creation Transaction

```text
BEGIN
 ↓
Read cart
 ↓
Lock / validate inventory
 ↓
Read current prices
 ↓
Calculate quote
 ↓
Insert quote
 ↓
COMMIT
```

The quote is then immutable.

If the cart changes:

```text
old quote remains historical
new quote created
```

---

# 62. Immutable Financial Records

Do not freely edit:

```text
quotes
completed orders
captured payments
audit events
```

If something needs correction:

```text
new record / correction event
```

rather than silently modifying history.

---

# 63. Pydantic Schema Categories

Keep schemas separated.

```text
schemas/
│
├── auth.py
├── user.py
├── merchant.py
├── product.py
├── inventory.py
├── buyer.py
├── cart.py
├── quote.py
├── policy.py
├── authorization.py
├── order.py
├── payment.py
├── webhook.py
├── audit.py
├── conversation.py
├── agent.py
├── offer.py
├── campaign.py
├── experiment.py
└── risk.py
```

---

# 64. Never Reuse One Schema Everywhere

Do not create:

```text
ProductSchema
```

and use it for:

```text
create
update
response
AI
database
```

Instead:

```text
ProductCreate
ProductUpdate
ProductResponse
ProductInternal
ProductAgentView
```

This prevents accidental field exposure.

---

# 65. Product Pydantic Schemas

## Create

```python
class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(max_length=5000)
    category: str = Field(min_length=1, max_length=100)
    price: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

## Update

```python
class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    category: str | None = Field(default=None, max_length=100)
    price: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    metadata: dict[str, Any] | None = None
```

## Response

```python
class ProductResponse(BaseModel):
    id: UUID
    name: str
    description: str
    category: str
    price: int
    currency: str
    is_active: bool
    metadata: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
```

---

# 66. Pydantic Does Not Replace Business Logic

Pydantic can check:

```text
price >= 0
quantity > 0
string length
valid UUID
valid email
valid enum
```

Business services check:

```text
merchant owns product
quote belongs to cart
customer owns cart
product is active
inventory is available
policy allows transaction
authorization is valid
```

PostgreSQL checks:

```text
foreign keys
unique constraints
NOT NULL
CHECK constraints
```

---

# 67. Three-Layer Validation Model

```text
               REQUEST
                  │
                  ▼
        ┌──────────────────┐
        │ Pydantic         │
        │ Shape + Type     │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ Service Layer    │
        │ Business Rules  │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ PostgreSQL       │
        │ Integrity        │
        └──────────────────┘
```

---

# 68. AI Data Validation

LLM output must pass through:

```text
LLM
 ↓
JSON schema
 ↓
Pydantic
 ↓
Business validation
 ↓
Database / service
```

Example:

```text
LLM says:

max_budget = -1000
```

Pydantic:

```text
REJECT
```

LLM says:

```text
product_id = random UUID
```

Pydantic may accept the UUID shape.

Business layer must then check:

```text
Does product exist?
Does it belong to this merchant?
Is it active?
```

---

# 69. AI Tool Input Validation

Every tool has its own Pydantic schema.

Example:

```python
class SearchProductsInput(BaseModel):
    category: str | None = None
    max_budget: int | None = Field(default=None, ge=0)
    requirements: list[str] = Field(default_factory=list)
```

Tool execution:

```text
Agent
 ↓
Tool input schema
 ↓
Business validation
 ↓
Tool
```

---

# 70. Enum Design

Use enums for controlled states.

Example:

```python
class OrderStatus(str, Enum):
    CREATED = "CREATED"
    ATTEMPTED = "ATTEMPTED"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
```

Avoid arbitrary strings throughout the application.

---

# 71. State Transition Service

Do not expose generic status updates.

Bad:

```http
PATCH /orders/{id}

{
  "status": "PAID"
}
```

Good:

```python
order_service.mark_paid(
    order_id=order_id,
    payment_id=payment_id
)
```

The service verifies the transition.

---

# 72. Repository Pattern

Example:

```python
class ProductRepository:

    async def get_by_id(self, product_id: UUID):
        ...

    async def get_for_merchant(
        self,
        product_id: UUID,
        merchant_id: UUID
    ):
        ...

    async def create(self, product: Product):
        ...

    async def update(self, product: Product):
        ...
```

The repository handles persistence.

The service handles business decisions.

---

# 73. Service Pattern

Example:

```python
class ProductService:

    async def update_product(
        self,
        merchant_id: UUID,
        product_id: UUID,
        data: ProductUpdate
    ):
        product = await repo.get_for_merchant(
            product_id,
            merchant_id
        )

        if not product:
            raise NotFoundError()

        # Business rules

        return await repo.update(product)
```

---

# 74. Database Session Management

FastAPI:

```text
Request
 ↓
DB Session
 ↓
Service
 ↓
Repository
 ↓
Commit / Rollback
 ↓
Close
```

Never maintain one global mutable SQLAlchemy session across users.

---

# 75. Migration Strategy

Use Alembic.

Example:

```bash
alembic revision --autogenerate -m "create products"
```

Then:

```bash
alembic upgrade head
```

Never manually change production schema without a migration.

---

# 76. Migration Rules

Every schema change:

```text
Code change
 ↓
Migration
 ↓
Test migration
 ↓
Apply
```

Before demo:

```bash
alembic upgrade head
```

---

# 77. Index Strategy

Index frequently queried fields.

Examples:

```text
users.email
products.merchant_id
products.category
inventory.product_id
carts.customer_id
orders.merchant_id
orders.customer_id
orders.razorpay_order_id
payments.razorpay_payment_id
webhook_events.event_id
events.merchant_id
events.created_at
```

Do not index every column blindly.

---

# 78. Composite Indexes

Useful examples:

```text
products(merchant_id, is_active)
orders(merchant_id, created_at)
events(merchant_id, created_at)
```

This helps common merchant dashboard queries.

---

# 79. Unique Constraints

Important:

```text
users.email UNIQUE

merchants.user_id UNIQUE

customers.user_id UNIQUE

inventory.product_id UNIQUE

orders.razorpay_order_id UNIQUE

orders.receipt UNIQUE

payments.razorpay_payment_id UNIQUE

webhook_events.event_id UNIQUE
```

Database-level uniqueness is stronger than application-only checks.

---

# 80. Check Constraints

Examples:

```text
price >= 0
amount >= 0
quantity > 0
available_quantity >= 0
reserved_quantity >= 0
confidence BETWEEN 0 AND 1
```

Use PostgreSQL CHECK constraints where practical.

---

# 81. Merchant Isolation at Query Level

Every merchant-scoped query should include:

```text
merchant_id = authenticated_merchant_id
```

Example:

```python
select(Product).where(
    Product.id == product_id,
    Product.merchant_id == merchant_id
)
```

Never:

```python
select(Product).where(Product.id == product_id)
```

and assume authorization was checked somewhere else.

---

# 82. Customer Isolation

Same principle:

```python
select(Cart).where(
    Cart.id == cart_id,
    Cart.customer_id == customer_id
)
```

This prevents ID-based horizontal privilege escalation.

---

# 83. AI Tenant Isolation

When constructing AI context:

```text
merchant_id
customer_id
conversation_id
```

must be explicit.

Only retrieve:

```text
current merchant's products
current merchant's policies
current customer's allowed preferences
```

Never use a global catalogue context accidentally.

---

# 84. Database and AI Separation

AI should never receive the entire database.

Instead:

```text
Database
 ↓
Repository
 ↓
Relevant structured data
 ↓
AI
```

Example:

```text
50,000 products
```

should not become:

```text
50,000 products in prompt
```

Use:

```text
filters
search
ranking
retrieval
```

first.

---

# 85. JSONB Rules

Use JSONB for:

```text
flexible metadata
AI structured intent
audit event data
event metadata
campaign configuration
experiment configuration
```

Do not use JSONB for everything.

Avoid putting authoritative relational fields into JSONB when they need:

```text
constraints
indexes
joins
financial guarantees
```

---

# 86. Data Retention

Define retention policies for:

```text
audit
webhooks
agent runs
tool calls
conversations
events
```

Do not keep data forever without a reason.

For the hackathon, retention can be simple, but the architecture should make future retention/deletion policies possible.

---

# 87. Soft Delete Strategy

Use soft deletion for entities where history matters:

```text
products
merchants
campaigns
```

Example:

```text
is_active = false
```

Do not soft-delete financial records in a way that makes them disappear from audit/reporting.

---

# 88. Transactional Event Pattern

When a business action changes state:

```text
DB transaction
   ↓
State change
   ↓
Create internal event
   ↓
Commit
```

Example:

```text
Payment captured
 ↓
Update payment
 ↓
Update order
 ↓
Insert event
 ↓
Insert audit
 ↓
COMMIT
```

If commit fails:

```text
nothing is considered locally completed
```

---

# 89. Outbox Pattern — Future

For higher reliability:

```text
Business Transaction
       ↓
DB State Change
       +
Outbox Event
       ↓
COMMIT
       ↓
Worker
       ↓
External Event System
```

P2 can introduce this if event-driven architecture becomes necessary.

For the hackathon:

```text
PostgreSQL events table
```

is sufficient.

---

# 90. Payment Webhook Database Flow

```text
Razorpay
   ↓
Webhook
   ↓
Verify signature
   ↓
BEGIN
   ↓
Insert webhook event
   ↓
Check duplicate
   ↓
Find local order
   ↓
Validate amount
   ↓
Validate state transition
   ↓
Update payment
   ↓
Update order
   ↓
Insert audit event
   ↓
COMMIT
```

If duplicate:

```text
ROLLBACK / no-op
```

depending on implementation.

---

# 91. Reconciliation Data

Store enough IDs to connect:

```text
customer
merchant
cart
quote
authorization
local order
Razorpay order
payment
Razorpay payment
webhook event
audit event
```

This creates:

```text
Complete Transaction Graph
```

---

# 92. Complete Transaction Graph

```text
Customer
   │
   ▼
Intent
   │
   ▼
Cart
   │
   ▼
Quote
   │
   ▼
Authorization
   │
   ▼
Local Order
   │
   ▼
Razorpay Order
   │
   ▼
Payment
   │
   ▼
Webhook Event
   │
   ▼
Audit Event
```

A support/debugging process should be able to traverse this chain.

---

# 93. Data Validation Checklist

## API

```text
[ ] Pydantic schema
[ ] enum validation
[ ] length validation
[ ] numeric bounds
[ ] UUID validation
[ ] email validation
```

## Business

```text
[ ] ownership
[ ] merchant isolation
[ ] customer isolation
[ ] inventory
[ ] quote validity
[ ] policy
[ ] authorization
```

## Database

```text
[ ] NOT NULL
[ ] FK
[ ] UNIQUE
[ ] CHECK
[ ] indexes
```

---

# 94. Financial Integrity Checklist

```text
[ ] integer minor-unit money
[ ] no bigint calculations
[ ] authoritative quote
[ ] quote expiry
[ ] order amount = quote amount
[ ] payment amount = order amount
[ ] unique Razorpay IDs
[ ] webhook idempotency
[ ] state transitions
[ ] immutable history
[ ] audit trail
```

---

# 95. AI Data Integrity Checklist

```text
[ ] LLM output validated
[ ] structured output only
[ ] AI cannot provide authoritative price
[ ] AI cannot directly mutate DB
[ ] AI cannot directly call Razorpay
[ ] tool input validated
[ ] merchant context isolated
[ ] customer context isolated
[ ] prompt injection treated as untrusted input
[ ] agent actions auditable
```

---

# 96. Recommended Backend Structure

```text
backend/
└── app/
    │
    ├── api/
    │   ├── auth.py
    │   ├── buyer.py
    │   ├── catalog.py
    │   ├── cart.py
    │   ├── quote.py
    │   ├── policy.py
    │   ├── authorization.py
    │   ├── checkout.py
    │   ├── merchant.py
    │   ├── optimization.py
    │   └── webhooks.py
    │
    ├── models/
    │   ├── user.py
    │   ├── merchant.py
    │   ├── customer.py
    │   ├── product.py
    │   ├── inventory.py
    │   ├── cart.py
    │   ├── quote.py
    │   ├── policy.py
    │   ├── authorization.py
    │   ├── order.py
    │   ├── payment.py
    │   ├── webhook.py
    │   ├── audit.py
    │   └── ...
    │
    ├── schemas/
    │   ├── auth.py
    │   ├── product.py
    │   ├── buyer.py
    │   ├── cart.py
    │   ├── quote.py
    │   ├── payment.py
    │   └── ...
    │
    ├── services/
    │   ├── auth_service.py
    │   ├── catalog_service.py
    │   ├── buyer_service.py
    │   ├── cart_service.py
    │   ├── quote_service.py
    │   ├── policy_service.py
    │   ├── authorization_service.py
    │   ├── payment_service.py
    │   ├── webhook_service.py
    │   └── audit_service.py
    │
    ├── repositories/
    │   ├── user_repository.py
    │   ├── product_repository.py
    │   ├── order_repository.py
    │   └── ...
    │
    ├── agents/
    ├── optimization/
    ├── db/
    │   ├── database.py
    │   └── migrations/
    │
    └── main.py
```

---

# 97. Final Data Flow

```text
                 FRONTEND
                    │
                    ▼
             Pydantic Schema
                    │
                    ▼
              API Endpoint
                    │
                    ▼
              Service Layer
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
   Business Validation    AI Adapter
          │                   │
          │              Structured Output
          │                   │
          └─────────┬─────────┘
                    ▼
                Repository
                    │
                    ▼
                SQLAlchemy
                    │
                    ▼
                PostgreSQL
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
      State Data          Audit/Event
```

---

# 98. Final Transaction Data Flow

```text
Customer
   ↓
Intent
   ↓
Catalogue
   ↓
Cart
   ↓
Quote
   ↓
Policy
   ↓
Authorization
   ↓
Local Order
   ↓
Razorpay Order
   ↓
Payment
   ↓
Webhook
   ↓
Verified Payment
   ↓
Order = PAID
   ↓
Audit + Event
```

At every step:

```text
Pydantic
    +
Business validation
    +
Database constraints
```

protect the state.

---

# 99. Most Important Database Rules

```text
1. PostgreSQL is the source of truth for application state.

2. Razorpay remains the external authority for payment state.

3. Pydantic validates API boundaries.

4. Service layers validate business rules.

5. PostgreSQL enforces hard integrity constraints.

6. Never use bigints for authoritative money.

7. Never trust frontend financial values.

8. Never let AI directly mutate financial state.

9. Keep merchant data isolated.

10. Keep customer data isolated.

11. Preserve transaction-time snapshots.

12. Do not casually delete financial/audit records.

13. Use unique constraints for external payment IDs.

14. Make webhook processing idempotent.

15. Validate every state transition.

16. Use transactions for atomic local state changes.

17. Use migrations for schema evolution.

18. Keep AI context structured and tenant-scoped.

19. Keep audit events server-generated.

20. Design the database so one transaction can be traced end-to-end.
```

---

# 100. Final Database Architecture

```text
                           APPLICATION
                               │
                               ▼
                        ┌──────────────┐
                        │ FastAPI API  │
                        └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  Pydantic    │
                        │  Validation  │
                        └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │   Services   │
                        │              │
                        │ Business     │
                        │ Validation   │
                        └──────┬───────┘
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
          ┌──────────────┐            ┌──────────────┐
          │ Repositories │            │ AI Services  │
          └──────┬───────┘            └──────────────┘
                 │
                 ▼
          ┌─────────────────────────────────────────┐
          │                PostgreSQL                │
          │                                         │
          │ Users       Merchants      Customers    │
          │ Products    Inventory      Cart         │
          │ Quotes      Policies       Authorization│
          │ Orders      Payments       Webhooks     │
          │ Audit       Events         AI State     │
          └────────────────────┬────────────────────┘
                               │
                               ▼
                       Transaction Graph
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
          Analytics          Audit          Reconciliation
```

---

# 101. North Star

The database should make it possible to answer one question at any time:

> **"Exactly what happened in this transaction, what data caused it, which agent/tool acted, which rules allowed it, what amount was authorized, and what external payment event confirmed it?"**

If the database can answer that reliably, the system becomes significantly easier to:

```text
debug
secure
audit
scale
demonstrate
trust
```

The database is not merely storage.

It is the **state and integrity backbone of the entire AI-commerce system**.


## September 4 Update
- `price` field in `products` is authoritative and strictly treated as minor units (paise) across all backend calculations.
- `Inventory.available_quantity` is authoritatively joined via a single query for simulation. A `None` value represents unmanaged inventory (no friction).