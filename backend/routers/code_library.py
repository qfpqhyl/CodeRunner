"""Code library management routes."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db, User, CodeLibrary
from models.models import CodeLibraryCreate, CodeLibraryUpdate, CodeLibraryResponse, CodeLibrarySaveRequest, CodeLibrarySaveResponse
from services.auth import get_current_user
from models.user_levels import get_user_level_config

router = APIRouter(prefix="/code-library", tags=["code-library"])


@router.post("/", response_model=CodeLibraryResponse)
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


@router.get("/", response_model=list[CodeLibraryResponse])
def get_user_code_library(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0
):
    """Get user's code library"""
    return db.query(CodeLibrary).filter(CodeLibrary.user_id == current_user.id).order_by(CodeLibrary.updated_at.desc()).offset(offset).limit(limit).all()


@router.get("/{code_id}", response_model=CodeLibraryResponse)
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


@router.put("/{code_id}", response_model=CodeLibraryResponse)
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


@router.delete("/{code_id}")
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


@router.post("/save", response_model=CodeLibrarySaveResponse)
def save_shared_code_to_library(
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
