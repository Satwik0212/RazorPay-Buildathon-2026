import uuid
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from app.models.product import Product, Inventory
from app.models.merchant import Merchant
from app.repositories.product_repository import ProductRepository
from app.schemas.product.requests import ProductCreate, ProductUpdate, ProductBulkCreate
from app.schemas.product.responses import ProductBulkResponse, ProductResponse
from app.core.exceptions import NotFoundError, ForbiddenError
from app.core.constants import ActorType, AuditEventType
from app.services.audit_service import AuditService


class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProductRepository(db)
        self.audit_service = AuditService(db)

    def create_product(self, merchant_id: uuid.UUID, req: ProductCreate) -> Product:
        product = Product(
            merchant_id=merchant_id,
            name=req.name,
            description=req.description,
            category=req.category,
            price=req.price,
            currency=req.currency,
            is_active=True,
            product_metadata=req.metadata,
        )
        created = self.repo.create_product(product, initial_quantity=req.initial_quantity)

        self.audit_service.log_event(
            event_type=AuditEventType.PRODUCT_CREATED.value,
            actor_type=ActorType.MERCHANT.value,
            entity_type="product",
            merchant_id=merchant_id,
            entity_id=created.id,
            event_data={"name": created.name, "price": created.price, "category": created.category},
        )
        return created

    def bulk_create_products(self, merchant_id: uuid.UUID, req: ProductBulkCreate) -> ProductBulkResponse:
        created_items = []
        errors = []
        for index, item_req in enumerate(req.products):
            try:
                prod = self.create_product(merchant_id, item_req)
                created_items.append(prod)
            except Exception as exc:
                errors.append({"index": index, "product_name": item_req.name, "error": str(exc)})

        return ProductBulkResponse(
            created=len(created_items),
            failed=len(errors),
            errors=errors,
            items=[ProductResponse.model_validate(p) for p in created_items],
        )

    def get_product_by_id(self, product_id: uuid.UUID) -> Product:
        product = self.repo.get_by_id(product_id)
        if not product:
            raise NotFoundError("Product", product_id)
        return product

    def update_product(self, product_id: uuid.UUID, merchant_id: uuid.UUID, req: ProductUpdate) -> Product:
        product = self.get_product_by_id(product_id)
        if product.merchant_id != merchant_id:
            raise ForbiddenError("You cannot modify products of another merchant.")

        if req.name is not None:
            product.name = req.name
        if req.description is not None:
            product.description = req.description
        if req.category is not None:
            product.category = req.category
        if req.price is not None:
            product.price = req.price
        if req.currency is not None:
            product.currency = req.currency
        if req.metadata is not None:
            product.product_metadata = req.metadata
        if req.is_active is not None:
            product.is_active = req.is_active

        updated = self.repo.update_product(product)

        self.audit_service.log_event(
            event_type=AuditEventType.PRODUCT_UPDATED.value,
            actor_type=ActorType.MERCHANT.value,
            entity_type="product",
            merchant_id=merchant_id,
            entity_id=updated.id,
            event_data={"name": updated.name, "price": updated.price, "is_active": updated.is_active},
        )
        return updated

    def delete_product(self, product_id: uuid.UUID, merchant_id: uuid.UUID) -> Product:
        """
        Soft delete: deactivates product to preserve order and quote references.
        """
        product = self.get_product_by_id(product_id)
        if product.merchant_id != merchant_id:
            raise ForbiddenError("You cannot delete products of another merchant.")
        
        product.is_active = False
        updated = self.repo.update_product(product)

        self.audit_service.log_event(
            event_type=AuditEventType.PRODUCT_DELETED.value,
            actor_type=ActorType.MERCHANT.value,
            entity_type="product",
            merchant_id=merchant_id,
            entity_id=updated.id,
        )
        return updated

    def reactivate_product(self, product_id: uuid.UUID, merchant_id: uuid.UUID) -> Product:
        """
        Reactivates a previously soft-deleted product.
        """
        product = self.get_product_by_id(product_id)
        if product.merchant_id != merchant_id:
            raise ForbiddenError("You cannot reactivate products of another merchant.")
        
        product.is_active = True
        updated = self.repo.update_product(product)

        # Audit event doesn't have an exact enum for REACTIVATED yet, let's use UPDATED with explicit data
        self.audit_service.log_event(
            event_type=AuditEventType.PRODUCT_UPDATED.value,
            actor_type=ActorType.MERCHANT.value,
            entity_type="product",
            merchant_id=merchant_id,
            entity_id=updated.id,
            event_data={"is_active": updated.is_active, "action": "reactivated"},
        )
        return updated

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
        return self.repo.list_products(
            merchant_id=merchant_id,
            category=category,
            min_price=min_price,
            max_price=max_price,
            is_active=is_active,
            search=search,
            limit=limit,
            offset=offset,
        )

    def list_categories(self, merchant_id: uuid.UUID) -> List[str]:
        return self.repo.list_categories(merchant_id)

    def update_inventory(self, product_id: uuid.UUID, merchant_id: uuid.UUID, quantity: int) -> Inventory:
        product = self.get_product_by_id(product_id)
        if product.merchant_id != merchant_id:
            raise ForbiddenError("You cannot modify inventory of another merchant.")
        
        inv = self.repo.update_inventory(product_id, quantity)
        if not inv:
            raise NotFoundError("Inventory for product", product_id)

        self.audit_service.log_event(
            event_type=AuditEventType.INVENTORY_UPDATED.value,
            actor_type=ActorType.MERCHANT.value,
            entity_type="inventory",
            merchant_id=merchant_id,
            entity_id=product_id,
            event_data={"available_quantity": inv.available_quantity},
        )
        return inv
