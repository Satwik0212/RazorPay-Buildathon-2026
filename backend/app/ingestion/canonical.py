"""
Canonical field definitions for GraahakLens Catalogue Ingestion.

This module defines the authoritative list of canonical product fields,
their aliases from common merchant CSV formats, and which fields are
platform-owned (never mappable from uploaded CSVs).
"""
from typing import Dict, List, Set, Optional


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE CATALOGUE FIELDS
# ─────────────────────────────────────────────────────────────────────────────

CANONICAL_SOURCE_FIELDS: Dict[str, str] = {
    "product_name":            "Product name or title",
    "description":             "Long-form product description",
    "category":                "Product category or type",
    "brand":                   "Brand or manufacturer name",
    "retail_price":            "Original/MRP price (numeric, in rupees)",
    "discounted_price":        "Selling/discounted price (numeric, in rupees)",
    "product_rating":          "Customer rating (numeric, 0-5)",
    "image":                   "Product image URL or JSON list of URLs",
    "product_specifications":  "Structured product specifications / attributes",
    "source_product_id":       "Unique identifier from the source system",
    "inventory":               "Available quantity in stock",
}

# ─────────────────────────────────────────────────────────────────────────────
# PLATFORM-OWNED FIELDS — NEVER mappable from CSV
# ─────────────────────────────────────────────────────────────────────────────

PLATFORM_OWNED_FIELDS: Set[str] = {
    "merchant_id",
    "id",
    "is_active",
    "currency",
    "created_at",
    "updated_at",
}

# ─────────────────────────────────────────────────────────────────────────────
# KNOWN ALIASES — For deterministic fast-path mapping
# ─────────────────────────────────────────────────────────────────────────────

KNOWN_ALIASES: Dict[str, str] = {
    # product_name
    "product_name": "product_name",
    "name": "product_name",
    "title": "product_name",
    "item_title": "product_name",
    "item_name": "product_name",
    "product_title": "product_name",
    "product name": "product_name",
    # description
    "description": "description",
    "details": "description",
    "desc": "description",
    "about": "description",
    "product_description": "description",
    "long_description": "description",
    "product description": "description",
    # category
    "category": "category",
    "product_category": "category",
    "category_path": "category",
    "cat": "category",
    "product_category_tree": "category",
    # brand
    "brand": "brand",
    "brand_name": "brand",
    "manufacturer": "brand",
    "company": "brand",
    "make": "brand",
    # retail_price
    "retail_price": "retail_price",
    "mrp": "retail_price",
    "original_price": "retail_price",
    "list_price": "retail_price",
    "full_price": "retail_price",
    "regular_price": "retail_price",
    "market_price": "retail_price",
    # discounted_price
    "discounted_price": "discounted_price",
    "selling_price": "discounted_price",
    "sale_price": "discounted_price",
    "offer_price": "discounted_price",
    "price": "discounted_price",
    "final_price": "discounted_price",
    "net_price": "discounted_price",
    # product_rating
    "product_rating": "product_rating",
    "rating": "product_rating",
    "star_rating": "product_rating",
    "average_rating": "product_rating",
    "customer_rating": "product_rating",
    "overall_rating": "product_rating",
    # image
    "image": "image",
    "image_url": "image",
    "images": "image",
    "photo": "image",
    "thumbnail": "image",
    "image_link": "image",
    "picture": "image",
    # product_specifications
    "product_specifications": "product_specifications",
    "specifications": "product_specifications",
    "specs": "product_specifications",
    "features": "product_specifications",
    "attributes": "product_specifications",
    "product_details": "product_specifications",
    # source_product_id
    "uniq_id": "source_product_id",
    "sku": "source_product_id",
    "product_id": "source_product_id",
    "pid": "source_product_id",
    "item_id": "source_product_id",
    "code": "source_product_id",
    "barcode": "source_product_id",
    # inventory
    "inventory": "inventory",
    "qty": "inventory",
    "stock_count": "inventory",
    "quantity": "inventory",
    "stock": "inventory",
    "available": "inventory",
    "available_qty": "inventory",
    "available_quantity": "inventory",
    "in_stock": "inventory",
}

# Headers that indicate the canonical Flipkart PromptCloudHQ schema
FLIPKART_CANONICAL_HEADERS: Set[str] = {
    "uniq_id", "crawl_timestamp", "product_url", "product_name",
    "product_category_tree", "pid", "retail_price", "discounted_price",
    "image", "is_fk_advantage_product", "description", "product_rating",
    "overall_rating", "brand", "product_specifications",
}

REQUIRED_CANONICAL_FIELDS: Set[str] = {"product_name"}
PRICE_CANONICAL_FIELDS: Set[str] = {"retail_price", "discounted_price"}


def get_canonical_field_for_alias(header: str) -> Optional[str]:
    """Case-insensitive alias lookup. Returns None if not recognized."""
    return KNOWN_ALIASES.get(header.strip().lower())


def is_platform_owned(field: str) -> bool:
    """Returns True if the field is platform-owned."""
    return field.strip().lower() in PLATFORM_OWNED_FIELDS


def get_all_canonical_field_names() -> List[str]:
    """Returns the list of all valid canonical source field names."""
    return list(CANONICAL_SOURCE_FIELDS.keys())