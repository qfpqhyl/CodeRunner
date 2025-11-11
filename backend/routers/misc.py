"""Miscellaneous routes (root, user stats, etc)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.database import get_db, User, CodeExecution, CodeLibrary, APIKey
from models.models import UserResponse
from services.auth import get_current_user
from models.user_levels import get_user_level_config, get_daily_execution_count, get_daily_api_call_count, USER_LEVELS

router = APIRouter(tags=["misc"])


@router.get("/")
def read_root():
    return {"message": "Welcome to CodeRunner API"}

# System Logs endpoints (Admin only)

@router.get("/user-levels", response_model=dict)
def get_user_levels():
    """Get all user level configurations"""
    return USER_LEVELS


@router.get("/user-stats")
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

