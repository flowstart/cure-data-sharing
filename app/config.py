import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

class Settings(BaseSettings):
    """系统配置类"""
    
    # 应用设置
    APP_NAME: str = "数据安全共享系统"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "基于CP-ABE和区块链技术的数据安全共享系统"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_secret_key_here")
    
    # API设置
    API_V1_PREFIX: str = "/api/v1"
    
    # 数据库设置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./secure_data_sharing.db")
    
    # 密码学设置
    MASTER_KEY_PATH: str = os.getenv("MASTER_KEY_PATH", "./keys/master_key")
    PUBLIC_KEY_PATH: str = os.getenv("PUBLIC_KEY_PATH", "./keys/public_key")
    
    # 区块链设置
    ETHEREUM_NODE_URL: str = os.getenv("ETHEREUM_NODE_URL", "http://localhost:8545")
    ETHEREUM_PRIVATE_KEY: str = os.getenv("ETHEREUM_PRIVATE_KEY", "")
    DATA_REGISTRY_CONTRACT_ADDRESS: str = os.getenv("DATA_REGISTRY_CONTRACT_ADDRESS", "")
    ATTRIBUTE_AUTHORITY_CONTRACT_ADDRESS: str = os.getenv("ATTRIBUTE_AUTHORITY_CONTRACT_ADDRESS", "")
    
    # IPFS设置
    IPFS_API_URL: str = os.getenv("IPFS_API_URL", "http://localhost:5001")
    IPFS_GATEWAY_URL: str = os.getenv("IPFS_GATEWAY_URL", "http://localhost:8080")
    
    # JWT设置
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 日志设置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局设置对象
settings = Settings()