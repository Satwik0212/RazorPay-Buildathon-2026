import uuid
from typing import Optional
from app.models.merchant import User, Merchant
from app.models.customer import Customer
from app.core.exceptions import ForbiddenError
from app.core.constants import UserRole


def verify_merchant_ownership(merchant: Merchant, requested_merchant_id: uuid.UUID) -> None:
    if merchant.id != requested_merchant_id:
        raise ForbiddenError("You cannot access or modify resources belonging to another merchant.")


def verify_customer_ownership(customer: Customer, requested_customer_id: uuid.UUID) -> None:
    if customer.id != requested_customer_id:
        raise ForbiddenError("You cannot access or modify resources belonging to another customer.")
