from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import timedelta, datetime
import subprocess
import tempfile
import os
import time
import secrets
import string
import json
import uuid
from database import get_db, init_db, User, CodeExecution, CodeLibrary, APIKey, SystemLog, AIConfig
from models import UserCreate, UserResponse, UserLogin, Token, CodeExecutionRequest, CodeExecutionResponse, CodeLibraryCreate, CodeLibraryUpdate, CodeLibraryResponse, PasswordChange, PasswordChangeByAdmin, APIKeyCreate, APIKeyResponse, APIKeyInfo, CodeExecuteByAPIRequest, CodeExecuteByAPIResponse, AIConfigCreate, AIConfigUpdate, AIConfigResponse, AICodeGenerateRequest, AICodeGenerateResponse
from auth import authenticate_user, create_access_token, get_password_hash, get_current_user, get_current_admin_user, get_api_key_user, ACCESS_TOKEN_EXPIRE_MINUTES
from user_levels import get_user_level_config, can_user_execute, get_daily_execution_count, can_user_make_api_call, get_daily_api_call_count, USER_LEVELS

app = FastAPI(title="CodeRunner API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Utility function to log system events
def log_system_event(
    db: Session,
    user_id: int = None,
    action: str = "",
    resource_type: str = "",
    resource_id: int = None,
    details: dict = None,
    ip_address: str = None,
    user_agent: str = None,
    status: str = "success"
):
    """Log a system event"""
    try:
        log_entry = SystemLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details) if details else None,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        # Don't fail the main operation if logging fails
        print(f"Failed to log system event: {e}")
        db.rollback()

# Dependency to get client information
async def get_client_info(request: Request):
    """Get client IP and User-Agent from request"""
    # Get real client IP (considering reverse proxies)
    client_ip = request.client.host
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        client_ip = real_ip.strip()

    user_agent = request.headers.get("User-Agent", "")

    return {
        "ip_address": client_ip,
        "user_agent": user_agent
    }

@app.post("/register", response_model=UserResponse)
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

@app.post("/login", response_model=Token)
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

@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/change-password")
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

@app.post("/admin/users/{user_id}/change-password")
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

