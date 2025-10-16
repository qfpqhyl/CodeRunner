from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./coderunner.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    user_level = Column(Integer, default=1)  # 1: Free, 2: Basic, 3: Premium, 4: Enterprise
    created_at = Column(DateTime, default=datetime.utcnow)

    # Profile fields
    avatar_url = Column(String, nullable=True)  # Profile avatar URL
    bio = Column(Text, nullable=True)  # Personal biography
    location = Column(String, nullable=True)  # User location
    website = Column(String, nullable=True)  # Personal website
    github_username = Column(String, nullable=True)  # GitHub username
    company = Column(String, nullable=True)  # Company/organization
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CodeExecution(Base):
    __tablename__ = "code_executions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    code = Column(Text)
    result = Column(Text)
    status = Column(String)  # "success", "error", "running", "timeout", "memory_exceeded"
    created_at = Column(DateTime, default=datetime.utcnow)
    execution_time = Column(Integer)  # in milliseconds
    memory_usage = Column(Integer)  # in MB
    is_api_call = Column(Boolean, default=False)  # Track if this was an API call
    code_library_id = Column(Integer, nullable=True)  # Reference to code library if applicable

class CodeLibrary(Base):
    __tablename__ = "code_library"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    code = Column(Text)
    language = Column(String, default="python")
    is_public = Column(Boolean, default=False)
    tags = Column(String)  # Comma-separated tags
    conda_env = Column(String, default="base")  # Conda environment name
    is_shared_via_post = Column(Boolean, default=False)  # Track if this code is shared via a post
    shared_post_id = Column(Integer, nullable=True)  # Reference to the post that shares this code
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    key_name = Column(String, index=True)
    key_value = Column(String, unique=True, index=True)  # The actual API key
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration date

class AIConfig(Base):
    __tablename__ = "ai_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    config_name = Column(String, index=True)
    provider = Column(String, default="qwen")  # qwen, openai, etc.
    model_name = Column(String, default="qwen-plus")
    api_key = Column(String)
    base_url = Column(String, default="https://dashscope.aliyuncs.com/compatible-mode/v1")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserEnvironment(Base):
    __tablename__ = "user_environments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    env_name = Column(String, unique=True, index=True)  # Must be unique across all users
    display_name = Column(String)  # User-friendly name for the environment
    description = Column(Text, nullable=True)
    python_version = Column(String, default="3.11")
    conda_yaml = Column(Text)  # YAML configuration for environment recreation
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)  # If true, other users can use this environment
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # Can be null for system events
    action = Column(String, index=True)  # "login", "logout", "code_execute", "user_create", "user_update", "user_delete", "api_call", etc.
    resource_type = Column(String, index=True)  # "user", "code_execution", "api_key", "code_library", "user_environment", etc.
    resource_id = Column(Integer, nullable=True)  # ID of the affected resource
    details = Column(Text)  # JSON string with additional details
    ip_address = Column(String, index=True)
    user_agent = Column(Text)
    status = Column(String, index=True)  # "success", "error", "warning"
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

# Community Models
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    title = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=False)  # Markdown content
    summary = Column(Text)  # Optional summary/preivew
    tags = Column(String)  # Comma-separated tags
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PostLike(Base):
    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    post_id = Column(Integer, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Unique constraint on user_id + post_id
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

class PostFavorite(Base):
    __tablename__ = "post_favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    post_id = Column(Integer, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Unique constraint on user_id + post_id
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    post_id = Column(Integer, index=True, nullable=False)
    parent_id = Column(Integer, index=True, nullable=True)  # For nested comments/replies
    content = Column(Text, nullable=False)
    like_count = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CommentLike(Base):
    __tablename__ = "comment_likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    comment_id = Column(Integer, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Unique constraint on user_id + comment_id
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

class PostCodeShare(Base):
    __tablename__ = "post_code_shares"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, index=True, nullable=False)
    code_library_id = Column(Integer, index=True, nullable=False)
    share_order = Column(Integer, default=0)  # Order of display
    created_at = Column(DateTime, default=datetime.utcnow)

class Follow(Base):
    __tablename__ = "follows"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, index=True, nullable=False)  # User who follows
    following_id = Column(Integer, index=True, nullable=False)  # User being followed
    created_at = Column(DateTime, default=datetime.utcnow)

    # Unique constraint on follower_id + following_id
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)

    # Check if admin user exists, create if not
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.is_admin == True).first()
        if not admin_user:
            # Create default admin user
            from auth import get_password_hash
            admin_password = "admin123"  # Default password, should be changed
            admin_user = User(
                username="admin",
                email="admin@coderunner.com",
                hashed_password=get_password_hash(admin_password),
                full_name="System Administrator",
                is_admin=True,
                is_active=True,
                user_level=4  # Enterprise level for admin
            )
            db.add(admin_user)
            db.commit()
            print(f"Default admin user created: username=admin, password={admin_password}")
            print("Please change the default password after first login!")
    finally:
        db.close()