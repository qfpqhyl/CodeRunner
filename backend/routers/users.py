"""User management routes (admin only)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db, User
from models import UserCreate, UserResponse, PasswordChangeByAdmin
from auth import get_password_hash, get_current_admin_user

router = APIRouter(prefix="/admin/users", tags=["users"])


@router.post("/{user_id}/change-password")
def change_user_password_by_admin(
    user_id: int,
    password_data: PasswordChangeByAdmin,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin can change any user's password"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户未找到")

    # Check new password length
    if len(password_data.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少需要6个字符")

    # Update password
    db_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "用户密码修改成功"}


@router.get("/", response_model=list[UserResponse])
def list_users(current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    return db.query(User).all()


@router.post("/", response_model=UserResponse)
def create_user_by_admin(
    user: UserCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_admin=user.is_admin,
        user_level=user.user_level
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.put("/{user_id}", response_model=UserResponse)
def update_user_by_admin(
    user_id: int,
    user_update: dict,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from deactivating themselves
    if db_user.id == current_user.id and "is_active" in user_update and not user_update["is_active"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    # Prevent admin from removing their own admin status
    if db_user.id == current_user.id and "is_admin" in user_update and not user_update["is_admin"]:
        raise HTTPException(status_code=400, detail="Cannot remove your own admin status")

    for field, value in user_update.items():
        if hasattr(db_user, field) and field not in ["id", "hashed_password", "created_at"]:
            setattr(db_user, field, value)

    # Handle password update separately
    if "password" in user_update and user_update["password"]:
        db_user.hashed_password = get_password_hash(user_update["password"])

    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}")
def delete_user_by_admin(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from deleting themselves
    if db_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}
