from app.models.merchant import User, Merchant
from app.models.policy import Policy
from app.security.authentication import hash_password, create_access_token
from app.core.constants import UserRole

class DummyResponse:
    def __init__(self, token, user, merchant):
        self.status_code = 201
        self._json = {
            "access_token": token,
            "user": {
                "id": str(user.id),
                "merchant_id": str(merchant.id),
                "email": user.email,
                "role": user.role
            }
        }
    def json(self):
        return self._json

def create_test_merchant(db_session, email, password="password12345"):
    user = User(
        email=email,
        password_hash=hash_password(password),
        role=UserRole.MERCHANT.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    merchant = Merchant(
        user_id=user.id,
        name=email.split("@")[0].capitalize() + " Store",
        description="Merchant store",
        is_active=True,
    )
    db_session.add(merchant)
    db_session.commit()
    db_session.refresh(merchant)

    policy = Policy(
        merchant_id=merchant.id,
        max_autonomous_amount=500000,
        daily_autonomous_limit=5000000,
        require_approval_above=500000,
        blocked_categories=[],
        is_ai_enabled=True,
    )
    db_session.add(policy)
    db_session.commit()

    token = create_access_token(user_id=user.id, role=user.role)
    return DummyResponse(token, user, merchant)
