"""Protected routes that require PropelAuth authentication."""
from fastapi import APIRouter, Depends, HTTPException, Request
from propelauth_fastapi import User
from loguru import logger
from .propel import auth
from typing import Dict, Any
from ..config.settings import get_settings

router = APIRouter()
settings = get_settings()

@router.get("/test-auth")
async def test_auth(current_user: User = Depends(auth.require_user)) -> Dict[str, Any]:
    """A simple endpoint to test if authentication is working."""
    logger.info(f"Test auth endpoint accessed by user: {current_user.user_id}")
    return {
        "status": "success",
        "message": "Authentication working!",
        "user_email": current_user.email,
        "development_mode": settings.development_mode
    }

@router.get("/me")
async def get_user_info(current_user: User = Depends(auth.require_user)) -> Dict[str, Any]:
    """Get information about the currently authenticated user."""
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "organizations": [
            {
                "org_id": org_id,
                "org_info": org_info.dict()
            }
            for org_id, org_info in (current_user.org_id_to_org_member_info or {}).items()
        ],
        "development_mode": settings.development_mode
    }

@router.get("/org/{org_id}/protected")
async def protected_org_route(org_id: str, current_user: User = Depends(auth.require_user)) -> Dict[str, str]:
    """A protected route that requires membership in a specific organization."""
    if not current_user.org_id_to_org_member_info or org_id not in current_user.org_id_to_org_member_info:
        raise HTTPException(
            status_code=403,
            detail=f"User is not a member of organization {org_id}"
        )
    return {
        "message": f"You have access to organization {org_id}",
        "user_id": current_user.user_id,
        "development_mode": settings.development_mode
    } 