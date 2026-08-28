import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.customer import Customer


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, customer_id: uuid.UUID) -> Optional[Customer]:
        return self.db.get(Customer, customer_id)

    def get_by_user_id(self, user_id: uuid.UUID) -> Optional[Customer]:
        stmt = select(Customer).where(Customer.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer
