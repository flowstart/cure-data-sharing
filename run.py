import os
import sys
import uvicorn
import logging
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
load_dotenv()

# 设置Python路径
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# 配置基本日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.getenv('LOG_FILE', 'logs/app.log'))
    ]
)

if __name__ == "__main__":
    # 从环境变量或使用默认值
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8000'))
    reload = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # 启动应用
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=os.getenv('LOG_LEVEL', 'info').lower()
    )