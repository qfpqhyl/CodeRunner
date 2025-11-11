"""External API routes (API key authenticated)."""
import subprocess
import tempfile
import os
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db, CodeLibrary, CodeExecution
from models import CodeExecuteByAPIRequest, CodeExecuteByAPIResponse, CodeLibraryResponse
from auth import get_api_key_user
from user_levels import get_user_level_config, can_user_make_api_call

router = APIRouter(prefix="/api/v1", tags=["external-api"])


@router.post("/execute", response_model=CodeExecuteByAPIResponse)
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


@router.get("/codes", response_model=list[CodeLibraryResponse])
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


@router.get("/codes/{code_id}", response_model=CodeLibraryResponse)
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
