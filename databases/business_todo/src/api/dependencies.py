from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from databases.business_todo.src.core.security import decode_token
from databases.business_todo.src.repositories.user_repo import UserRepository

security = HTTPBearer()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    token = credentials.credentials

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = UserRepository.get_by_id(int(user_id))
    if not user or user["status"] != "active":
        raise HTTPException(status_code=401, detail="User not found or blocked")
    return user


async def get_current_admin_user(
        current_user: dict = Depends(get_current_user)
) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
