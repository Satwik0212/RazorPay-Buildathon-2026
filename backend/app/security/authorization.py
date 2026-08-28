from fastapi import Depends, HTTPException, status
from app.security.authentication import get_current_user

def require_role(required_role: str):
    def role_checker(user: dict = Depends(get_current_user)):
        if user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Insufficient permissions"
            )
        return user
    return role_checker

def verify_ownership(resource_owner_id: str, current_user_id: str):
    if resource_owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to resource"
        )
