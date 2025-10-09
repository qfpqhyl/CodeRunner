from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    is_admin: Optional[bool] = False
    user_level: Optional[int] = 1

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    user_level: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class CodeExecutionRequest(BaseModel):
    code: str

class CodeExecutionResponse(BaseModel):
    id: int
    result: str
    status: str
    execution_time: int
    memory_usage: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CodeLibraryCreate(BaseModel):
    title: str
    description: Optional[str] = None
    code: str
    language: Optional[str] = "python"
    is_public: Optional[bool] = False
    tags: Optional[str] = None

class CodeLibraryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    language: Optional[str] = None
    is_public: Optional[bool] = None
    tags: Optional[str] = None

class CodeLibraryResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    code: str
    language: str
    is_public: bool
    tags: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class PasswordChangeByAdmin(BaseModel):
    new_password: str

class APIKeyCreate(BaseModel):
    key_name: str
    expires_at: Optional[datetime] = None

class APIKeyResponse(BaseModel):
    id: int
    key_name: str
    key_value: str
    is_active: bool
    last_used: Optional[datetime] = None
    usage_count: int
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class APIKeyInfo(BaseModel):
    id: int
    key_name: str
    is_active: bool
    last_used: Optional[datetime] = None
    usage_count: int
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CodeExecuteByAPIRequest(BaseModel):
    code_id: int
    parameters: Optional[dict] = None  # Optional parameters to pass to the code

class CodeExecuteByAPIResponse(BaseModel):
    id: int
    result: str
    status: str
    execution_time: int
    memory_usage: Optional[int] = None
    created_at: datetime
    code_title: str

    class Config:
        from_attributes = True

# AI Configuration Models
class AIConfigCreate(BaseModel):
    model_config = {"protected_namespaces": ()}

    config_name: str
    provider: Optional[str] = "qwen"
    model_name: Optional[str] = "qwen-plus"
    api_key: str
    base_url: Optional[str] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    is_active: Optional[bool] = True

class AIConfigUpdate(BaseModel):
    model_config = {"protected_namespaces": ()}

    config_name: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_active: Optional[bool] = None

class AIConfigResponse(BaseModel):
    model_config = {"protected_namespaces": (), "from_attributes": True}

    id: int
    user_id: int
    config_name: str
    provider: str
    model_name: str
    api_key: str
    base_url: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class AICodeGenerateRequest(BaseModel):
    prompt: str
    config_id: Optional[int] = None  # Use specific AI config, if not provided use active one
    max_tokens: Optional[int] = 2000
    temperature: Optional[float] = 0.7

class AICodeGenerateResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    generated_code: str
    model_used: str
    tokens_used: Optional[int] = None