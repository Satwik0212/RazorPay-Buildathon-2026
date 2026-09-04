# Document 6: CATALOGUE_SCHEMA
> What product data exists, what is populated, what is used.

---

## A. Product SQLAlchemy Model

**Source:** `backend/app/models/product.py`

```python
class Product(ModelBase):
    __tablename__ = "products"

    merchant_id: Mapped[uuid.UUID]  # FK to merchants.id, indexed, NOT NULL
    name: Mapped[str]               # String(255), indexed, NOT NULL
    description: Mapped[str]        # Text, default="", NOT NULL
    category: Mapped[str]           # String(100), indexed, NOT NULL
    price: Mapped[int]              # BigInteger (PAISE), NOT NULL
    currency: Mapped[str]           # String(3), default="INR", NOT NULL
    is_active: Mapped[bool]         # Boolean, default=True, indexed, NOT NULL
    product_metadata: Mapped[Dict]  # JSON column (DB alias: "metadata"), default={}, NOT NULL

    # Relationships
    inventory: Inventory            # one-to-one, cascade delete-orphan

class Inventory(ModelBase):
    __tablename__ = "inventory"

    product_id: Mapped[uuid.UUID]       # FK to products.id, UNIQUE, NOT NULL
    available_quantity: Mapped[int]     # Integer, default=0, NOT NULL
    reserved_quantity: Mapped[int]      # Integer, default=0, NOT NULL
```

**Notes:**
- `product_metadata` is a flexible JSON blob (Python dict). No enforced sub-schema.
- `price` is stored in **paise** (minor units). ₹10,000 = 1,000,000.
- `reserved_quantity` exists but is never written by any service (always 0).

---

## B. Product Metadata Structure

No enforced JSON schema. Fields discovered from Flipkart import + seeding:

```json
{
  "brand": "Sony",
  "rating": 4.5,
  "product_rating": 4.5,
  "overall_rating": 4.5,
  "delivery_days": 3,
  "return_days": 7,
  "returnable": true,
  "return_policy": true,
  "warranty": "1 year manufacturer warranty",
  "discount_percent": 15,
  "has_offer": true,
  "has_discount": true,
  "high_quality": true,
  "premium": false,
  "specifications": {
    "color": "Black",
    "connectivity": "Bluetooth 5.0",
    "battery_life": "30 hours"
  },
  "image_urls": ["https://..."],
  "highlights": ["Noise Cancelling", "30hr Battery"]
}
```

---

## C. Field Population Status

| Field | In Schema? | Populated in Seed/Import? | Used by Simulation? | Used by Search? |
|---|---|---|---|---|
| `name` | YES | YES (100%) | YES (text match) | YES |
| `description` | YES | YES (~90%, some empty) | YES (friction + metadata_score) | YES (ilike search) |
| `category` | YES | YES (100%) | NO | YES (filter) |
| `price` | YES | YES (100%) | YES (hard constraint + score) | YES (filter) |
| `currency` | YES | YES (all INR) | NO | NO |
| `is_active` | YES | YES | YES (hard constraint) | YES (filter) |
| `metadata.rating` / `product_rating` / `overall_rating` | YES | PARTIAL (~70-80% from Flipkart) | YES (normalized) | NO |
| `metadata.delivery_days` | YES | PARTIAL (~40% from Flipkart data) | YES (hard constraint + score) | NO |
| `metadata.return_days` | YES | PARTIAL (~30%) | YES (score) | NO |
| `metadata.warranty` | YES | PARTIAL (descriptive strings, e.g. "1 year") | YES (normalized) | NO |
| `metadata.discount_percent` | YES | PARTIAL | YES (offer score) | NO |
| `metadata.specifications` | YES | YES (Flipkart import) | PARTIAL (warranty lookup only) | NO |
| `metadata.image_urls` | YES | YES (Flipkart) | NO | NO |
| `metadata.highlights` | YES | YES (Flipkart) | NO | NO |
| `inventory.available_quantity` | YES | YES (100% have records) | YES (hard constraint) | NO |
| `inventory.reserved_quantity` | YES | YES but always 0 | NO | NO |

---

## D. Search / Retrieval Patterns

| Method | File | Line | Query Type | Limit |
|---|---|---|---|---|
| `ProductRepository.list_products()` | `product_repository.py` | 20 | SQL SELECT + filters + LIMIT/OFFSET | Default 20, max 100 |
| `ProductRepository.get_active_catalogue_for_merchant()` | `product_repository.py` | 58 | Core column SELECT + LEFT JOIN inventory WHERE is_active=True ORDER BY id | None (ALL active) |
| `ProductService.list_products()` | `product_service.py` | 188 | Delegates to repo.list_products() | Configurable |
| `/catalogue/search` | `intents.py` | 44 | `list_products(category=X, max_price=Y, is_active=True, limit=50)` | Hard 50 |
| `ProductRepository.get_by_id()` | `product_repository.py` | 12 | SELECT + joinedload inventory | Single |

**Indexing:** `products.name (index)`, `products.category (index)`, `products.is_active (index)`, `products.merchant_id (index)`.
Search by name uses `ilike("%search%")` — no full-text search index.

---

## E. Data Sources

| Source | File | What it Creates |
|---|---|---|
| Flipkart CSV import | `backend/app/services/flipkart_import_service.py` | 2,977 products with rich metadata (brand, rating, specs, images) |
| Manual seed / ProductCreate API | `backend/app/api/v1/products.py` | Merchant-created products with minimal metadata |
| `ProductRepository.create_product()` | `product_repository.py:105` | Always creates an `Inventory` record with `initial_quantity=10` (default) |

**Computed fields:** None. All fields stored directly. Scores/rankings are computed at simulation time and NOT persisted per product.
