import os
import sys
from collections import Counter
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.product import Product, Inventory

def validate():
    db = SessionLocal()
    
    # 1. Total imported products
    products = db.execute(select(Product)).scalars().all()
    print(f"Total Products in DB: {len(products)}")
    
    cat_counts = Counter()
    has_desc = 0
    has_specs = 0
    has_rating = 0
    inv_gt_0 = 0
    inv_eq_0 = 0
    uniq_ids = []
    names = []
    active = 0
    
    for p in products:
        cat_counts[p.category] += 1
        if p.description: has_desc += 1
        
        meta = p.product_metadata or {}
        if meta.get("specifications"): has_specs += 1
        if meta.get("product_rating") and meta.get("product_rating") != "No rating available":
            has_rating += 1
        if meta.get("source_product_id"):
            uniq_ids.append(meta.get("source_product_id"))
        
        names.append(p.name)
        
        if p.is_active: active += 1
        
        if p.inventory and p.inventory.available_quantity > 0:
            inv_gt_0 += 1
        else:
            inv_eq_0 += 1

    print("Products per category:")
    for k, v in cat_counts.most_common():
        print(f"  {k}: {v}")
    
    print(f"Products with descriptions: {has_desc}")
    print(f"Products with specifications: {has_specs}")
    print(f"Products with ratings: {has_rating}")
    print(f"Products with inventory > 0: {inv_gt_0}")
    print(f"Products with inventory = 0: {inv_eq_0}")
    
    print(f"Duplicate source IDs: {len(uniq_ids) - len(set(uniq_ids))}")
    print(f"Duplicate product names: {len(names) - len(set(names))}")
    print(f"Active products: {active}")
    print(f"Number of categories: {len(cat_counts)}")
    
validate()
