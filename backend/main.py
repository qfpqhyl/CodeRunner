from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import timedelta, datetime
import subprocess
import tempfile
import os
import time
import secrets
import string
import json
import uuid
from database import get_db, init_db, User, CodeExecution, CodeLibrary, APIKey, SystemLog, AIConfig, UserEnvironment, Post, PostLike, PostFavorite, Comment, CommentLike, PostCodeShare, Follow
from models import UserCreate, UserResponse, UserLogin, Token, CodeExecutionRequest, CodeExecutionResponse, CodeLibraryCreate, CodeLibraryUpdate, CodeLibraryResponse, PasswordChange, PasswordChangeByAdmin, APIKeyCreate, APIKeyResponse, APIKeyInfo, CodeExecuteByAPIRequest, CodeExecuteByAPIResponse, AIConfigCreate, AIConfigUpdate, AIConfigResponse, AICodeGenerateRequest, AICodeGenerateResponse, UserEnvironmentCreate, UserEnvironmentUpdate, UserEnvironmentResponse, EnvironmentInfo, PackageInfo, PackageInstallRequest, PackageInstallResponse, UserProfileUpdate, UserProfileResponse, SystemLogResponse, UserLogQuery, PostCreate, PostUpdate, PostResponse, CommentCreate, CommentUpdate, CommentResponse, PostQuery, CommentQuery, FollowCreate, FollowResponse, UserStatsResponse, CodeLibrarySaveRequest, CodeLibrarySaveResponse
from auth import authenticate_user, create_access_token, get_password_hash, get_current_user, get_current_admin_user, get_api_key_user, ACCESS_TOKEN_EXPIRE_MINUTES
from user_levels import get_user_level_config, can_user_execute, get_daily_execution_count, can_user_make_api_call, get_daily_api_call_count, USER_LEVELS

