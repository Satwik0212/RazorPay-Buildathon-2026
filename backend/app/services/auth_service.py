import uuid
from typing import Tuple
from sqlalchemy.orm import Session
from app.models.merchant import User, Merchant
from app.models.customer import Customer
from app.models.policy import Policy
from app.repositories.merchant_repository import MerchantRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.policy_repository import PolicyRepository
from app.schemas.auth.requests import RegisterRequest, LoginRequest
from app.security.authentication import hash_password, verify_password, create_access_token
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.constants import UserRole, ActorType, AuditEventType
from app.services.audit_service import AuditService


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.merchant_repo = MerchantRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.policy_repo = PolicyRepository(db)
        self.audit_service = AuditService(db)

    def register(self, req: RegisterRequest) -> Tuple[User, str]:
        existing_user = self.merchant_repo.get_user_by_email(req.email)
        if existing_user:
            raise ConflictError(f"User with email '{req.email}' already exists.")

        user = User(
            email=req.email,
            password_hash=hash_password(req.password),
            role=req.role.value,
            is_active=True,
        )
        created_user = self.merchant_repo.create_user(user)

        # Initialize corresponding role profile
        if req.role == UserRole.MERCHANT:
            merchant = Merchant(
                user_id=created_user.id,
                name=req.email.split("@")[0].capitalize() + " Store",
                description="Merchant store",
                is_active=True,
            )
            created_merchant = self.merchant_repo.create_merchant(merchant)
            # Default merchant policy
            self.policy_repo.create_or_update(
                {
                    "max_autonomous_amount": 500000,
                    "daily_autonomous_limit": 5000000,
                    "require_approval_above": 500000,
                    "blocked_categories": [],
                    "is_ai_enabled": True,
                },
                merchant_id=created_merchant.id,
            )
        elif req.role == UserRole.CUSTOMER:
            customer = Customer(user_id=created_user.id)
            self.customer_repo.create(customer)

        token = create_access_token(user_id=created_user.id, role=created_user.role)

        self.audit_service.log_event(
            event_type=AuditEventType.USER_REGISTERED.value,
            actor_type=ActorType.SYSTEM.value,
            entity_type="user",
            entity_id=created_user.id,
            event_data={"email": created_user.email, "role": created_user.role},
        )

        return created_user, token

    def login(self, req: LoginRequest) -> Tuple[User, str]:
        user = self.merchant_repo.get_user_by_email(req.email)
        if not user or not verify_password(req.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password.")

        if not user.is_active:
            raise UnauthorizedError("User account is inactive.")

        token = create_access_token(user_id=user.id, role=user.role)

        self.audit_service.log_event(
            event_type=AuditEventType.USER_LOGGED_IN.value,
            actor_type=ActorType.USER.value if hasattr(ActorType, "USER") else user.role,
            entity_type="user",
            actor_id=user.id,
            entity_id=user.id,
            event_data={"email": user.email},
        )

        return user, token
