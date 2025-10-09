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