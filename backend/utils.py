"""Utility functions for the CodeRunner backend."""
import json
from fastapi import Request
from sqlalchemy.orm import Session
from database import SystemLog


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
