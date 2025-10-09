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
    created_at = Column(DateTime, default=datetime.utcnow)

class CodeExecution(Base):
    __tablename__ = "code_executions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    code = Column(Text)
    result = Column(Text)
    status = Column(String)  # "success", "error", "running"
    created_at = Column(DateTime, default=datetime.utcnow)
    execution_time = Column(Integer)  # in milliseconds

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
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print(f"Default admin user created: username=admin, password={admin_password}")
            print("Please change the default password after first login!")
    finally:
        db.close()