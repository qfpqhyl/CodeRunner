"""AI configuration and code generation routes."""
import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db, User, AIConfig
from models.models import AIConfigCreate, AIConfigUpdate, AIConfigResponse, AICodeGenerateRequest, AICodeGenerateResponse
from services.auth import get_current_user
from utils.utils import get_client_info, log_system_event

router = APIRouter(tags=["ai"])


@router.post("/ai-configs", response_model=AIConfigResponse)
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


@router.get("/ai-configs", response_model=list[AIConfigResponse])
def get_ai_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all AI configurations for the current user"""
    return db.query(AIConfig).filter(AIConfig.user_id == current_user.id).all()


@router.put("/ai-configs/{config_id}", response_model=AIConfigResponse)
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


@router.delete("/ai-configs/{config_id}")
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


@router.post("/ai/generate-code", response_model=AICodeGenerateResponse)
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

