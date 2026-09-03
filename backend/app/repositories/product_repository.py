import uuid
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
from app.models.product import Product, Inventory


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, product_id: uuid.UUID) -> Optional[Product]:
        stmt = (
            select(Product)
            .options(joinedload(Product.inventory))
            .where(Product.id == product_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def list_products(
        self,
        merchant_id: Optional[uuid.UUID] = None,
        category: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        is_active: Optional[bool] = True,
        search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Product], int]:
        stmt = select(Product).options(joinedload(Product.inventory))
        count_stmt = select(func.count(Product.id))

        filters = []
        if merchant_id:
            filters.append(Product.merchant_id == merchant_id)
        if category:
            filters.append(Product.category == category)
        if min_price is not None:
            filters.append(Product.price >= min_price)
        if max_price is not None:
            filters.append(Product.price <= max_price)
        if is_active is not None:
            filters.append(Product.is_active == is_active)
        if search:
            filters.append(Product.name.ilike(f"%{search}%"))

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total = self.db.execute(count_stmt).scalar() or 0
        products = list(
            self.db.execute(stmt.order_by(Product.id).limit(limit).offset(offset)).unique().scalars().all()
        )
        return products, total

    def get_active_catalogue_for_merchant(self, merchant_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Retrieves the complete active catalogue for the authenticated merchant in a single query.
        Utilizes a Core column-level query outer-joining Inventory to avoid ORM hydration overhead
        while preserving deterministic Product.id ordering and truthful inventory semantics.
        """
        stmt = (
            select(
                Product.id,
                Product.name,
                Product.description,
                Product.category,
                Product.price,
                Product.currency,
                Product.is_active,
                Product.product_metadata,
                Inventory.available_quantity,
            )
            .outerjoin(Inventory, Product.id == Inventory.product_id)
            .where(
                Product.merchant_id == merchant_id,
                Product.is_active == True,
            )
            .order_by(Product.id)
        )
        rows = self.db.execute(stmt).all()
        return [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description or "",
                "category": r.category,
                "price": r.price,
                "currency": r.currency,
                "is_active": r.is_active,
                "product_metadata": r.product_metadata or {},
                "available_quantity": r.available_quantity,
            }
            for r in rows
        ]


    def list_categories(self, merchant_id: uuid.UUID) -> List[str]:
        stmt = select(Product.category).where(Product.merchant_id == merchant_id).where(Product.category != None).distinct()
        categories = self.db.execute(stmt).scalars().all()
        return [c for c in categories if c]

    def create_product(self, product: Product, initial_quantity: int = 10) -> Product:
        self.db.add(product)
        self.db.flush()
        inventory = Inventory(
            product_id=product.id,
            available_quantity=initial_quantity,
            reserved_quantity=0,
        )
        self.db.add(inventory)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update_product(self, product: Product) -> Product:
        self.db.commit()
        self.db.refresh(product)
        return product

    def update_inventory(self, product_id: uuid.UUID, available_quantity: int) -> Optional[Inventory]:
        stmt = select(Inventory).where(Inventory.product_id == product_id)
        inv = self.db.execute(stmt).scalar_one_or_none()
        if inv:
            inv.available_quantity = available_quantity
            self.db.commit()
            self.db.refresh(inv)
        return inv

    def decrement_inventory(self, product_id: uuid.UUID, quantity: int) -> bool:
        from sqlalchemy import update
        stmt = (
            update(Inventory)
            .where(Inventory.product_id == product_id)
            .where(Inventory.available_quantity >= quantity)
            .values(available_quantity=Inventory.available_quantity - quantity)
        )
        result = self.db.execute(stmt)
        return result.rowcount > 0
