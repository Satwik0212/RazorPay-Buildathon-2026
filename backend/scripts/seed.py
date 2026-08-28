import uuid
import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, Base, engine
from app.models.merchant import User, Merchant
from app.models.customer import Customer
from app.models.product import Product, Inventory
from app.models.policy import Policy
from app.security.authentication import hash_password
from app.core.constants import UserRole


def seed_demo_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("[+] Seeding P0 Demo Data...")

        # 1. Demo Merchant User
        merchant_email = "merchant@demo.com"
        merchant_user = db.query(User).filter(User.email == merchant_email).first()
        if not merchant_user:
            merchant_user = User(
                email=merchant_email,
                password_hash=hash_password("password123"),
                role=UserRole.MERCHANT.value,
                is_active=True,
            )
            db.add(merchant_user)
            db.flush()

            merchant = Merchant(
                user_id=merchant_user.id,
                name="Apex Audio & Tech",
                description="Premium audiophile electronics and smart gadgets with high agent-readiness.",
            )
            db.add(merchant)
            db.flush()

            # Default Merchant Policy
            policy = Policy(
                merchant_id=merchant.id,
                max_autonomous_amount=1000000,  # 10,000 max autonomous spend (paise)
                daily_autonomous_limit=10000000, # 100,000 daily spend
                require_approval_above=500000,  # Requires human check above 5,000
                blocked_categories=["gambling", "weapons", "restricted"],
                is_ai_enabled=True,
            )
            db.add(policy)
            db.flush()
            print(f"  [+] Created Merchant: {merchant.name} ({merchant_email})")
        else:
            merchant = db.query(Merchant).filter(Merchant.user_id == merchant_user.id).first()

        # 2. Demo Customer User
        customer_email = "buyer@demo.com"
        customer_user = db.query(User).filter(User.email == customer_email).first()
        if not customer_user:
            customer_user = User(
                email=customer_email,
                password_hash=hash_password("password123"),
                role=UserRole.CUSTOMER.value,
                is_active=True,
            )
            db.add(customer_user)
            db.flush()

            customer = Customer(
                user_id=customer_user.id,
            )
            db.add(customer)
            db.flush()
            print(f"  [+] Created Customer: {customer_email}")
        else:
            customer = db.query(Customer).filter(Customer.user_id == customer_user.id).first()

        # 3. Seed Catalogue Products (with authoritative minor unit prices)
        demo_products = [
            {
                "name": "Apex Sonic Pro Wireless ANC Headphones",
                "description": "Industry-leading active noise cancelling headphones with 40-hour battery life, multipoint Bluetooth 5.3, and ultra-low latency gaming mode.",
                "category": "headphones",
                "price": 499900,  # 4,999.00 in paise
                "currency": "INR",
                "is_active": True,
                "product_metadata": {
                    "anc": True,
                    "battery_hours": 40,
                    "bluetooth_version": "5.3",
                    "latency_ms": 35,
                    "weight_grams": 245,
                    "delivery_days": 2,
                    "returnable": True,
                },
                "quantity": 45,
            },
            {
                "name": "Apex BassFlow Sport Earbuds",
                "description": "IPX7 waterproof wireless sport earbuds with secure ear hooks, deep bass resonance, and 24-hour total playback with charging case.",
                "category": "earphones",
                "price": 199900,  # 1,999.00 in paise
                "currency": "INR",
                "is_active": True,
                "product_metadata": {
                    "waterproof_rating": "IPX7",
                    "battery_hours": 24,
                    "microphone": True,
                    "touch_controls": True,
                    "delivery_days": 3,
                    "returnable": True,
                },
                "quantity": 80,
            },
            {
                "name": "Apex Studio Monitor Wired Over-Ear Headphones",
                "description": "Professional studio reference monitoring headphones with 50mm neodymium drivers, detachable braided cable, and flat acoustic profile.",
                "category": "headphones",
                "price": 349900,  # 3,499.00 in paise
                "currency": "INR",
                "is_active": True,
                "product_metadata": {
                    "driver_size_mm": 50,
                    "connector": "3.5mm gold-plated + 6.35mm adapter",
                    "frequency_response": "15Hz - 28kHz",
                    "wired": True,
                    "delivery_days": 2,
                    "returnable": True,
                },
                "quantity": 30,
            },
            {
                "name": "Apex Braided 3.5mm Audio Cable (1.5m)",
                "description": "High-durability oxygen-free copper braided auxiliary audio cable with 24k gold-plated connectors.",
                "category": "accessories",
                "price": 34900,  # 349.00 in paise
                "currency": "INR",
                "is_active": True,
                "product_metadata": {
                    "length_meters": 1.5,
                    "material": "Braided nylon + OFC copper",
                    "delivery_days": 1,
                    "returnable": True,
                },
                "quantity": 150,
            },
        ]

        for p_data in demo_products:
            existing = db.query(Product).filter(
                Product.merchant_id == merchant.id,
                Product.name == p_data["name"]
            ).first()

            if not existing:
                qty = p_data.pop("quantity")
                product = Product(
                    merchant_id=merchant.id,
                    **p_data,
                )
                db.add(product)
                db.flush()

                inventory = Inventory(
                    product_id=product.id,
                    available_quantity=qty,
                    reserved_quantity=0,
                )
                db.add(inventory)
                print(f"  [+] Seeded Product: {product.name} (Price: {product.price} paise, Stock: {qty})")

        db.commit()
        print("[SUCCESS] Database seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
