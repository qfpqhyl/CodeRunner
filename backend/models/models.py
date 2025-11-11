from pydantic import BaseModel, EmailStr
from typing import Optional, Union
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
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    github_username: Optional[str] = None
    company: Optional[str] = None
    updated_at: datetime

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
    conda_env: Optional[str] = "base"

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
    conda_env: Optional[str] = "base"

class CodeLibraryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    language: Optional[str] = None
    is_public: Optional[bool] = None
    tags: Optional[str] = None
    conda_env: Optional[str] = None

class CodeLibraryResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    code: str
    language: str
    is_public: bool
    tags: Optional[str] = None
    conda_env: str
    is_shared_via_post: bool
    shared_post_id: Optional[int] = None
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

# User Environment Models
class UserEnvironmentCreate(BaseModel):
    env_name: str
    display_name: str
    description: Optional[str] = None
    python_version: Optional[str] = "3.11"
    is_public: Optional[bool] = False
    packages: Optional[list[str]] = []  # List of packages to install

class UserEnvironmentUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None

class UserEnvironmentResponse(BaseModel):
    id: int
    user_id: int
    env_name: str
    display_name: str
    description: Optional[str] = None
    python_version: str
    is_active: bool
    is_public: bool
    created_at: datetime
    updated_at: datetime
    last_used: Optional[datetime] = None
    owner_name: Optional[str] = None  # Username of environment owner

    class Config:
        from_attributes = True

class EnvironmentInfo(BaseModel):
    name: str
    python_version: str
    python_path: str
    site_packages_path: str
    package_count: int
    is_base: bool
    environment_type: str
    is_owner: bool
    is_public: bool
    display_name: Optional[str] = None
    description: Optional[str] = None

class PackageInfo(BaseModel):
    name: str
    version: str
    latest_version: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None

class PackageInstallRequest(BaseModel):
    package_name: str

class PackageInstallResponse(BaseModel):
    message: str

# User Profile Models
class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    github_username: Optional[str] = None
    company: Optional[str] = None

class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    github_username: Optional[str] = None
    company: Optional[str] = None
    is_active: bool
    is_admin: bool
    user_level: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# System Log Models for User Profile
class SystemLogResponse(BaseModel):
    id: int
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    details: Optional[Union[str, dict]] = None
    ip_address: str
    user_agent: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogQuery(BaseModel):
    action: Optional[str] = None
    resource_type: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: Optional[int] = 1
    page_size: Optional[int] = 20

# Community Models
class PostCreate(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    tags: Optional[str] = None
    is_public: Optional[bool] = True
    shared_code_ids: Optional[list[int]] = []  # List of code library IDs to share

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[str] = None
    is_public: Optional[bool] = None

class PostResponse(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    summary: Optional[str] = None
    tags: Optional[str] = None
    view_count: int
    like_count: int
    comment_count: int
    favorite_count: int
    is_pinned: bool
    is_public: bool
    created_at: datetime
    updated_at: datetime

    # Additional fields for response
    author_username: Optional[str] = None
    author_avatar: Optional[str] = None
    author_full_name: Optional[str] = None
    is_liked_by_current_user: Optional[bool] = False
    is_favorited_by_current_user: Optional[bool] = False
    shared_codes: Optional[list[dict]] = []

    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None

class CommentUpdate(BaseModel):
    content: Optional[str] = None

class CommentResponse(BaseModel):
    id: int
    user_id: int
    post_id: int
    parent_id: Optional[int] = None
    content: str
    like_count: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    # Additional fields for response
    author_username: Optional[str] = None
    author_avatar: Optional[str] = None
    author_full_name: Optional[str] = None
    is_liked_by_current_user: Optional[bool] = False
    replies: Optional[list["CommentResponse"]] = []

    class Config:
        from_attributes = True

class PostQuery(BaseModel):
    page: Optional[int] = 1
    page_size: Optional[int] = 20
    author_id: Optional[int] = None
    tag: Optional[str] = None
    search: Optional[str] = None
    sort_by: Optional[str] = "latest"  # latest, popular, most_liked, most_commented
    is_pinned: Optional[bool] = None

class CommentQuery(BaseModel):
    page: Optional[int] = 1
    page_size: Optional[int] = 20
    sort_by: Optional[str] = "latest"  # latest, most_liked

class FollowCreate(BaseModel):
    following_id: int

class FollowResponse(BaseModel):
    id: int
    follower_id: int
    following_id: int
    created_at: datetime

    # Additional fields
    following_username: Optional[str] = None
    following_avatar: Optional[str] = None
    following_full_name: Optional[str] = None
    is_following: Optional[bool] = True

    class Config:
        from_attributes = True

# User Stats Models
class UserStatsResponse(BaseModel):
    # Basic stats
    code_library_count: int
    posts_count: int
    followers_count: int
    following_count: int
    total_likes: int
    total_favorites: int
    total_views: int

    # Recent activity
    recent_posts: list[PostResponse] = []
    recent_codes: list[CodeLibraryResponse] = []
    favorite_posts: list[PostResponse] = []
    liked_posts: list[PostResponse] = []

    class Config:
        from_attributes = True

# Code Library Save/Copy Models
class CodeLibrarySaveRequest(BaseModel):
    source_code_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    conda_env: Optional[str] = "base"

class CodeLibrarySaveResponse(BaseModel):
    id: int
    title: str
    message: str

    class Config:
        from_attributes = True