app = FastAPI(title="CodeRunner API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Vercel deployment
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

        # Determine which python executable to use based on conda_env
        if code_request.conda_env and code_request.conda_env != "base":
            python_executable = f"conda run -n {code_request.conda_env} python"
        else:
            python_executable = "python"

        # Execute the Python code with user level limits
        result = subprocess.run(
            python_executable.split() + [temp_file],
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
        tags=code_data.tags,
        conda_env=code_data.conda_env
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
    update_data = code_update.model_dump(exclude_unset=True)
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

        # Determine which python executable to use based on conda_env
        if code_entry.conda_env and code_entry.conda_env != "base":
            python_executable = f"conda run -n {code_entry.conda_env} python"
        else:
            python_executable = "python"

        # Execute the Python code with user level limits
        result = subprocess.run(
            python_executable.split() + [temp_file],
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

@app.get("/conda-environments")
def get_conda_environments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get available conda environments based on user permissions"""
    try:
        # Get user's accessible environments from database
        accessible_envs = set()

        # Always include base environment
        accessible_envs.add("base")

        # Add user's own environments
        user_envs = db.query(UserEnvironment).filter(
            UserEnvironment.user_id == current_user.id,
            UserEnvironment.is_active == True
        ).all()
        for env in user_envs:
            accessible_envs.add(env.env_name)

        # Add public environments (for non-admin users)
        if not current_user.is_admin:
            public_envs = db.query(UserEnvironment).filter(
                UserEnvironment.is_public == True,
                UserEnvironment.is_active == True,
                UserEnvironment.user_id != current_user.id
            ).all()
            for env in public_envs:
                accessible_envs.add(env.env_name)

        # If admin, add all active environments except runner
        if current_user.is_admin:
            all_envs = db.query(UserEnvironment).filter(
                UserEnvironment.is_active == True
            ).all()
            for env in all_envs:
                if env.env_name != "runner":  # Admin can't see runner environment
                    accessible_envs.add(env.env_name)

        # Get actual conda environments to verify which ones exist
        result = subprocess.run(
            ["conda", "env", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            # Parse conda env list output
            conda_envs = set()
            lines = result.stdout.split('\n')

            for line in lines:
                line = line.strip()
                # Skip empty lines, headers, and lines with #
                if not line or line.startswith('#') or line.startswith('Name'):
                    continue

                # Extract environment name (first column)
                parts = line.split()
                if parts:
                    env_name = parts[0]
                    conda_envs.add(env_name)

            # Only return environments that exist in conda and user has access to
            final_envs = list(accessible_envs.intersection(conda_envs))

            # Ensure base is always included even if not in conda list
            if "base" not in final_envs:
                final_envs.insert(0, "base")

            return final_envs
        else:
            # Fallback: return base + user environments from database
            return list(accessible_envs)

    except subprocess.TimeoutExpired:
        # Return base + user environments from database on timeout
        return ["base"]
    except Exception as e:
        # Log error but return basic environments
        print(f"Failed to get conda environments: {e}")
        return ["base"]

@app.post("/user-environments", response_model=UserEnvironmentResponse)
def create_user_environment(
    env_data: UserEnvironmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Create a new user environment"""
    # Check if user has reached their environment limit (non-admin users can only have 1)
    if not current_user.is_admin:
        current_count = db.query(UserEnvironment).filter(UserEnvironment.user_id == current_user.id).count()
        if current_count >= 1:
            raise HTTPException(
                status_code=429,
                detail="普通用户只能创建一个环境"
            )

    # Check if environment name already exists
    existing_env = db.query(UserEnvironment).filter(UserEnvironment.env_name == env_data.env_name).first()
    if existing_env:
        raise HTTPException(status_code=400, detail="环境名称已存在")

    # Validate environment name format
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', env_data.env_name):
        raise HTTPException(status_code=400, detail="环境名称只能包含字母、数字、下划线和连字符")

    try:
        # Create conda environment
        create_cmd = f"conda create -n {env_data.env_name} python={env_data.python_version} -y"
        result = subprocess.run(
            create_cmd.split(),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "环境创建失败"
            raise HTTPException(status_code=500, detail=f"Conda环境创建失败: {error_msg}")

        # Install additional packages if specified
        if env_data.packages:
            pip_cmd = f"conda run -n {env_data.env_name} pip"
            for package in env_data.packages:
                install_cmd = f"{pip_cmd} install {package}".split()
                install_result = subprocess.run(
                    install_cmd,
                    capture_output=True,
                    text=True,
                    timeout=120  # 2 minutes per package
                )
                if install_result.returncode != 0:
                    # Log warning but continue with environment creation
                    print(f"Failed to install package {package}: {install_result.stderr}")

        # Generate conda environment YAML
        conda_yaml = f"""name: {env_data.env_name}
channels:
  - defaults
dependencies:
  - python={env_data.python_version}
"""
        if env_data.packages:
            for package in env_data.packages:
                conda_yaml += f"  - {package}\n"

        # Create database record
        user_env = UserEnvironment(
            user_id=current_user.id,
            env_name=env_data.env_name,
            display_name=env_data.display_name,
            description=env_data.description,
            python_version=env_data.python_version,
            conda_yaml=conda_yaml,
            is_public=env_data.is_public
        )

        db.add(user_env)
        db.commit()
        db.refresh(user_env)

        # Log environment creation
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="environment_create",
            resource_type="user_environment",
            resource_id=user_env.id,
            details={
                "env_name": env_data.env_name,
                "display_name": env_data.display_name,
                "python_version": env_data.python_version,
                "packages": env_data.packages,
                "is_public": env_data.is_public
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        # Add owner name to response
        user_env.owner_name = current_user.username
        return user_env

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="环境创建超时")
    except HTTPException:
        raise
    except Exception as e:
        # Log failed environment creation
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="environment_create",
            resource_type="user_environment",
            details={
                "env_name": env_data.env_name,
                "error": str(e)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"环境创建失败: {str(e)}")

@app.get("/user-environments", response_model=list[UserEnvironmentResponse])
def get_user_environments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get environments available to the current user"""
    environments = []

    # Always include base environment
    environments.append({
        "id": 0,
        "user_id": 0,
        "env_name": "base",
        "display_name": "基础环境",
        "description": "系统默认的conda基础环境",
        "python_version": "3.11",
        "is_active": True,
        "is_public": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_used": None,
        "owner_name": "system"
    })

    # Get user's own environments
    user_envs = db.query(UserEnvironment).filter(UserEnvironment.user_id == current_user.id).all()
    for env in user_envs:
        env.owner_name = current_user.username
        environments.append(env)

    # Get public environments from other users (excluding admin-only)
    if not current_user.is_admin:
        public_envs = db.query(UserEnvironment).filter(
            UserEnvironment.is_public == True,
            UserEnvironment.user_id != current_user.id
        ).all()
        for env in public_envs:
            owner = db.query(User).filter(User.id == env.user_id).first()
            env.owner_name = owner.username if owner else "unknown"
            environments.append(env)

    return environments

@app.get("/user-environments/{env_id}", response_model=UserEnvironmentResponse)
def get_user_environment(
    env_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific user environment"""
    # Handle base environment (id = 0)
    if env_id == 0:
        return {
            "id": 0,
            "user_id": 0,
            "env_name": "base",
            "display_name": "基础环境",
            "description": "系统默认的conda基础环境",
            "python_version": "3.11",
            "is_active": True,
            "is_public": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_used": None,
            "owner_name": "system"
        }

    # Get user environment
    env = db.query(UserEnvironment).filter(UserEnvironment.id == env_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="环境未找到")

    # Check permissions
    if env.user_id != current_user.id and not env.is_public and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权访问此环境")

    # Add owner name
    owner = db.query(User).filter(User.id == env.user_id).first()
    env.owner_name = owner.username if owner else "unknown"

    return env

@app.put("/user-environments/{env_id}", response_model=UserEnvironmentResponse)
def update_user_environment(
    env_id: int,
    env_update: UserEnvironmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Update a user environment"""
    # Cannot update base environment
    if env_id == 0:
        raise HTTPException(status_code=400, detail="不能修改基础环境")

    env = db.query(UserEnvironment).filter(UserEnvironment.id == env_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="环境未找到")

    # Check permissions - only owner or admin can update
    if env.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权修改此环境")

    # Update fields
    update_data = env_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(env, field, value)

    env.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(env)

    # Log environment update
    log_system_event(
        db=db,
        user_id=current_user.id,
        action="environment_update",
        resource_type="user_environment",
        resource_id=env.id,
        details=update_data,
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        status="success"
    )

    # Add owner name
    owner = db.query(User).filter(User.id == env.user_id).first()
    env.owner_name = owner.username if owner else "unknown"

    return env

@app.delete("/user-environments/{env_id}")
def delete_user_environment(
    env_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Delete a user environment"""
    # Cannot delete base environment
    if env_id == 0:
        raise HTTPException(status_code=400, detail="不能删除基础环境")

    env = db.query(UserEnvironment).filter(UserEnvironment.id == env_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="环境未找到")

    # Check permissions - only owner or admin can delete
    if env.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权删除此环境")

    try:
        # Remove conda environment
        remove_cmd = f"conda env remove -n {env.env_name} -y"
        result = subprocess.run(
            remove_cmd.split(),
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "环境删除失败"
            raise HTTPException(status_code=500, detail=f"Conda环境删除失败: {error_msg}")

        # Remove from database
        db.delete(env)
        db.commit()

        # Log environment deletion
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="environment_delete",
            resource_type="user_environment",
            resource_id=env.id,
            details={
                "env_name": env.env_name,
                "display_name": env.display_name
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        return {"message": "环境删除成功"}

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="环境删除超时")
    except HTTPException:
        raise
    except Exception as e:
        # Log failed environment deletion
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="environment_delete",
            resource_type="user_environment",
            resource_id=env.id,
            details={
                "env_name": env.env_name,
                "error": str(e)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"环境删除失败: {str(e)}")

# Admin endpoints for managing all user environments
@app.get("/admin/user-environments", response_model=list[UserEnvironmentResponse])
def admin_get_all_environments(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all user environments (admin only)"""
    environments = db.query(UserEnvironment).all()
    for env in environments:
        owner = db.query(User).filter(User.id == env.user_id).first()
        env.owner_name = owner.username if owner else "unknown"
    return environments

@app.delete("/admin/user-environments/{env_id}")
def admin_delete_environment(
    env_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Admin can delete any user environment"""
    env = db.query(UserEnvironment).filter(UserEnvironment.id == env_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="环境未找到")

    try:
        # Remove conda environment
        remove_cmd = f"conda env remove -n {env.env_name} -y"
        result = subprocess.run(
            remove_cmd.split(),
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "环境删除失败"
            raise HTTPException(status_code=500, detail=f"Conda环境删除失败: {error_msg}")

        # Remove from database
        db.delete(env)
        db.commit()

        # Log environment deletion
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="admin_environment_delete",
            resource_type="user_environment",
            resource_id=env.id,
            details={
                "env_name": env.env_name,
                "display_name": env.display_name,
                "original_owner_id": env.user_id
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        return {"message": "环境删除成功"}

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="环境删除超时")
    except Exception as e:
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="admin_environment_delete",
            resource_type="user_environment",
            resource_id=env.id,
            details={
                "env_name": env.env_name,
                "error": str(e)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"环境删除失败: {str(e)}")

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
    update_data = config_update.model_dump(exclude_unset=True)
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

# Database Import/Export endpoints (Admin only)
@app.post("/admin/database/export")
def export_database(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Export database to SQL file"""
    try:
        import sqlite3
        from io import BytesIO
        import zipfile
        from datetime import datetime

        # Get database file path
        db_path = "coderunner.db"

        # Create in-memory zip file
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add database file
            zip_file.write(db_path, "coderunner.db")

            # Create metadata file
            metadata = {
                "export_time": datetime.utcnow().isoformat(),
                "exported_by": current_user.username,
                "user_id": current_user.id,
                "database_path": db_path,
                "tables": {
                    "users": db.query(User).count(),
                    "code_executions": db.query(CodeExecution).count(),
                    "code_library": db.query(CodeLibrary).count(),
                    "api_keys": db.query(APIKey).count(),
                    "ai_configs": db.query(AIConfig).count(),
                    "system_logs": db.query(SystemLog).count()
                }
            }

            metadata_content = f"""# CodeRunner Database Export

Generated: {metadata['export_time']}
Exported by: {metadata['exported_by']} (ID: {metadata['user_id']})
Database file: {metadata['database_path']}

## Table Statistics
- Users: {metadata['tables']['users']}
- Code Executions: {metadata['tables']['code_executions']}
- Code Library: {metadata['tables']['code_library']}
- API Keys: {metadata['tables']['api_keys']}
- AI Configs: {metadata['tables']['ai_configs']}
- System Logs: {metadata['tables']['system_logs']}

## Instructions
To import this database:
1. Stop the CodeRunner backend service
2. Replace the existing coderunner.db file with the one in this archive
3. Restart the backend service
4. Verify data integrity

## Important Notes
- This backup contains all user data, including sensitive information
- Store this backup securely and only restore to trusted environments
- Consider creating regular backups for disaster recovery

---
Export generated by CodeRunner Admin Panel
"""

            zip_file.writestr("export_info.txt", metadata_content)

        # Log the export action
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="database_export",
            resource_type="database",
            details=metadata,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        # Return the zip file
        zip_buffer.seek(0)
        from fastapi.responses import StreamingResponse

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"coderunner_backup_{timestamp}.zip"

        return StreamingResponse(
            BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        # Log failed export
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="database_export",
            resource_type="database",
            details={"error": str(e)},
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )

        raise HTTPException(status_code=500, detail=f"数据库导出失败: {str(e)}")

@app.post("/admin/database/import")
def import_database(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Import database from uploaded file"""
    try:
        import tempfile
        import zipfile
        import os
        from datetime import datetime

        if not file:
            raise HTTPException(status_code=400, detail="请上传数据库备份文件")

        # Check file type (should be zip)
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="只能上传 ZIP 格式的备份文件")

        # Check file size (max 100MB)
        file_size = 0
        content = file.file.read(1024 * 1024)  # Read 1MB at a time to check size
        while content:
            file_size += len(content)
            if file_size > 100 * 1024 * 1024:  # 100MB limit
                raise HTTPException(status_code=400, detail="备份文件大小不能超过 100MB")
            content = file.file.read(1024 * 1024)

        # Reset file pointer
        file.file.seek(0)

        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write uploaded file to temp location
            temp_zip_path = os.path.join(temp_dir, "backup.zip")
            with open(temp_zip_path, "wb") as f:
                content = file.file.read(8192)  # Read in chunks
                while content:
                    f.write(content)
                    content = file.file.read(8192)

            # Extract zip file
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Check for database file
            db_backup_path = os.path.join(temp_dir, "coderunner.db")
            if not os.path.exists(db_backup_path):
                raise HTTPException(status_code=400, detail="备份文件中未找到数据库文件")

            # Validate the backup file
            import sqlite3
            conn = sqlite3.connect(db_backup_path)
            cursor = conn.cursor()

            # Check if database has required tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            required_tables = {"users", "code_executions", "code_library", "api_keys", "ai_configs", "system_logs"}

            missing_tables = required_tables - tables
            if missing_tables:
                conn.close()
                raise HTTPException(
                    status_code=400,
                    detail=f"备份文件缺少必要的数据表: {', '.join(missing_tables)}"
                )

            # Get backup statistics
            backup_stats = {}
            for table in required_tables:
                if table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    backup_stats[table] = cursor.fetchone()[0]
                else:
                    backup_stats[table] = 0

            conn.close()

            # Backup current database before replacing
            current_db_path = "coderunner.db"
            backup_current_path = f"coderunner_backup_before_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

            if os.path.exists(current_db_path):
                import shutil
                shutil.copy2(current_db_path, backup_current_path)

            # Replace current database with backup
            import shutil
            shutil.copy2(db_backup_path, current_db_path)

            # Reinitialize database connection
            from database import engine, SessionLocal
            from sqlalchemy import create_engine

            # Dispose current engine
            engine.dispose()

            # Recreate engine
            from database import SQLALCHEMY_DATABASE_URL
            new_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

            # Test new database connection
            test_db = SessionLocal(bind=new_engine)
            try:
                # Verify database is accessible
                test_db.execute(text("SELECT 1"))
                test_db.close()
            except Exception as test_error:
                # If test fails, restore backup
                if os.path.exists(backup_current_path):
                    shutil.copy2(backup_current_path, current_db_path)
                raise HTTPException(
                    status_code=500,
                    detail=f"导入后数据库验证失败，已恢复原数据库: {str(test_error)}"
                )

            # Log the import action
            import_details = {
                "backup_stats": backup_stats,
                "backup_file_saved": backup_current_path if os.path.exists(backup_current_path) else None,
                "import_time": datetime.utcnow().isoformat()
            }

            log_system_event(
                db=db,
                user_id=current_user.id,
                action="database_import",
                resource_type="database",
                details=import_details,
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"],
                status="success"
            )

            return {
                "message": "数据库导入成功",
                "backup_stats": backup_stats,
                "previous_backup": backup_current_path if os.path.exists(backup_current_path) else None
            }

    except HTTPException:
        raise
    except Exception as e:
        # Log failed import
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="database_import",
            resource_type="database",
            details={"error": str(e)},
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )

        raise HTTPException(status_code=500, detail=f"数据库导入失败: {str(e)}")

@app.get("/admin/database/info")
def get_database_info(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get database information and statistics"""
    try:
        import os
        from datetime import datetime

        # Get database file info
        db_path = "coderunner.db"
        db_info = {}

        if os.path.exists(db_path):
            stat = os.stat(db_path)
            db_info = {
                "file_size": stat.st_size,
                "file_size_human": _format_file_size(stat.st_size),
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "file_path": os.path.abspath(db_path)
            }

        # Get table statistics
        table_stats = {
            "users": db.query(User).count(),
            "code_executions": db.query(CodeExecution).count(),
            "code_library": db.query(CodeLibrary).count(),
            "api_keys": db.query(APIKey).count(),
            "ai_configs": db.query(AIConfig).count(),
            "system_logs": db.query(SystemLog).count()
        }

        # Get additional statistics
        user_stats = {
            "total_users": table_stats["users"],
            "active_users": db.query(User).filter(User.is_active == True).count(),
            "admin_users": db.query(User).filter(User.is_admin == True).count()
        }

        # Get recent activity
        recent_executions = db.query(CodeExecution).order_by(CodeExecution.created_at.desc()).limit(1).first()
        recent_log = db.query(SystemLog).order_by(SystemLog.created_at.desc()).limit(1).first()

        return {
            "database_file": db_info,
            "table_statistics": table_stats,
            "user_statistics": user_stats,
            "recent_activity": {
                "last_execution": recent_executions.created_at.isoformat() if recent_executions else None,
                "last_log": recent_log.created_at.isoformat() if recent_log else None
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库信息失败: {str(e)}")

def _format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.2f} {size_names[i]}"

# Environment Management endpoints
@app.get("/environments/{env_name}/info")
def get_environment_info(
    env_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get information about a specific conda environment"""
    # Check if user has permission to access this environment
    if env_name != "base":
        # Check if it's a user environment
        user_env = db.query(UserEnvironment).filter(
            UserEnvironment.env_name == env_name,
            UserEnvironment.is_active == True
        ).first()

        if user_env:
            # Check permissions
            if (user_env.user_id != current_user.id and
                not user_env.is_public and
                not current_user.is_admin):
                raise HTTPException(status_code=403, detail="无权访问此环境")
        else:
            # If not in user environments, only admin can access system environments (except base)
            if not current_user.is_admin:
                raise HTTPException(status_code=403, detail="无权访问此环境")

            # Admin cannot access runner environment
            if env_name == "runner":
                raise HTTPException(status_code=403, detail="无权访问此环境")
    try:
        # Get Python version and environment info
        python_cmd = f"conda run -n {env_name} python" if env_name != "base" else "python"

        # Get Python version
        version_result = subprocess.run(
            f"{python_cmd} --version".split(),
            capture_output=True,
            text=True,
            timeout=10
        )

        python_version = version_result.stdout.strip() if version_result.returncode == 0 else "Unknown"

        # Get Python executable path
        path_result = subprocess.run(
            f"{python_cmd} -c \"import sys; print(sys.executable)\"".split(),
            capture_output=True,
            text=True,
            timeout=10
        )

        python_path = path_result.stdout.strip() if path_result.returncode == 0 else "Unknown"

        # Get site packages path
        site_packages_result = subprocess.run(
            f"{python_cmd} -c \"import site; print(site.getsitepackages()[0])\"".split(),
            capture_output=True,
            text=True,
            timeout=10
        )

        site_packages_path = site_packages_result.stdout.strip() if site_packages_result.returncode == 0 else "Unknown"

        # Count installed packages
        pip_list_result = subprocess.run(
            f"{python_cmd} -m pip list".split(),
            capture_output=True,
            text=True,
            timeout=15
        )

        package_count = 0
        if pip_list_result.returncode == 0:
            lines = pip_list_result.stdout.split('\n')
            for line in lines[2:]:  # Skip header lines
                if line.strip():
                    package_count += 1

        return {
            "name": env_name,
            "python_version": python_version,
            "python_path": python_path,
            "site_packages_path": site_packages_path,
            "package_count": package_count,
            "is_base": env_name == "base",
            "environment_type": "系统默认" if env_name == "base" else "虚拟环境"
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="获取环境信息超时")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取环境信息失败: {str(e)}")

@app.get("/environments/{env_name}/packages")
def get_environment_packages(
    env_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get packages installed in a specific conda environment"""
    # Check if user has permission to access this environment
    if env_name != "base":
        # Check if it's a user environment
        user_env = db.query(UserEnvironment).filter(
            UserEnvironment.env_name == env_name,
            UserEnvironment.is_active == True
        ).first()

        if user_env:
            # Check permissions
            if (user_env.user_id != current_user.id and
                not user_env.is_public and
                not current_user.is_admin):
                raise HTTPException(status_code=403, detail="无权访问此环境")
        else:
            # If not in user environments, only admin can access system environments (except base)
            if not current_user.is_admin:
                raise HTTPException(status_code=403, detail="无权访问此环境")

            # Admin cannot access runner environment
            if env_name == "runner":
                raise HTTPException(status_code=403, detail="无权访问此环境")
    try:
        # Get Python version and installed packages
        python_cmd = f"conda run -n {env_name} python" if env_name != "base" else "python"

        # Get Python version
        version_result = subprocess.run(
            f"{python_cmd} --version".split(),
            capture_output=True,
            text=True,
            timeout=10
        )

        python_version = version_result.stdout.strip() if version_result.returncode == 0 else "Unknown"

        # Get installed packages using pip list
        pip_list_result = subprocess.run(
            f"{python_cmd} -m pip list --format=json".split(),
            capture_output=True,
            text=True,
            timeout=30
        )

        if pip_list_result.returncode != 0:
            # Fallback to pip list without json format
            pip_list_result = subprocess.run(
                f"{python_cmd} -m pip list".split(),
                capture_output=True,
                text=True,
                timeout=30
            )

            if pip_list_result.returncode == 0:
                # Parse the output manually
                packages = []
                lines = pip_list_result.stdout.split('\n')
                for line in lines[2:]:  # Skip header lines
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            package_name = parts[0]
                            version = parts[1]
                            packages.append({
                                "name": package_name,
                                "version": version,
                                "latest_version": None,
                                "size": None,
                                "location": None
                            })
                return packages

        # Parse JSON output
        import json
        packages_info = json.loads(pip_list_result.stdout)

        # Enhance package information
        packages = []
        for pkg in packages_info:
            packages.append({
                "name": pkg.get("name", ""),
                "version": pkg.get("version", ""),
                "latest_version": None,  # Could be implemented with pip list --outdated
                "size": None,  # Size info not available in basic pip list
                "location": None
            })

        return packages

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="获取包列表超时")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取包列表失败: {str(e)}")

@app.post("/environments/{env_name}/packages/install")
def install_package(
    env_name: str,
    package_data: dict,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    """Install a package in a specific conda environment"""
    # Check if user has permission to access this environment
    if env_name != "base":
        # Check if it's a user environment
        user_env = db.query(UserEnvironment).filter(
            UserEnvironment.env_name == env_name,
            UserEnvironment.is_active == True
        ).first()

        if user_env:
            # Check permissions - only owner or admin can install packages
            if user_env.user_id != current_user.id and not current_user.is_admin:
                raise HTTPException(status_code=403, detail="无权修改此环境")
        else:
            # If not in user environments, only admin can access system environments (except base)
            if not current_user.is_admin:
                raise HTTPException(status_code=403, detail="无权访问此环境")

            # Admin cannot install packages in runner environment
            if env_name == "runner":
                raise HTTPException(status_code=403, detail="无权修改此环境")
    try:
        # Protect base environment - only admins can modify it
        if env_name == "base" and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以修改基础环境")

        package_name = package_data.get("package_name", "")
        if not package_name:
            raise HTTPException(status_code=400, detail="请提供包名")

        # Validate package name format
        import re
        if not re.match(r'^[a-zA-Z0-9\-_.==>=<]+$', package_name):
            raise HTTPException(status_code=400, detail="包名格式无效")

        # Determine python command
        python_cmd = f"conda run -n {env_name} python" if env_name != "base" else "python"
        pip_cmd = f"conda run -n {env_name} pip" if env_name != "base" else "pip"

        # Install the package
        install_result = subprocess.run(
            f"{pip_cmd} install {package_name}".split(),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout for installation
        )

        if install_result.returncode != 0:
            error_msg = install_result.stderr.strip() if install_result.stderr else "安装失败"
            raise HTTPException(status_code=500, detail=f"包安装失败: {error_msg}")

        # Log the package installation
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_install",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "success": True
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        return {"message": f"包 {package_name} 安装成功"}

    except subprocess.TimeoutExpired:
        # Log timeout
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_install",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "error": "timeout"
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=408, detail="包安装超时")
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_install",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "error": str(e)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"包安装失败: {str(e)}")

@app.delete("/environments/{env_name}/packages/{package_name}")
def uninstall_package(
    env_name: str,
    package_name: str,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    """Uninstall a package from a specific conda environment"""
    # Check if user has permission to access this environment
    if env_name != "base":
        # Check if it's a user environment
        user_env = db.query(UserEnvironment).filter(
            UserEnvironment.env_name == env_name,
            UserEnvironment.is_active == True
        ).first()

        if user_env:
            # Check permissions - only owner or admin can uninstall packages
            if user_env.user_id != current_user.id and not current_user.is_admin:
                raise HTTPException(status_code=403, detail="无权修改此环境")
        else:
            # If not in user environments, only admin can access system environments (except base)
            if not current_user.is_admin:
                raise HTTPException(status_code=403, detail="无权访问此环境")

            # Admin cannot uninstall packages in runner environment
            if env_name == "runner":
                raise HTTPException(status_code=403, detail="无权修改此环境")
    try:
        # Protect base environment - only admins can modify it
        if env_name == "base" and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以修改基础环境")

        # Validate package name
        import re
        if not re.match(r'^[a-zA-Z0-9\-_.]+$', package_name):
            raise HTTPException(status_code=400, detail="包名格式无效")

        # Don't allow uninstalling critical packages
        critical_packages = {"pip", "setuptools", "wheel", "python"}
        if package_name.lower() in critical_packages:
            raise HTTPException(status_code=400, detail=f"不能卸载关键包: {package_name}")

        # Determine pip command
        pip_cmd = f"conda run -n {env_name} pip" if env_name != "base" else "pip"

        # Uninstall the package
        uninstall_result = subprocess.run(
            f"{pip_cmd} uninstall -y {package_name}".split(),
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes timeout for uninstallation
        )

        if uninstall_result.returncode != 0:
            error_msg = uninstall_result.stderr.strip() if uninstall_result.stderr else "卸载失败"
            raise HTTPException(status_code=500, detail=f"包卸载失败: {error_msg}")

        # Log the package uninstallation
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_uninstall",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "success": True
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        return {"message": f"包 {package_name} 卸载成功"}

    except subprocess.TimeoutExpired:
        # Log timeout
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_uninstall",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "error": "timeout"
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=408, detail="包卸载超时")
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_uninstall",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "error": str(e)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"包卸载失败: {str(e)}")

@app.put("/environments/{env_name}/packages/{package_name}/upgrade")
def upgrade_package(
    env_name: str,
    package_name: str,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    """Upgrade a package in a specific conda environment"""
    # Check if user has permission to access this environment
    if env_name != "base":
        # Check if it's a user environment
        user_env = db.query(UserEnvironment).filter(
            UserEnvironment.env_name == env_name,
            UserEnvironment.is_active == True
        ).first()

        if user_env:
            # Check permissions - only owner or admin can upgrade packages
            if user_env.user_id != current_user.id and not current_user.is_admin:
                raise HTTPException(status_code=403, detail="无权修改此环境")
        else:
            # If not in user environments, only admin can access system environments (except base)
            if not current_user.is_admin:
                raise HTTPException(status_code=403, detail="无权访问此环境")

            # Admin cannot upgrade packages in runner environment
            if env_name == "runner":
                raise HTTPException(status_code=403, detail="无权修改此环境")
    try:
        # Protect base environment - only admins can modify it
        if env_name == "base" and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以修改基础环境")

        # Validate package name
        import re
        if not re.match(r'^[a-zA-Z0-9\-_.]+$', package_name):
            raise HTTPException(status_code=400, detail="包名格式无效")

        # Determine pip command
        pip_cmd = f"conda run -n {env_name} pip" if env_name != "base" else "pip"

        # Upgrade the package
        upgrade_result = subprocess.run(
            f"{pip_cmd} install --upgrade {package_name}".split(),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout for upgrade
        )

        if upgrade_result.returncode != 0:
            error_msg = upgrade_result.stderr.strip() if upgrade_result.stderr else "升级失败"
            raise HTTPException(status_code=500, detail=f"包升级失败: {error_msg}")

        # Log the package upgrade
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_upgrade",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "success": True
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        return {"message": f"包 {package_name} 升级成功"}

    except subprocess.TimeoutExpired:
        # Log timeout
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_upgrade",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "error": "timeout"
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=408, detail="包升级超时")
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_upgrade",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "error": str(e)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"包升级失败: {str(e)}")

# User Profile endpoints
@app.get("/profile", response_model=UserProfileResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile information"""
    return current_user

@app.put("/profile", response_model=UserProfileResponse)
def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Update current user's profile information"""
    # Update fields
    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    # Log profile update
    log_system_event(
        db=db,
        user_id=current_user.id,
        action="profile_update",
        resource_type="user_profile",
        resource_id=current_user.id,
        details=update_data,
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        status="success"
    )

    return current_user

@app.post("/profile/upload-avatar")
def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Upload user avatar image"""
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="只能上传图片文件")

    # Check file size (max 5MB)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="图片文件大小不能超过5MB")

    try:
        import os
        import uuid

        # Create avatars directory if it doesn't exist
        avatars_dir = "data/avatars"
        os.makedirs(avatars_dir, exist_ok=True)

        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(avatars_dir, unique_filename)

        # Save file directly without processing
        with open(file_path, "wb") as buffer:
            content = file.file.read()
            buffer.write(content)

        # Update user avatar URL
        avatar_url = f"/api/avatars/{unique_filename}"
        current_user.avatar_url = avatar_url
        current_user.updated_at = datetime.utcnow()
        db.commit()

        # Log avatar upload
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="avatar_upload",
            resource_type="user_profile",
            resource_id=current_user.id,
            details={
                "avatar_url": avatar_url,
                "file_size": file_size,
                "original_filename": file.filename
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        return {"avatar_url": avatar_url, "message": "头像上传成功"}

    except Exception as e:
        # Log failed upload
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="avatar_upload",
            resource_type="user_profile",
            resource_id=current_user.id,
            details={
                "error": str(e),
                "original_filename": file.filename
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"头像上传失败: {str(e)}")

@app.get("/api/avatars/{filename}")
def get_avatar(filename: str):
    """Serve avatar images"""
    from fastapi.responses import FileResponse
    import os

    file_path = os.path.join("data/avatars", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="头像文件未找到")

    return FileResponse(file_path, media_type="image/jpeg")

@app.delete("/profile/avatar")
def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Delete user avatar"""
    if not current_user.avatar_url:
        raise HTTPException(status_code=400, detail="当前没有头像")

    try:
        import os

        # Extract filename from URL
        filename = current_user.avatar_url.split('/')[-1]
        file_path = os.path.join("data/avatars", filename)

        # Delete file if exists
        if os.path.exists(file_path):
            os.remove(file_path)

        # Update user avatar URL
        current_user.avatar_url = None
        current_user.updated_at = datetime.utcnow()
        db.commit()

        # Log avatar deletion
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="avatar_delete",
            resource_type="user_profile",
            resource_id=current_user.id,
            details={"deleted_filename": filename},
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        return {"message": "头像删除成功"}

    except Exception as e:
        # Log failed deletion
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="avatar_delete",
            resource_type="user_profile",
            resource_id=current_user.id,
            details={"error": str(e)},
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"头像删除失败: {str(e)}")

# User Activity Logs endpoints
@app.get("/profile/logs", response_model=dict)
def get_user_activity_logs(
    query: UserLogQuery = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's activity logs with filtering and pagination"""
    # Build query
    db_query = db.query(SystemLog).filter(SystemLog.user_id == current_user.id)

    # Apply filters
    if query.action:
        db_query = db_query.filter(SystemLog.action == query.action)
    if query.resource_type:
        db_query = db_query.filter(SystemLog.resource_type == query.resource_type)
    if query.status:
        db_query = db_query.filter(SystemLog.status == query.status)
    if query.start_date:
        try:
            start_dt = query.start_date
            if isinstance(start_dt, str):
                start_dt = datetime.fromisoformat(start_dt.replace('Z', '+00:00'))
            db_query = db_query.filter(SystemLog.created_at >= start_dt)
        except ValueError:
            pass
    if query.end_date:
        try:
            end_dt = query.end_date
            if isinstance(end_dt, str):
                end_dt = datetime.fromisoformat(end_dt.replace('Z', '+00:00'))
            db_query = db_query.filter(SystemLog.created_at <= end_dt)
        except ValueError:
            pass

    # Count total logs
    total_count = db_query.count()

    # Calculate pagination
    page = max(1, query.page)
    page_size = min(100, max(1, query.page_size))  # Limit page size to 100
    offset = (page - 1) * page_size

    # Get paginated logs
    logs = db_query.order_by(SystemLog.created_at.desc()).offset(offset).limit(page_size).all()

    # Convert logs to response format
    log_responses = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": json.loads(log.details) if log.details else None,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "status": log.status,
            "created_at": log.created_at.isoformat()
        }
        log_responses.append(SystemLogResponse(**log_dict))

    return {
        "logs": log_responses,
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }

@app.get("/profile/logs/actions")
def get_user_log_actions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get available log actions for the current user"""
    actions = db.query(SystemLog.action).filter(
        SystemLog.user_id == current_user.id
    ).distinct().all()
    return [action[0] for action in actions if action[0]]

@app.get("/profile/logs/resource-types")
def get_user_log_resource_types(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get available resource types for the current user"""
    resource_types = db.query(SystemLog.resource_type).filter(
        SystemLog.user_id == current_user.id
    ).distinct().all()
    return [rt[0] for rt in resource_types if rt[0]]

@app.get("/profile/stats")
def get_user_profile_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user's profile statistics"""
    # Get basic user stats
    level_config = get_user_level_config(current_user.user_level)

    # Execution stats
    total_executions = db.query(CodeExecution).filter(CodeExecution.user_id == current_user.id).count()
    successful_executions = db.query(CodeExecution).filter(
        CodeExecution.user_id == current_user.id,
        CodeExecution.status == "success"
    ).count()

    # Library stats
    library_count = db.query(CodeLibrary).filter(CodeLibrary.user_id == current_user.id).count()
    public_library_count = db.query(CodeLibrary).filter(
        CodeLibrary.user_id == current_user.id,
        CodeLibrary.is_public == True
    ).count()

    # API key stats
    api_key_count = db.query(APIKey).filter(APIKey.user_id == current_user.id).count()
    active_api_key_count = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True
    ).count()

    # AI config stats
    ai_config_count = db.query(AIConfig).filter(AIConfig.user_id == current_user.id).count()

    # Environment stats
    environment_count = db.query(UserEnvironment).filter(
        UserEnvironment.user_id == current_user.id,
        UserEnvironment.is_active == True
    ).count()

    # Recent activity (last 7 days)
    from datetime import timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    recent_executions = db.query(CodeExecution).filter(
        CodeExecution.user_id == current_user.id,
        CodeExecution.created_at >= seven_days_ago
    ).count()

    recent_logins = db.query(SystemLog).filter(
        SystemLog.user_id == current_user.id,
        SystemLog.action == "user_login",
        SystemLog.created_at >= seven_days_ago
    ).count()

    return {
        "user_info": {
            "username": current_user.username,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "user_level": current_user.user_level,
            "is_admin": current_user.is_admin,
            "avatar_url": current_user.avatar_url,
            "bio": current_user.bio,
            "location": current_user.location,
            "website": current_user.website,
            "github_username": current_user.github_username,
            "company": current_user.company,
            "created_at": current_user.created_at.isoformat(),
            "updated_at": current_user.updated_at.isoformat()
        },
        "usage_stats": {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": round(successful_executions / total_executions * 100, 2) if total_executions > 0 else 0,
            "library_count": library_count,
            "public_library_count": public_library_count,
            "api_key_count": api_key_count,
            "active_api_key_count": active_api_key_count,
            "ai_config_count": ai_config_count,
            "environment_count": environment_count
        },
        "recent_activity": {
            "executions_last_7_days": recent_executions,
            "logins_last_7_days": recent_logins
        },
        "user_level_config": level_config
    }

# Community API endpoints
@app.post("/community/posts", response_model=PostResponse)
def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Create a new community post"""
    try:
        # Create the post
        post = Post(
            user_id=current_user.id,
            title=post_data.title,
            content=post_data.content,
            summary=post_data.summary,
            tags=post_data.tags,
            is_public=post_data.is_public
        )

        db.add(post)
        db.commit()
        db.refresh(post)

        # Handle code library sharing
        if post_data.shared_code_ids:
            for code_id in post_data.shared_code_ids:
                # Verify the code belongs to the user or is public
                code = db.query(CodeLibrary).filter(
                    CodeLibrary.id == code_id
                ).first()

                if code and (code.user_id == current_user.id or code.is_public):
                    post_code_share = PostCodeShare(
                        post_id=post.id,
                        code_library_id=code_id,
                        share_order=len(post.shared_codes) if hasattr(post, 'shared_codes') else 0
                    )
                    db.add(post_code_share)

                    # Mark code as shared via post and make it publicly accessible
                    if code.user_id == current_user.id:
                        code.is_shared_via_post = True
                        code.shared_post_id = post.id
                        # Make the code public if the post is public
                        if post_data.is_public:
                            code.is_public = True

        db.commit()

        # Log post creation
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="post_create",
            resource_type="post",
            resource_id=post.id,
            details={
                "title": post_data.title,
                "tags": post_data.tags,
                "is_public": post_data.is_public,
                "shared_code_count": len(post_data.shared_code_ids)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        # Prepare response with author info
        response_dict = {
            "id": post.id,
            "user_id": post.user_id,
            "title": post.title,
            "content": post.content,
            "summary": post.summary,
            "tags": post.tags,
            "view_count": post.view_count,
            "like_count": post.like_count,
            "comment_count": post.comment_count,
            "favorite_count": post.favorite_count,
            "is_pinned": post.is_pinned,
            "is_public": post.is_public,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "author_username": current_user.username,
            "author_avatar": current_user.avatar_url,
            "author_full_name": current_user.full_name,
            "is_liked_by_current_user": False,
            "is_favorited_by_current_user": False,
            "shared_codes": []
        }

        return PostResponse(**response_dict)

    except Exception as e:
        # Log failed post creation
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="post_create",
            resource_type="post",
            details={
                "title": post_data.title,
                "error": str(e)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"帖子创建失败: {str(e)}")

@app.get("/community/posts", response_model=dict)
def get_posts(
    query: PostQuery = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get community posts with filtering and pagination"""
    try:
        # Build base query
        db_query = db.query(Post).filter(Post.is_public == True)

        # Apply filters
        if query.author_id:
            db_query = db_query.filter(Post.user_id == query.author_id)

        if query.tag:
            db_query = db_query.filter(Post.tags.like(f"%{query.tag}%"))

        if query.search:
            search_term = f"%{query.search}%"
            db_query = db_query.filter(
                (Post.title.like(search_term)) |
                (Post.content.like(search_term)) |
                (Post.summary.like(search_term))
            )

        if query.is_pinned is not None:
            db_query = db_query.filter(Post.is_pinned == query.is_pinned)

        # Apply sorting
        if query.sort_by == "latest":
            db_query = db_query.order_by(Post.is_pinned.desc(), Post.created_at.desc())
        elif query.sort_by == "popular":
            db_query = db_query.order_by(Post.is_pinned.desc(), Post.view_count.desc())
        elif query.sort_by == "most_liked":
            db_query = db_query.order_by(Post.is_pinned.desc(), Post.like_count.desc())
        elif query.sort_by == "most_commented":
            db_query = db_query.order_by(Post.is_pinned.desc(), Post.comment_count.desc())
        else:
            db_query = db_query.order_by(Post.is_pinned.desc(), Post.created_at.desc())

        # Count total posts
        total_count = db_query.count()

        # Apply pagination
        page = max(1, query.page)
        page_size = min(50, max(1, query.page_size))
        offset = (page - 1) * page_size

        posts = db_query.offset(offset).limit(page_size).all()

        # Get user's interaction status for each post
        post_ids = [post.id for post in posts]
        user_likes = {}
        user_favorites = {}

        if post_ids:
            # Get user's likes
            user_like_records = db.query(PostLike).filter(
                PostLike.user_id == current_user.id,
                PostLike.post_id.in_(post_ids)
            ).all()
            user_likes = {like.post_id: True for like in user_like_records}

            # Get user's favorites
            user_favorite_records = db.query(PostFavorite).filter(
                PostFavorite.user_id == current_user.id,
                PostFavorite.post_id.in_(post_ids)
            ).all()
            user_favorites = {favorite.post_id: True for favorite in user_favorite_records}

        # Prepare response
        post_responses = []
        for post in posts:
            # Get author info
            author = db.query(User).filter(User.id == post.user_id).first()

            # Get shared codes
            shared_codes = []
            post_code_shares = db.query(PostCodeShare).filter(PostCodeShare.post_id == post.id).all()
            for share in post_code_shares:
                code = db.query(CodeLibrary).filter(CodeLibrary.id == share.code_library_id).first()
                if code:
                    shared_codes.append({
                        "id": code.id,
                        "title": code.title,
                        "description": code.description,
                        "language": code.language,
                        "tags": code.tags,
                        "author_id": code.user_id,
                        "author_username": author.username if author else "unknown",
                        "is_public": code.is_public
                    })

            response_dict = {
                "id": post.id,
                "user_id": post.user_id,
                "title": post.title,
                "content": post.content,
                "summary": post.summary,
                "tags": post.tags,
                "view_count": post.view_count,
                "like_count": post.like_count,
                "comment_count": post.comment_count,
                "favorite_count": post.favorite_count,
                "is_pinned": post.is_pinned,
                "is_public": post.is_public,
                "created_at": post.created_at,
                "updated_at": post.updated_at,
                "author_username": author.username if author else "unknown",
                "author_avatar": author.avatar_url if author else None,
                "author_full_name": author.full_name if author else None,
                "is_liked_by_current_user": user_likes.get(post.id, False),
                "is_favorited_by_current_user": user_favorites.get(post.id, False),
                "shared_codes": shared_codes
            }
            post_responses.append(PostResponse(**response_dict))

        return {
            "posts": post_responses,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取帖子列表失败: {str(e)}")

@app.get("/community/posts/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific post by ID"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子未找到")

    # Check if post is public or belongs to current user
    if not post.is_public and post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此帖子")

    # Increment view count
    post.view_count += 1
    db.commit()

    # Get author info
    author = db.query(User).filter(User.id == post.user_id).first()

    # Get user's interaction status
    is_liked = db.query(PostLike).filter(
        PostLike.user_id == current_user.id,
        PostLike.post_id == post_id
    ).first() is not None

    is_favorited = db.query(PostFavorite).filter(
        PostFavorite.user_id == current_user.id,
        PostFavorite.post_id == post_id
    ).first() is not None

    # Get shared codes
    shared_codes = []
    post_code_shares = db.query(PostCodeShare).filter(PostCodeShare.post_id == post_id).all()
    for share in post_code_shares:
        code = db.query(CodeLibrary).filter(CodeLibrary.id == share.code_library_id).first()
        if code and (code.user_id == current_user.id or code.is_public):
            shared_codes.append({
                "id": code.id,
                "title": code.title,
                "description": code.description,
                "language": code.language,
                "tags": code.tags,
                "author_id": code.user_id,
                "author_username": author.username if author else "unknown",
                "is_public": code.is_public
            })

    response_dict = {
        "id": post.id,
        "user_id": post.user_id,
        "title": post.title,
        "content": post.content,
        "summary": post.summary,
        "tags": post.tags,
        "view_count": post.view_count,
        "like_count": post.like_count,
        "comment_count": post.comment_count,
        "favorite_count": post.favorite_count,
        "is_pinned": post.is_pinned,
        "is_public": post.is_public,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "author_username": author.username if author else "unknown",
        "author_avatar": author.avatar_url if author else None,
        "author_full_name": author.full_name if author else None,
        "is_liked_by_current_user": is_liked,
        "is_favorited_by_current_user": is_favorited,
        "shared_codes": shared_codes
    }

    return PostResponse(**response_dict)

@app.post("/community/posts/{post_id}/like")
def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Like or unlike a post"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子未找到")

    # Check if post is public or belongs to current user
    if not post.is_public and post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此帖子")

    # Check if already liked
    existing_like = db.query(PostLike).filter(
        PostLike.user_id == current_user.id,
        PostLike.post_id == post_id
    ).first()

    if existing_like:
        # Unlike
        db.delete(existing_like)
        post.like_count = max(0, post.like_count - 1)
        message = "取消点赞"
        is_liked = False
    else:
        # Like
        like = PostLike(user_id=current_user.id, post_id=post_id)
        db.add(like)
        post.like_count += 1
        message = "点赞成功"
        is_liked = True

    db.commit()

    # Log the interaction
    log_system_event(
        db=db,
        user_id=current_user.id,
        action="post_like" if is_liked else "post_unlike",
        resource_type="post",
        resource_id=post_id,
        details={"post_title": post.title},
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        status="success"
    )

    return {"message": message, "is_liked": is_liked, "like_count": post.like_count}

@app.post("/community/posts/{post_id}/favorite")
def favorite_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Favorite or unfavorite a post"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子未找到")

    # Check if post is public or belongs to current user
    if not post.is_public and post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此帖子")

    # Check if already favorited
    existing_favorite = db.query(PostFavorite).filter(
        PostFavorite.user_id == current_user.id,
        PostFavorite.post_id == post_id
    ).first()

    if existing_favorite:
        # Unfavorite
        db.delete(existing_favorite)
        post.favorite_count = max(0, post.favorite_count - 1)
        message = "取消收藏"
        is_favorited = False
    else:
        # Favorite
        favorite = PostFavorite(user_id=current_user.id, post_id=post_id)
        db.add(favorite)
        post.favorite_count += 1
        message = "收藏成功"
        is_favorited = True

    db.commit()

    # Log the interaction
    log_system_event(
        db=db,
        user_id=current_user.id,
        action="post_favorite" if is_favorited else "post_unfavorite",
        resource_type="post",
        resource_id=post_id,
        details={"post_title": post.title},
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        status="success"
    )

    return {"message": message, "is_favorited": is_favorited, "favorite_count": post.favorite_count}

@app.post("/community/posts/{post_id}/comments", response_model=CommentResponse)
def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Create a comment on a post"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子未找到")

    # Check if post is public or belongs to current user
    if not post.is_public and post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此帖子")

    # If replying to a comment, check if parent comment exists
    if comment_data.parent_id:
        parent_comment = db.query(Comment).filter(Comment.id == comment_data.parent_id).first()
        if not parent_comment or parent_comment.post_id != post_id:
            raise HTTPException(status_code=404, detail="父评论未找到")

    # Create comment
    comment = Comment(
        user_id=current_user.id,
        post_id=post_id,
        parent_id=comment_data.parent_id,
        content=comment_data.content
    )

    db.add(comment)

    # Update post comment count
    post.comment_count += 1

    db.commit()
    db.refresh(comment)

    # Log comment creation
    log_system_event(
        db=db,
        user_id=current_user.id,
        action="comment_create",
        resource_type="comment",
        resource_id=comment.id,
        details={
            "post_id": post_id,
            "parent_id": comment_data.parent_id,
            "content_length": len(comment_data.content)
        },
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        status="success"
    )

    # Prepare response
    response_dict = {
        "id": comment.id,
        "user_id": comment.user_id,
        "post_id": comment.post_id,
        "parent_id": comment.parent_id,
        "content": comment.content,
        "like_count": comment.like_count,
        "is_deleted": comment.is_deleted,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
        "author_username": current_user.username,
        "author_avatar": current_user.avatar_url,
        "author_full_name": current_user.full_name,
        "is_liked_by_current_user": False,
        "replies": []
    }

    return CommentResponse(**response_dict)

@app.get("/community/posts/{post_id}/comments", response_model=dict)
def get_comments(
    post_id: int,
    query: CommentQuery = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comments for a post"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子未找到")

    # Check if post is public or belongs to current user
    if not post.is_public and post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此帖子")

    try:
        # Get top-level comments (no parent)
        db_query = db.query(Comment).filter(
            Comment.post_id == post_id,
            Comment.parent_id.is_(None),
            Comment.is_deleted == False
        )

        # Apply sorting
        if query.sort_by == "latest":
            db_query = db_query.order_by(Comment.created_at.desc())
        elif query.sort_by == "most_liked":
            db_query = db_query.order_by(Comment.like_count.desc())
        else:
            db_query = db_query.order_by(Comment.created_at.desc())

        # Apply pagination
        page = max(1, query.page)
        page_size = min(50, max(1, query.page_size))
        offset = (page - 1) * page_size

        comments = db_query.offset(offset).limit(page_size).all()

        # Get user's like status for each comment
        comment_ids = [comment.id for comment in comments]
        user_likes = {}

        if comment_ids:
            user_like_records = db.query(CommentLike).filter(
                CommentLike.user_id == current_user.id,
                CommentLike.comment_id.in_(comment_ids)
            ).all()
            user_likes = {like.comment_id: True for like in user_like_records}

        # Prepare response
        comment_responses = []
        for comment in comments:
            # Get author info
            author = db.query(User).filter(User.id == comment.user_id).first()

            # Get replies
            replies = []
            reply_records = db.query(Comment).filter(
                Comment.parent_id == comment.id,
                Comment.is_deleted == False
            ).order_by(Comment.created_at.asc()).all()

            for reply in reply_records:
                reply_author = db.query(User).filter(User.id == reply.user_id).first()
                reply_response_dict = {
                    "id": reply.id,
                    "user_id": reply.user_id,
                    "post_id": reply.post_id,
                    "parent_id": reply.parent_id,
                    "content": reply.content,
                    "like_count": reply.like_count,
                    "is_deleted": reply.is_deleted,
                    "created_at": reply.created_at,
                    "updated_at": reply.updated_at,
                    "author_username": reply_author.username if reply_author else "unknown",
                    "author_avatar": reply_author.avatar_url if reply_author else None,
                    "author_full_name": reply_author.full_name if reply_author else None,
                    "is_liked_by_current_user": False,
                    "replies": []
                }
                replies.append(CommentResponse(**reply_response_dict))

            response_dict = {
                "id": comment.id,
                "user_id": comment.user_id,
                "post_id": comment.post_id,
                "parent_id": comment.parent_id,
                "content": comment.content,
                "like_count": comment.like_count,
                "is_deleted": comment.is_deleted,
                "created_at": comment.created_at,
                "updated_at": comment.updated_at,
                "author_username": author.username if author else "unknown",
                "author_avatar": author.avatar_url if author else None,
                "author_full_name": author.full_name if author else None,
                "is_liked_by_current_user": user_likes.get(comment.id, False),
                "replies": replies
            }
            comment_responses.append(CommentResponse(**response_dict))

        return {
            "comments": comment_responses,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_count": db_query.count(),
                "total_pages": (db_query.count() + page_size - 1) // page_size
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取评论失败: {str(e)}")

@app.post("/community/comments/{comment_id}/like")
def like_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Like or unlike a comment"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="评论未找到")

    # Check if user can access the post
    post = db.query(Post).filter(Post.id == comment.post_id).first()
    if not post or (not post.is_public and post.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="无权访问此评论")

    # Check if already liked
    existing_like = db.query(CommentLike).filter(
        CommentLike.user_id == current_user.id,
        CommentLike.comment_id == comment_id
    ).first()

    if existing_like:
        # Unlike
        db.delete(existing_like)
        comment.like_count = max(0, comment.like_count - 1)
        message = "取消点赞"
        is_liked = False
    else:
        # Like
        like = CommentLike(user_id=current_user.id, comment_id=comment_id)
        db.add(like)
        comment.like_count += 1
        message = "点赞成功"
        is_liked = True

    db.commit()

    # Log the interaction
    log_system_event(
        db=db,
        user_id=current_user.id,
        action="comment_like" if is_liked else "comment_unlike",
        resource_type="comment",
        resource_id=comment_id,
        details={"post_id": comment.post_id},
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        status="success"
    )

    return {"message": message, "is_liked": is_liked, "like_count": comment.like_count}

@app.post("/community/follow/{user_id}", response_model=FollowResponse)
def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Follow or unfollow a user"""
    # Cannot follow yourself
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能关注自己")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户未找到")

    # Check if already following
    existing_follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()

    if existing_follow:
        # Unfollow
        db.delete(existing_follow)
        message = "取消关注"
        is_following = False
    else:
        # Follow
        follow = Follow(follower_id=current_user.id, following_id=user_id)
        db.add(follow)
        message = "关注成功"
        is_following = True

    db.commit()

    # Log the interaction
    log_system_event(
        db=db,
        user_id=current_user.id,
        action="user_follow" if is_following else "user_unfollow",
        resource_type="user",
        resource_id=user_id,
        details={"target_username": target_user.username},
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        status="success"
    )

    response_dict = {
        "id": 0,  # Placeholder
        "follower_id": current_user.id,
        "following_id": user_id,
        "created_at": datetime.utcnow(),
        "following_username": target_user.username,
        "following_avatar": target_user.avatar_url,
        "following_full_name": target_user.full_name,
        "is_following": is_following
    }

    return FollowResponse(**response_dict)

# Enhanced User Profile Stats
@app.get("/profile/enhanced-stats", response_model=UserStatsResponse)
def get_user_enhanced_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get enhanced user profile statistics for profile page"""

    # Basic counts
    code_library_count = db.query(CodeLibrary).filter(CodeLibrary.user_id == current_user.id).count()
    posts_count = db.query(Post).filter(Post.user_id == current_user.id).count()
    followers_count = db.query(Follow).filter(Follow.following_id == current_user.id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == current_user.id).count()

    # Calculate total stats from user's posts
    user_posts = db.query(Post).filter(Post.user_id == current_user.id).all()
    total_likes = sum(post.like_count for post in user_posts)
    total_favorites = sum(post.favorite_count for post in user_posts)
    total_views = sum(post.view_count for post in user_posts)

    # Recent posts (last 5)
    recent_posts = db.query(Post).filter(Post.user_id == current_user.id).order_by(Post.created_at.desc()).limit(5).all()

    # Recent codes (last 5)
    recent_codes = db.query(CodeLibrary).filter(CodeLibrary.user_id == current_user.id).order_by(CodeLibrary.created_at.desc()).limit(5).all()

    # Favorite posts (last 5)
    favorite_post_ids = db.query(PostFavorite.post_id).filter(PostFavorite.user_id == current_user.id).all()
    favorite_posts = db.query(Post).filter(Post.id.in_([fp[0] for fp in favorite_post_ids])).order_by(Post.created_at.desc()).limit(5).all()

    # Liked posts (last 5)
    liked_post_ids = db.query(PostLike.post_id).filter(PostLike.user_id == current_user.id).all()
    liked_posts = db.query(Post).filter(Post.id.in_([lp[0] for lp in liked_post_ids])).order_by(Post.created_at.desc()).limit(5).all()

    return UserStatsResponse(
        code_library_count=code_library_count,
        posts_count=posts_count,
        followers_count=followers_count,
        following_count=following_count,
        total_likes=total_likes,
        total_favorites=total_favorites,
        total_views=total_views,
        recent_posts=[PostResponse.model_validate(post) for post in recent_posts],
        recent_codes=[CodeLibraryResponse.model_validate(code) for code in recent_codes],
        favorite_posts=[PostResponse.model_validate(post) for post in favorite_posts],
        liked_posts=[PostResponse.model_validate(post) for post in liked_posts]
    )

# Code Library Save/Copy functionality
@app.post("/code-library/save", response_model=CodeLibrarySaveResponse)
def save_code_to_library(
    save_request: CodeLibrarySaveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save a shared code to user's own library"""

    # Get the source code
    source_code = db.query(CodeLibrary).filter(CodeLibrary.id == save_request.source_code_id).first()
    if not source_code:
        raise HTTPException(status_code=404, detail="Source code not found")

    # Check if the code is accessible (either public or shared via post)
    if not source_code.is_public and not source_code.is_shared_via_post:
        raise HTTPException(status_code=403, detail="This code is not accessible for saving")

    # Create a copy in user's library
    new_code = CodeLibrary(
        user_id=current_user.id,
        title=save_request.title or f"[Copy] {source_code.title}",
        description=save_request.description or source_code.description,
        code=source_code.code,
        language=source_code.language,
        is_public=False,  # Saved codes are private by default
        tags=source_code.tags,
        conda_env=save_request.conda_env
    )

    db.add(new_code)
    db.commit()
    db.refresh(new_code)

    return CodeLibrarySaveResponse(
        id=new_code.id,
        title=new_code.title,
        message="Code saved to your library successfully"
    )

# Get available environments for code saving
@app.get("/environments/available")
def get_available_environments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all available environments for the current user"""

    # User's own environments
    user_envs = db.query(UserEnvironment).filter(
        UserEnvironment.user_id == current_user.id,
        UserEnvironment.is_active == True
    ).all()

    # Public environments from other users
    public_envs = db.query(UserEnvironment).filter(
        UserEnvironment.is_public == True,
        UserEnvironment.is_active == True,
        UserEnvironment.user_id != current_user.id
    ).all()

    # Always include base environment
    environments = [{"name": "base", "display_name": "Base Environment", "is_default": True}]

    # Add user environments
    for env in user_envs:
        environments.append({
            "name": env.env_name,
            "display_name": env.display_name,
            "is_default": False
        })

    # Add public environments
    for env in public_envs:
        environments.append({
            "name": env.env_name,
            "display_name": f"{env.display_name} (by {env.user_id})",
            "is_default": False
        })

    return {"environments": environments}

# Delete Post API
@app.delete("/community/posts/{post_id}")
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Delete a community post and hide related shared codes"""
    try:
        # Get the post
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        # Check if user is the author or admin
        if post.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="无权删除此帖子")

        # Get all shared codes for this post
        shared_codes = db.query(CodeLibrary).join(PostCodeShare).filter(
            PostCodeShare.post_id == post_id
        ).all()

        # Hide codes that were made public through this post
        for code in shared_codes:
            if code.is_shared_via_post and code.shared_post_id == post_id:
                code.is_public = False
                code.is_shared_via_post = False
                code.shared_post_id = None

        # Delete post code shares
        db.query(PostCodeShare).filter(PostCodeShare.post_id == post_id).delete()

        # Delete post comments
        db.query(Comment).filter(Comment.post_id == post_id).delete()

        # Delete post likes and favorites
        db.query(PostLike).filter(PostLike.post_id == post_id).delete()
        db.query(PostFavorite).filter(PostFavorite.post_id == post_id).delete()

        # Delete the post
        db.delete(post)
        db.commit()

        # Log post deletion
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="post_delete",
            resource_type="post",
            resource_id=post_id,
            details={
                "title": post.title,
                "hidden_codes_count": len(shared_codes)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        return {"message": "帖子删除成功，相关代码已设为私密"}
    except HTTPException:
        raise
    except Exception as e:
        # Log failed post deletion
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="post_delete",
            resource_type="post",
            resource_id=post_id,
            details={
                "error": str(e)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"帖子删除失败: {str(e)}")

# Follow/Followers List endpoints
@app.get("/users/{user_id}/followers", response_model=dict)
def get_user_followers(
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """Get user's followers list"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")

    # Get followers with user info
    followers_query = db.query(
        User.id,
        User.username,
        User.full_name,
        User.avatar_url,
        Follow.created_at
    ).join(
        Follow, User.id == Follow.follower_id
    ).filter(
        Follow.following_id == user_id
    ).order_by(
        Follow.created_at.desc()
    )

    total_count = followers_query.count()
    followers = followers_query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "followers": [
            {
                "id": follower.id,
                "username": follower.username,
                "full_name": follower.full_name,
                "avatar_url": follower.avatar_url,
                "followed_at": follower.created_at
            }
            for follower in followers
        ],
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }

@app.get("/users/{user_id}/following", response_model=dict)
def get_user_following(
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """Get user's following list"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")

    # Get following with user info
    following_query = db.query(
        User.id,
        User.username,
        User.full_name,
        User.avatar_url,
        Follow.created_at
    ).join(
        Follow, User.id == Follow.following_id
    ).filter(
        Follow.follower_id == user_id
    ).order_by(
        Follow.created_at.desc()
    )

    total_count = following_query.count()
    following = following_query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "following": [
            {
                "id": following_user.id,
                "username": following_user.username,
                "full_name": following_user.full_name,
                "avatar_url": following_user.avatar_url,
                "followed_at": following_user.created_at
            }
            for following_user in following
        ],
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }

@app.get("/users/{user_id}/follow-status", response_model=dict)
def get_follow_status(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get follow status between current user and target user"""
    if user_id == current_user.id:
        return {"is_following": False, "is_self": True}

    is_following = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first() is not None

    return {"is_following": is_following, "is_self": False}

@app.get("/users/by-username/{username}")
def get_user_by_username(
    username: str,
    db: Session = Depends(get_db)
):
    """Get user by username"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")

    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "location": user.location,
        "company": user.company,
        "github_username": user.github_username,
        "website": user.website,
        "created_at": user.created_at
    }

@app.get("/users/{user_id}/posts", response_model=dict)
def get_user_posts(
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    """Get public posts by a specific user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")

    # Count total posts
    total_count = db.query(Post).filter(
        Post.user_id == user_id,
        Post.is_public == True
    ).count()

    # Get paginated posts
    posts = db.query(Post).filter(
        Post.user_id == user_id,
        Post.is_public == True
    ).order_by(Post.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "posts": [
            {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "summary": post.content[:200] + "..." if len(post.content) > 200 else post.content,
                "code_snippet": post.code_snippet,
                "language": post.language,
                "tags": post.tags,
                "view_count": post.view_count,
                "like_count": post.like_count,
                "comment_count": len(db.query(Comment).filter(Comment.post_id == post.id).all()),
                "created_at": post.created_at,
                "updated_at": post.updated_at
            }
            for post in posts
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }

@app.get("/users/{user_id}/code-library", response_model=dict)
def get_user_code_library(
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    """Get public code library entries by a specific user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")

    # Count total public code entries
    total_count = db.query(CodeLibrary).filter(
        CodeLibrary.user_id == user_id,
        CodeLibrary.is_public == True
    ).count()

    # Get paginated code library entries
    codes = db.query(CodeLibrary).filter(
        CodeLibrary.user_id == user_id,
        CodeLibrary.is_public == True
    ).order_by(CodeLibrary.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "codes": [
            {
                "id": code.id,
                "title": code.title,
                "description": code.description,
                "language": code.language,
                "tags": code.tags,
                "conda_env": code.conda_env,
                "created_at": code.created_at,
                "updated_at": code.updated_at
            }
            for code in codes
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }

@app.get("/users/{user_id}/stats", response_model=dict)
def get_user_public_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get public statistics for a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")

    # Count posts
    posts_count = db.query(Post).filter(
        Post.user_id == user_id,
        Post.is_public == True
    ).count()

    # Count public code library entries
    code_library_count = db.query(CodeLibrary).filter(
        CodeLibrary.user_id == user_id,
        CodeLibrary.is_public == True
    ).count()

    # Count followers and following
    followers_count = db.query(Follow).filter(Follow.following_id == user_id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == user_id).count()

    # Get recent posts
    recent_posts = db.query(Post).filter(
        Post.user_id == user_id,
        Post.is_public == True
    ).order_by(Post.created_at.desc()).limit(5).all()

    # Get recent code library entries
    recent_codes = db.query(CodeLibrary).filter(
        CodeLibrary.user_id == user_id,
        CodeLibrary.is_public == True
    ).order_by(CodeLibrary.created_at.desc()).limit(5).all()

    return {
        "posts_count": posts_count,
        "code_library_count": code_library_count,
        "followers_count": followers_count,
        "following_count": following_count,
        "recent_posts": [
            {
                "id": post.id,
                "title": post.title,
                "summary": post.content[:200] + "..." if len(post.content) > 200 else post.content,
                "like_count": post.like_count,
                "comment_count": len(db.query(Comment).filter(Comment.post_id == post.id).all()),
                "view_count": post.view_count,
                "created_at": post.created_at
            }
            for post in recent_posts
        ],
        "recent_codes": [
            {
                "id": code.id,
                "title": code.title,
                "description": code.description,
                "language": code.language,
                "conda_env": code.conda_env,
                "created_at": code.created_at
            }
            for code in recent_codes
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)