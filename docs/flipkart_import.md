# Flipkart Dataset Import Documentation

## Dataset Source
The source data for this demo catalogue originates from the **PromptCloudHQ "Flipkart Products" dataset**. It contains approximately 20,000 real e-commerce product records originally crawled from Flipkart.com.

## Data Distinction: Source vs Demo Environment
This project explicitly distinguishes between original dataset values and fabricated demo states:
- **Source Data**: Product name, category tree, descriptions, brand, specifications, image URLs, original retail prices, discounted prices, and product ratings.
- **Demo-Environment Data**: Inventory quantities, active status, and merchant assignments. **These are simulated for the demo environment and are NOT claimed to originate from Flipkart.**

## Category Selection
To ensure meaningful behavior for the AI simulation, upsell, cross-sell, and campaign engines, the importer selectively targets high-density categories that naturally support rich metadata and related products.

Categories imported:
- Mobiles & Accessories
- Computers
- Cameras & Accessories
- Watches
- Beauty and Personal Care
- Home Decor & Festive Needs

## Field Mappings
- `product_name` -> `Product.name`
- `description` -> `Product.description`
- `product_category_tree` -> `Product.category` (Normalized to the top-level category)
- `discounted_price` (fallback to `retail_price`) -> `Product.price` (Converted from INR to minor units/paise)
- `product_specifications` -> Parsed from Ruby-hash syntax (`=>`) into structured JSON stored in `Product.product_metadata["specifications"]`
- `uniq_id` -> `Product.product_metadata["source_product_id"]` (Used for idempotency)
- `image` -> Extracted as a list of strings into `Product.product_metadata["image_urls"]`

## Fields Intentionally Ignored
- `product_url`, `pid`, `is_FK_Advantage_product`, and `crawl_timestamp` were skipped to prevent bloating the database with Flipkart-specific internal routing parameters. 

## Duplicate Handling
- Duplicate product names within the source CSV were eliminated. The importer prioritizes the first encountered record for any given product name.
- Any row lacking a valid, parsable price > 0 was automatically rejected.

## Inventory Strategy
The Flipkart dataset does not provide accurate current inventory. Thus, inventory initialization is an explicit application-level choice:
- `--inventory-mode demo`: Initializes a deterministic pseudorandom quantity (based on the product name's length) to ensure the product is in-stock and usable by the Simulation, Upsell, and Campaign engines.
- `--inventory-mode zero`: Initializes all imported inventory to 0.

## Importer Command
To run the importer with deterministic demo inventory:
```bash
python backend/scripts/import_flipkart_data.py --inventory-mode demo
```

You may optionally specify a specific merchant UUID using `--merchant-id <uuid>`. By default, it targets the first available merchant in the database.

## Re-import Behavior (Idempotency)
The importer is fully idempotent. On repeated executions, it checks the database for existing records by `product_name` and `merchant_id`. If a record already exists, it safely skips the insertion, preventing duplicate data accumulation.

## Known Limitations
- The parser discards specifications that do not strictly follow the `{"key"=>"...", "value"=>"..."}` format found in the dataset.
- Because duplicate names are dropped immediately, if the first occurrence of a product name in the CSV is missing a price, the entire product name is permanently excluded from that import run.


## September 4 Update
- No changes to Flipkart ingestion, but imported metadata (like `product_rating` vs `overall_rating` or descriptive `warranty`) is now aggressively normalized in `MetadataNormalizer` before simulation.