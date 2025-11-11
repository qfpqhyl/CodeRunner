"""Admin routes (logs, database management)."""
import os
import json
import shutil
import zipfile
import tempfile
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from database import get_db, User, SystemLog, CodeExecution, CodeLibrary, APIKey, AIConfig, UserEnvironment, Post, Comment, Follow
from models import SystemLogResponse, UserLogQuery
from auth import get_current_admin_user
from utils import get_client_info, log_system_event

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/logs")
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


@router.get("/logs/stats")
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


@router.get("/logs/actions")
def get_log_actions(current_user: User = Depends(get_current_admin_user)):
    """Get all available log actions for filtering"""
    db = next(get_db())
    try:
        actions = db.query(SystemLog.action).distinct().all()
        return [action[0] for action in actions if action[0]]
    finally:
        db.close()


@router.get("/logs/resource-types")
def get_log_resource_types(current_user: User = Depends(get_current_admin_user)):
    """Get all available resource types for filtering"""
    db = next(get_db())
    try:
        resource_types = db.query(SystemLog.resource_type).distinct().all()
        return [rt[0] for rt in resource_types if rt[0]]
    finally:
        db.close()

# AI Configuration endpoints

@router.post("/database/export")
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


@router.post("/database/import")
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


@router.get("/database/info")
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