@app.get("/users", response_model=list[UserResponse])
def list_users(current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    return db.query(User).all()

@app.post("/execute", response_model=CodeExecutionResponse)
def execute_code(
    code_request: CodeExecutionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    # Check if user can execute code based on their level
    can_execute, message = can_user_execute(current_user, db)
    if not can_execute:
        raise HTTPException(status_code=429, detail=message)

    # Get user level configuration
    level_config = get_user_level_config(current_user.user_level)

    # Check daily execution count
    if level_config["daily_executions"] > 0:
        today_count = get_daily_execution_count(current_user.id, db)
        remaining = level_config["daily_executions"] - today_count
        if remaining <= 0:
            raise HTTPException(
                status_code=429,
                detail=f"今日执行次数已达上限 ({level_config['daily_executions']} 次)"
            )

    # Create a temporary file for the Python code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code_request.code)
        temp_file = f.name

    try:
        start_time = time.time()

        # Execute the Python code with user level limits
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=level_config["max_execution_time"]
        )

        execution_time = int((time.time() - start_time) * 1000)  # in milliseconds

        if result.returncode == 0:
            output = result.stdout
            status = "success"
        else:
            output = result.stderr
            status = "error"

        # Save execution record with memory usage (placeholder for now)
        execution = CodeExecution(
            user_id=current_user.id,
            code=code_request.code,
            result=output,
            status=status,
            execution_time=execution_time,
            memory_usage=None  # Could be implemented with psutil in the future
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        # Log code execution
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="code_execute",
            resource_type="code_execution",
            resource_id=execution.id,
            details={
                "status": status,
                "execution_time": execution_time,
                "code_length": len(code_request.code),
                "user_level": current_user.user_level
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success" if status == "success" else "error"
        )

        return execution

    except subprocess.TimeoutExpired:
        output = f"执行超时 ({level_config['max_execution_time']} 秒限制)"
        status = "timeout"
        execution = CodeExecution(
            user_id=current_user.id,
            code=code_request.code,
            result=output,
            status=status,
            execution_time=level_config["max_execution_time"] * 1000
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution

    except Exception as e:
        output = f"执行错误: {str(e)}"
        status = "error"
        execution = CodeExecution(
            user_id=current_user.id,
            code=code_request.code,
            result=output,
            status=status,
            execution_time=0
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution

    finally:
        # Clean up the temporary file
        os.unlink(temp_file)

@app.get("/executions", response_model=list[CodeExecutionResponse])
def get_executions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    return db.query(CodeExecution).filter(CodeExecution.user_id == current_user.id).order_by(CodeExecution.created_at.desc()).limit(limit).all()

# Admin-only endpoints
@app.post("/admin/users", response_model=UserResponse)
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

@app.put("/admin/users/{user_id}", response_model=UserResponse)
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

@app.delete("/admin/users/{user_id}")
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

@app.get("/admin/executions", response_model=list[CodeExecutionResponse])
def get_all_executions(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    limit: int = 100
):
    return db.query(CodeExecution).order_by(CodeExecution.created_at.desc()).limit(limit).all()

@app.get("/user-levels", response_model=dict)
def get_user_levels():
    """Get all user level configurations"""
    return USER_LEVELS

@app.get("/user-stats")
def get_user_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user's statistics and limits"""
    level_config = get_user_level_config(current_user.user_level)
    today_count = get_daily_execution_count(current_user.id, db)
    today_api_calls = get_daily_api_call_count(current_user.id, db)

    remaining_executions = None
    if level_config["daily_executions"] > 0:
        remaining_executions = max(0, level_config["daily_executions"] - today_count)

    remaining_api_calls = None
    if level_config["daily_api_calls"] > 0:
        remaining_api_calls = max(0, level_config["daily_api_calls"] - today_api_calls)

    return {
        "user_level": current_user.user_level,
        "level_config": level_config,
        "today_executions": today_count,
        "remaining_executions": remaining_executions,
        "today_api_calls": today_api_calls,
        "remaining_api_calls": remaining_api_calls,
        "is_unlimited_executions": level_config["daily_executions"] == -1,
        "is_unlimited_api_calls": level_config["daily_api_calls"] == -1
    }

# Code Library endpoints
@app.post("/code-library", response_model=CodeLibraryResponse)
def save_code_to_library(
    code_data: CodeLibraryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save code to user's code library"""
    # Check if user has reached their code library limit (based on user level)
    level_config = get_user_level_config(current_user.user_level)
    max_codes = level_config.get("max_saved_codes", 20)  # Default limit if not specified

    current_count = db.query(CodeLibrary).filter(CodeLibrary.user_id == current_user.id).count()
    if max_codes > 0 and current_count >= max_codes:  # Only check limit if max_codes > 0 (not unlimited)
        raise HTTPException(
            status_code=429,
            detail=f"代码库已满 ({max_codes} 个代码片段限制)"
        )

    # Create new code library entry
    library_entry = CodeLibrary(
        user_id=current_user.id,
        title=code_data.title,
        description=code_data.description,
        code=code_data.code,
        language=code_data.language,
        is_public=code_data.is_public,
        tags=code_data.tags
    )

    db.add(library_entry)
    db.commit()
    db.refresh(library_entry)

    return library_entry

@app.get("/code-library", response_model=list[CodeLibraryResponse])
def get_user_code_library(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0
):
    """Get user's code library"""
    return db.query(CodeLibrary).filter(CodeLibrary.user_id == current_user.id).order_by(CodeLibrary.updated_at.desc()).offset(offset).limit(limit).all()

@app.get("/code-library/{code_id}", response_model=CodeLibraryResponse)
def get_code_from_library(
    code_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific code from library"""
    code_entry = db.query(CodeLibrary).filter(
        CodeLibrary.id == code_id,
        CodeLibrary.user_id == current_user.id
    ).first()

    if not code_entry:
        raise HTTPException(status_code=404, detail="代码片段未找到")

    return code_entry

@app.put("/code-library/{code_id}", response_model=CodeLibraryResponse)
def update_code_in_library(
    code_id: int,
    code_update: CodeLibraryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update code in library"""
    code_entry = db.query(CodeLibrary).filter(
        CodeLibrary.id == code_id,
        CodeLibrary.user_id == current_user.id
    ).first()

    if not code_entry:
        raise HTTPException(status_code=404, detail="代码片段未找到")

    # Update fields
    update_data = code_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(code_entry, field, value)

    code_entry.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(code_entry)

    return code_entry

@app.delete("/code-library/{code_id}")
def delete_code_from_library(
    code_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete code from library"""
    code_entry = db.query(CodeLibrary).filter(
        CodeLibrary.id == code_id,
        CodeLibrary.user_id == current_user.id
    ).first()

    if not code_entry:
        raise HTTPException(status_code=404, detail="代码片段未找到")

    db.delete(code_entry)
    db.commit()

    return {"message": "代码片段已删除"}

# Utility function to generate API keys
def generate_api_key():
    """Generate a secure API key"""
    prefix = "sk-"
    random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    return prefix + random_part

# API Key Management endpoints
@app.post("/api-keys", response_model=APIKeyResponse)
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

@app.get("/api-keys", response_model=list[APIKeyInfo])
def get_user_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all API keys for the current user (without the actual key values)"""
    return db.query(APIKey).filter(APIKey.user_id == current_user.id).all()

@app.put("/api-keys/{key_id}/toggle")
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

@app.delete("/api-keys/{key_id}")
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

# External API endpoints for code execution
@app.post("/api/v1/execute", response_model=CodeExecuteByAPIResponse)
def execute_code_by_api(
    request: CodeExecuteByAPIRequest,
    api_key: str = None,
    db: Session = Depends(get_db)
):
    """Execute code from library using API key"""

    # Validate API key and get user
    try:
        user, api_key_obj = get_api_key_user(api_key, db)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    # Check if user can make API calls
    can_call, message = can_user_make_api_call(user, db)
    if not can_call:
        raise HTTPException(status_code=429, detail=message)

    # Get the code from library
    code_entry = db.query(CodeLibrary).filter(
        CodeLibrary.id == request.code_id,
        CodeLibrary.user_id == user.id
    ).first()

    if not code_entry:
        raise HTTPException(status_code=404, detail="代码片段未找到或无权访问")

    # Get user level configuration
    level_config = get_user_level_config(user.user_level)

    # Create a temporary file for the Python code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        # If parameters are provided, we could modify the code here
        # For now, just use the code as-is
        f.write(code_entry.code)
        temp_file = f.name

    try:
        start_time = time.time()

        # Execute the Python code with user level limits
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=level_config["max_execution_time"]
        )

        execution_time = int((time.time() - start_time) * 1000)  # in milliseconds

        if result.returncode == 0:
            output = result.stdout
            status = "success"
        else:
            output = result.stderr
            status = "error"

        # Save execution record with API call tracking
        execution = CodeExecution(
            user_id=user.id,
            code=code_entry.code,
            result=output,
            status=status,
            execution_time=execution_time,
            memory_usage=None,  # Could be implemented with psutil in the future
            is_api_call=True,
            code_library_id=code_entry.id
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        # Create response with code title
        response = CodeExecuteByAPIResponse(
            id=execution.id,
            result=execution.result,
            status=execution.status,
            execution_time=execution.execution_time,
            memory_usage=execution.memory_usage,
            created_at=execution.created_at,
            code_title=code_entry.title
        )

        return response

    except subprocess.TimeoutExpired:
        output = f"执行超时 ({level_config['max_execution_time']} 秒限制)"
        status = "timeout"
        execution = CodeExecution(
            user_id=user.id,
            code=code_entry.code,
            result=output,
            status=status,
            execution_time=level_config["max_execution_time"] * 1000,
            is_api_call=True,
            code_library_id=code_entry.id
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        response = CodeExecuteByAPIResponse(
            id=execution.id,
            result=execution.result,
            status=execution.status,
            execution_time=execution.execution_time,
            memory_usage=execution.memory_usage,
            created_at=execution.created_at,
            code_title=code_entry.title
        )

        return response

    except Exception as e:
        output = f"执行错误: {str(e)}"
        status = "error"
        execution = CodeExecution(
            user_id=user.id,
            code=code_entry.code,
            result=output,
            status=status,
            execution_time=0,
            is_api_call=True,
            code_library_id=code_entry.id
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        response = CodeExecuteByAPIResponse(
            id=execution.id,
            result=execution.result,
            status=execution.status,
            execution_time=execution.execution_time,
            memory_usage=execution.memory_usage,
            created_at=execution.created_at,
            code_title=code_entry.title
        )

        return response

    finally:
        # Clean up the temporary file
        os.unlink(temp_file)

@app.get("/api/v1/codes", response_model=list[CodeLibraryResponse])
def get_user_codes_by_api(
    api_key: str = None,
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Get user's code library via API"""

    # Validate API key and get user
    try:
        user, api_key_obj = get_api_key_user(api_key, db)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    # Check if user can make API calls
    can_call, message = can_user_make_api_call(user, db)
    if not can_call:
        raise HTTPException(status_code=429, detail=message)

    # Get user's code library
    return db.query(CodeLibrary).filter(
        CodeLibrary.user_id == user.id
    ).order_by(CodeLibrary.updated_at.desc()).offset(offset).limit(limit).all()

@app.get("/api/v1/codes/{code_id}", response_model=CodeLibraryResponse)
def get_code_by_api(
    code_id: int,
    api_key: str = None,
    db: Session = Depends(get_db)
):
    """Get specific code from library via API"""

    # Validate API key and get user
    try:
        user, api_key_obj = get_api_key_user(api_key, db)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    # Check if user can make API calls
    can_call, message = can_user_make_api_call(user, db)
    if not can_call:
        raise HTTPException(status_code=429, detail=message)

    # Get specific code
    code_entry = db.query(CodeLibrary).filter(
        CodeLibrary.id == code_id,
        CodeLibrary.user_id == user.id
    ).first()

    if not code_entry:
        raise HTTPException(status_code=404, detail="代码片段未找到或无权访问")

    return code_entry

@app.get("/")
def read_root():
    return {"message": "Welcome to CodeRunner API"}

# System Logs endpoints (Admin only)
@app.get("/admin/logs")
def get_system_logs(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
    action: str = None,
    resource_type: str = None,
    status: str = None,
    user_id: int = None,
    start_date: str = None,
    end_date: str = None
):
    """Get system logs with filtering options"""
    query = db.query(SystemLog)

    # Apply filters
    if action:
        query = query.filter(SystemLog.action == action)
    if resource_type:
        query = query.filter(SystemLog.resource_type == resource_type)
    if status:
        query = query.filter(SystemLog.status == status)
    if user_id:
        query = query.filter(SystemLog.user_id == user_id)
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(SystemLog.created_at >= start_dt)
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(SystemLog.created_at <= end_dt)
        except ValueError:
            pass

    # Order by creation time (newest first) and apply pagination
    logs = query.order_by(SystemLog.created_at.desc()).offset(offset).limit(limit).all()

    # Convert to dict format with user info
    result = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": json.loads(log.details) if log.details else None,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "status": log.status,
            "created_at": log.created_at.isoformat(),
            "user": None
        }

        # Add user info if available
        if log.user_id:
            user = db.query(User).filter(User.id == log.user_id).first()
            if user:
                log_dict["user"] = {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name
                }

        result.append(log_dict)

    return result

@app.get("/admin/logs/stats")
def get_log_statistics(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    days: int = 7
):
    """Get log statistics for the past N days"""
    from datetime import timedelta

    start_date = datetime.utcnow() - timedelta(days=days)

    # Total logs in period
    total_logs = db.query(SystemLog).filter(SystemLog.created_at >= start_date).count()

    # Logs by status
    status_counts = {}
    for status in ["success", "error", "warning"]:
        count = db.query(SystemLog).filter(
            SystemLog.created_at >= start_date,
            SystemLog.status == status
        ).count()
        status_counts[status] = count

    # Logs by action (top 10)
    action_counts = db.query(
        SystemLog.action,
        func.count(SystemLog.id).label('count')
    ).filter(
        SystemLog.created_at >= start_date
    ).group_by(SystemLog.action).order_by(
        func.count(SystemLog.id).desc()
    ).limit(10).all()

    # Logs by resource_type
    resource_counts = db.query(
        SystemLog.resource_type,
        func.count(SystemLog.id).label('count')
    ).filter(
        SystemLog.created_at >= start_date
    ).group_by(SystemLog.resource_type).order_by(
        func.count(SystemLog.id).desc()
    ).limit(10).all()

    # Recent error logs (last 10)
    recent_errors = db.query(SystemLog).filter(
        SystemLog.status == "error",
        SystemLog.created_at >= start_date
    ).order_by(SystemLog.created_at.desc()).limit(10).all()

    return {
        "period_days": days,
        "total_logs": total_logs,
        "status_distribution": status_counts,
        "top_actions": [{"action": action, "count": count} for action, count in action_counts],
        "top_resources": [{"resource_type": resource, "count": count} for resource, count in resource_counts],
        "recent_errors": [
            {
                "id": log.id,
                "action": log.action,
                "details": json.loads(log.details) if log.details else None,
                "created_at": log.created_at.isoformat(),
                "user_id": log.user_id
            }
            for log in recent_errors
        ]
    }

@app.get("/admin/logs/actions")
def get_log_actions(current_user: User = Depends(get_current_admin_user)):
    """Get all available log actions for filtering"""
    db = next(get_db())
    try:
        actions = db.query(SystemLog.action).distinct().all()
        return [action[0] for action in actions if action[0]]
    finally:
        db.close()

@app.get("/admin/logs/resource-types")
def get_log_resource_types(current_user: User = Depends(get_current_admin_user)):
    """Get all available resource types for filtering"""
    db = next(get_db())
    try:
        resource_types = db.query(SystemLog.resource_type).distinct().all()
        return [rt[0] for rt in resource_types if rt[0]]
    finally:
        db.close()

# AI Configuration endpoints
@app.post("/ai-configs", response_model=AIConfigResponse)
def create_ai_config(
    ai_config: AIConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new AI configuration"""
    # Check if user has reached their AI config limit
    current_count = db.query(AIConfig).filter(AIConfig.user_id == current_user.id).count()
    if current_count >= 5:  # Limit to 5 AI configs per user
        raise HTTPException(
            status_code=429,
            detail="AI配置数量已达上限 (5个配置限制)"
        )

    # Check if config name already exists for this user
    existing_config = db.query(AIConfig).filter(
        AIConfig.user_id == current_user.id,
        AIConfig.config_name == ai_config.config_name
    ).first()
    if existing_config:
        raise HTTPException(status_code=400, detail="配置名称已存在")

    # Deactivate other configs if this one is set as active
    if ai_config.is_active:
        db.query(AIConfig).filter(AIConfig.user_id == current_user.id).update({"is_active": False})

    # Create new AI config
    new_config = AIConfig(
        user_id=current_user.id,
        config_name=ai_config.config_name,
        provider=ai_config.provider,
        model_name=ai_config.model_name,
        api_key=ai_config.api_key,
        base_url=ai_config.base_url,
        is_active=ai_config.is_active if ai_config.is_active is not None else True
    )

    db.add(new_config)
    db.commit()
    db.refresh(new_config)

    return new_config

@app.get("/ai-configs", response_model=list[AIConfigResponse])
def get_ai_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all AI configurations for the current user"""
    return db.query(AIConfig).filter(AIConfig.user_id == current_user.id).all()

@app.put("/ai-configs/{config_id}", response_model=AIConfigResponse)
def update_ai_config(
    config_id: int,
    config_update: AIConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an AI configuration"""
    ai_config = db.query(AIConfig).filter(
        AIConfig.id == config_id,
        AIConfig.user_id == current_user.id
    ).first()

    if not ai_config:
        raise HTTPException(status_code=404, detail="AI配置未找到")

    # Update fields
    update_data = config_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ai_config, field, value)

    # Deactivate other configs if this one is set as active
    if config_update.is_active:
        db.query(AIConfig).filter(
            AIConfig.user_id == current_user.id,
            AIConfig.id != config_id
        ).update({"is_active": False})

    ai_config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ai_config)

    return ai_config

@app.delete("/ai-configs/{config_id}")
def delete_ai_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an AI configuration"""
    ai_config = db.query(AIConfig).filter(
        AIConfig.id == config_id,
        AIConfig.user_id == current_user.id
    ).first()

    if not ai_config:
        raise HTTPException(status_code=404, detail="AI配置未找到")

    db.delete(ai_config)
    db.commit()

    return {"message": "AI配置已删除"}

@app.post("/ai/generate-code", response_model=AICodeGenerateResponse)
def generate_code_by_ai(
    request: AICodeGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Generate code using AI"""
    # Get AI configuration
    ai_config = None
    if request.config_id:
        ai_config = db.query(AIConfig).filter(
            AIConfig.id == request.config_id,
            AIConfig.user_id == current_user.id,
            AIConfig.is_active == True
        ).first()
    else:
        # Get active config
        ai_config = db.query(AIConfig).filter(
            AIConfig.user_id == current_user.id,
            AIConfig.is_active == True
        ).first()

    if not ai_config:
        raise HTTPException(status_code=400, detail="未找到可用的AI配置")

    try:
        # Import OpenAI
        from openai import OpenAI

        # Create OpenAI client
        client = OpenAI(
            api_key=ai_config.api_key,
            base_url=ai_config.base_url
        )

        # Prepare the prompt
        system_prompt = """你是一个专业的Python代码生成助手。请根据用户的需求生成高质量的Python代码。

重要要求：
1. 只返回纯Python代码，不要包含任何markdown标记（如```python或```）
2. 不要包含任何解释、说明或额外的文本
3. 生成可以直接执行的完整代码
4. 包含必要的注释说明代码功能
5. 遵循Python编程规范和最佳实践

例如，如果用户要求生成打印"Hello World"的代码，你应该直接返回：
print("Hello World!")

而不是：
```python
print("Hello World!")
```
"""

        user_prompt = f"""请为以下需求生成Python代码：
{request.prompt}

请直接返回可运行的Python代码，不要包含任何markdown格式或额外解释。"""

        # Make API call
        completion = client.chat.completions.create(
            model=ai_config.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        generated_code = completion.choices[0].message.content.strip()

        # Clean up the generated code to remove any markdown formatting
        # Remove ```python and ``` markers if present
        lines = generated_code.split('\n')
        cleaned_lines = []
        in_code_block = False

        for line in lines:
            # Remove markdown code block markers
            if line.strip().startswith('```python'):
                in_code_block = True
                continue
            elif line.strip().startswith('```'):
                if in_code_block:
                    in_code_block = False
                continue
            # Skip empty lines at the beginning
            elif not cleaned_lines and not line.strip():
                continue
            else:
                cleaned_lines.append(line)

        generated_code = '\n'.join(cleaned_lines).strip()
        tokens_used = completion.usage.total_tokens if completion.usage else None

        # Log AI usage
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="ai_code_generate",
            resource_type="ai_config",
            resource_id=ai_config.id,
            details={
                "model": ai_config.model_name,
                "tokens_used": tokens_used,
                "prompt_length": len(request.prompt),
                "response_length": len(generated_code)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        return AICodeGenerateResponse(
            generated_code=generated_code,
            model_used=ai_config.model_name,
            tokens_used=tokens_used
        )

    except Exception as e:
        # Log AI usage failure
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="ai_code_generate",
            resource_type="ai_config",
            resource_id=ai_config.id,
            details={
                "model": ai_config.model_name,
                "error": str(e),
                "prompt_length": len(request.prompt)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )

        raise HTTPException(status_code=500, detail=f"AI代码生成失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)