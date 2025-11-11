"""API key management routes."""
import secrets
import string
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db, User, APIKey
from models import APIKeyCreate, APIKeyResponse, APIKeyInfo
from auth import get_current_user
from user_levels import get_user_level_config

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


def generate_api_key():
    """Generate a secure API key"""
    prefix = "sk-"
    random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    return prefix + random_part


@router.post("/", response_model=APIKeyResponse)
def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API key for the user"""

    # Check if user has reached their API key limit (based on user level)
    level_config = get_user_level_config(current_user.user_level)
    max_keys = level_config.get("max_api_keys", 5)  # Default limit if not specified

    current_count = db.query(APIKey).filter(APIKey.user_id == current_user.id).count()
    if max_keys > 0 and current_count >= max_keys:  # Only check limit if max_keys > 0 (not unlimited)
        raise HTTPException(
            status_code=429,
            detail=f"API密钥数量已达上限 ({max_keys} 个密钥限制)"
        )

    # Generate a unique API key
    api_key_value = generate_api_key()

    # Ensure the key is unique
    while db.query(APIKey).filter(APIKey.key_value == api_key_value).first():
        api_key_value = generate_api_key()

    # Create new API key
    new_api_key = APIKey(
        user_id=current_user.id,
        key_name=api_key_data.key_name,
        key_value=api_key_value,
        expires_at=api_key_data.expires_at
    )

    db.add(new_api_key)
    db.commit()
    db.refresh(new_api_key)

    return new_api_key


@router.get("/", response_model=list[APIKeyInfo])
def get_user_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all API keys for the current user (without the actual key values)"""
    return db.query(APIKey).filter(APIKey.user_id == current_user.id).all()


@router.put("/{key_id}/toggle")
def toggle_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle the active status of an API key"""
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()

    if not api_key:
        raise HTTPException(status_code=404, detail="API密钥未找到")

    api_key.is_active = not api_key.is_active
    db.commit()

    return {"message": f"API密钥已{'启用' if api_key.is_active else '禁用'}"}


@router.delete("/{key_id}")
def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()

    if not api_key:
        raise HTTPException(status_code=404, detail="API密钥未找到")

    db.delete(api_key)
    db.commit()

    return {"message": "API密钥已删除"}
