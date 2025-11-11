"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from database import get_db, User
from models import UserCreate, UserResponse, UserLogin, Token, PasswordChange
from auth import authenticate_user, create_access_token, get_password_hash, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from utils import log_system_event, get_client_info

router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db), client_info: dict = Depends(get_client_info)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Only admin can create admin users
    if user.is_admin:
        # Check if any admin exists
        existing_admin = db.query(User).filter(User.is_admin == True).first()
        if not existing_admin:
            # This is the first admin creation, allow it
            pass
        else:
            # There's already an admin, only admin can create new admin
            raise HTTPException(status_code=403, detail="Only admin users can create admin accounts")

    try:
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

        # Log user registration
        log_system_event(
            db=db,
            user_id=db_user.id,
            action="user_register",
            resource_type="user",
            resource_id=db_user.id,
            details={
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin,
                "user_level": user.user_level
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        return db_user

    except Exception as e:
        # Log failed registration attempt
        log_system_event(
            db=db,
            action="user_register",
            resource_type="user",
            details={
                "username": user.username,
                "email": user.email,
                "error": str(e)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise


@router.post("/login", response_model=Token)
def login_user(user_credentials: UserLogin, db: Session = Depends(get_db), client_info: dict = Depends(get_client_info)):
    user = authenticate_user(db, user_credentials.username, user_credentials.password)

    if not user:
        # Log failed login attempt
        log_system_event(
            db=db,
            action="user_login",
            resource_type="user",
            details={
                "username": user_credentials.username,
                "reason": "invalid_credentials"
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Log successful login
    log_system_event(
        db=db,
        user_id=user.id,
        action="user_login",
        resource_type="user",
        resource_id=user.id,
        details={
            "username": user.username,
            "token_expires_minutes": ACCESS_TOKEN_EXPIRE_MINUTES
        },
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        status="success"
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user's password"""
    # Verify current password
    if not authenticate_user(db, current_user.username, password_data.current_password):
        raise HTTPException(status_code=400, detail="当前密码不正确")

    # Check new password length
    if len(password_data.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少需要6个字符")

    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "密码修改成功"}
