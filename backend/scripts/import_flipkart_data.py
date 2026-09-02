import os
import sys
import csv
import ast
import re
import argparse
import logging
from typing import Dict, Any

# Adjust path to import from app
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.product import Product, Inventory
from app.models.merchant import Merchant

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

TARGET_CATEGORIES = {
    "Mobiles & Accessories",
    "Computers",
    "Cameras & Accessories",
    "Watches",
    "Beauty and Personal Care",
    "Home Decor & Festive Needs"
}

def parse_specs(spec_str: str) -> Dict[str, str]:
    if not spec_str or spec_str == '{"product_specification"=>[]}':
        return {}
    results = {}
    for match in re.finditer(r'"key"\s*=>\s*"(.*?)",\s*"value"\s*=>\s*"(.*?)"', spec_str):
        results[match.group(1)] = match.group(2)
    return results

def main():
    parser = argparse.ArgumentParser(description="Import Flipkart Dataset")
    parser.add_argument("--inventory-mode", choices=["demo", "zero"], default="zero",
                        help="demo: deterministically populate inventory, zero: initialize to 0")
    parser.add_argument("--merchant-id", type=str, help="UUID of the demo merchant to assign products to")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.merchant_id:
            merchant = db.execute(select(Merchant).filter_by(id=args.merchant_id)).scalar_one_or_none()
        else:
            # Look up by the demo user email to guarantee deterministic ownership
            from app.models.merchant import User
            demo_user = db.execute(select(User).filter_by(email='merchant@demo.com')).scalar_one_or_none()
            if demo_user:
                merchant = db.execute(select(Merchant).filter_by(user_id=demo_user.id)).scalar_one_or_none()
            else:
                merchant = db.execute(select(Merchant)).scalars().first()
        
        if not merchant:
            logging.error("No merchant found in database. Run seed_demo_data.py first.")
            sys.exit(1)

        logging.info(f"Using Merchant: {merchant.name} (ID: {merchant.id})")
        logging.info(f"Inventory Mode: {args.inventory_mode}")

        file_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "flipkart_com-ecommerce_sample.csv")
        if not os.path.exists(file_path):
            logging.error(f"Dataset not found at {file_path}")
            sys.exit(1)

        csv.field_size_limit(2147483647)
        
        stats = {
            "source_rows": 0,
            "valid_rows": 0,
            "skipped_missing_price": 0,
            "skipped_category": 0,
            "skipped_duplicates_in_csv": 0,
            "newly_inserted": 0,
            "already_present": 0
        }

        seen_product_names = set()
        
        with open(file_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                stats["source_rows"] += 1
                
                # Category Filter
                cat_tree_str = row.get("product_category_tree", "")
                try:
                    cat_list = ast.literal_eval(cat_tree_str)
                    if not cat_list:
                        stats["skipped_category"] += 1
                        continue
                    top_cat = cat_list[0].split(' >> ')[0].strip()
                except:
                    stats["skipped_category"] += 1
                    continue
                
                if top_cat not in TARGET_CATEGORIES:
                    stats["skipped_category"] += 1
                    continue

                product_name = row.get("product_name", "").strip()
                if not product_name or product_name in seen_product_names:
                    stats["skipped_duplicates_in_csv"] += 1
                    continue
                seen_product_names.add(product_name)

                # Price resolution
                discounted_price_str = row.get("discounted_price", "").strip()
                retail_price_str = row.get("retail_price", "").strip()
                
                price_val = None
                if discounted_price_str and discounted_price_str.isdigit():
                    price_val = int(discounted_price_str)
                elif retail_price_str and retail_price_str.isdigit():
                    price_val = int(retail_price_str)
                
                if price_val is None or price_val <= 0:
                    stats["skipped_missing_price"] += 1
                    continue
                
                stats["valid_rows"] += 1

                # Source identity for idempotency
                uniq_id = row.get("uniq_id", "")
                
                # Check idempotency in DB by uniq_id in JSON metadata
                # Using a basic query check. We'll do it by exact product name in DB or uniq_id.
                # Actually, filtering by JSON in sqlite/pg can be tricky if we don't want to use specific dialects.
                # We can query by product_name for this merchant as a proxy for existence.
                existing = db.execute(
                    select(Product).filter(
                        Product.merchant_id == merchant.id,
                        Product.name == product_name
                    )
                ).scalar_one_or_none()

                if existing:
                    stats["already_present"] += 1
                    continue

                # Prepare Metadata
                specs = parse_specs(row.get("product_specifications", ""))
                
                metadata: Dict[str, Any] = {
                    "source_dataset": "PromptCloudHQ_Flipkart_Products",
                    "source_product_id": uniq_id,
                    "brand": row.get("brand", "").strip(),
                    "product_rating": row.get("product_rating", "").strip(),
                    "overall_rating": row.get("overall_rating", "").strip(),
                    "image_urls": [],
                    "specifications": specs
                }
                
                if retail_price_str and retail_price_str.isdigit():
                    metadata["original_retail_price"] = int(retail_price_str) * 100
                    if price_val < int(retail_price_str):
                        metadata["discount_percent"] = round((1 - (price_val / int(retail_price_str))) * 100, 2)

                try:
                    img_list = ast.literal_eval(row.get("image", ""))
                    if isinstance(img_list, list):
                        metadata["image_urls"] = img_list
                except:
                    pass

                # Create Product
                new_product = Product(
                    merchant_id=merchant.id,
                    name=product_name,
                    description=row.get("description", "").strip(),
                    category=top_cat,
                    price=price_val * 100, # DB stores minor units
                    currency="INR",
                    is_active=True,
                    product_metadata=metadata
                )
                
                # Create Inventory
                qty = 0
                if args.inventory_mode == "demo":
                    # Deterministic pseudo-random quantity based on length of name or similar
                    qty = (len(product_name) * 7) % 150 + 10
                
                new_inventory = Inventory(
                    product=new_product,
                    available_quantity=qty,
                    reserved_quantity=0
                )
                
                db.add(new_product)
                db.add(new_inventory)
                stats["newly_inserted"] += 1

                if stats["newly_inserted"] % 500 == 0:
                    db.commit()
                    logging.info(f"Inserted {stats['newly_inserted']} products...")

            db.commit()

        logging.info("==================================================")
        logging.info("IMPORT SUMMARY")
        logging.info("==================================================")
        logging.info(f"Source rows:               {stats['source_rows']}")
        logging.info(f"Skipped (Category):        {stats['skipped_category']}")
        logging.info(f"Skipped (Missing Price):   {stats['skipped_missing_price']}")
        logging.info(f"Skipped (Duplicates CSV):  {stats['skipped_duplicates_in_csv']}")
        logging.info(f"Valid rows for target:     {stats['valid_rows']}")
        logging.info(f"Already present in DB:     {stats['already_present']}")
        logging.info(f"Newly inserted:            {stats['newly_inserted']}")
        logging.info(f"Categories imported:       {', '.join(TARGET_CATEGORIES)}")
        logging.info("==================================================")

    except Exception as e:
        db.rollback()
        logging.error(f"Import failed: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    main()
