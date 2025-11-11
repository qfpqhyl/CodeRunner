"""Code execution routes."""
import subprocess
import tempfile
import os
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db, User, CodeExecution
from models import CodeExecutionRequest, CodeExecutionResponse
from auth import get_current_user, get_current_admin_user
from user_levels import get_user_level_config, can_user_execute, get_daily_execution_count
from utils import log_system_event, get_client_info

router = APIRouter(tags=["execution"])


@router.post("/execute", response_model=CodeExecutionResponse)
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


@router.get("/executions", response_model=list[CodeExecutionResponse])
def get_executions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    return db.query(CodeExecution).filter(CodeExecution.user_id == current_user.id).order_by(CodeExecution.created_at.desc()).limit(limit).all()


@router.get("/admin/executions", response_model=list[CodeExecutionResponse])
def get_all_executions(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    limit: int = 100
):
    return db.query(CodeExecution).order_by(CodeExecution.created_at.desc()).limit(limit).all()
