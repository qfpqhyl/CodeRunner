"""User profile management routes."""
import os
import uuid
import shutil
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db, User, SystemLog, CodeExecution, Post, Comment, Follow
from models import UserProfileUpdate, UserProfileResponse, SystemLogResponse, UserLogQuery, UserStatsResponse
from auth import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])

# Avatar storage directory
AVATAR_DIR = "data/avatars"
os.makedirs(AVATAR_DIR, exist_ok=True)


@router.get("/profile", response_model=UserProfileResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile information"""
    return current_user


@router.put("/profile", response_model=UserProfileResponse)
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


@router.post("/profile/upload-avatar")
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


@router.get("/api/avatars/{filename}")
def get_avatar(filename: str):
    """Serve avatar images"""
    from fastapi.responses import FileResponse
    import os

    file_path = os.path.join("data/avatars", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="头像文件未找到")

    return FileResponse(file_path, media_type="image/jpeg")


@router.delete("/profile/avatar")
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

@router.get("/profile/logs", response_model=dict)
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


@router.get("/profile/logs/actions")
def get_user_log_actions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get available log actions for the current user"""
    actions = db.query(SystemLog.action).filter(
        SystemLog.user_id == current_user.id
    ).distinct().all()
    return [action[0] for action in actions if action[0]]


@router.get("/profile/logs/resource-types")
def get_user_log_resource_types(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get available resource types for the current user"""
    resource_types = db.query(SystemLog.resource_type).filter(
        SystemLog.user_id == current_user.id
    ).distinct().all()
    return [rt[0] for rt in resource_types if rt[0]]


@router.get("/profile/stats")
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

@router.get("/profile/enhanced-stats", response_model=UserStatsResponse)
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

