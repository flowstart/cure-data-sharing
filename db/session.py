from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings

# 创建SQLAlchemy引擎
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True
)

# 创建SessionLocal类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

def get_db() -> Session:
    """
    获取数据库会话
    
    Returns:
        db: 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    初始化数据库
    """
    # 创建表
    Base.metadata.create_all(bind=engine)