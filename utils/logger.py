import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
import json
from datetime import datetime

# 默认日志格式
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_DIR = "logs"


class JsonFormatter(logging.Formatter):
    """JSON格式化器"""
    
    def __init__(self, fmt=None, datefmt=None, style='%', json_default=str):
        super().__init__(fmt, datefmt, style)
        self.json_default = json_default
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        for key, value in record.__dict__.items():
            if key not in ["args", "asctime", "created", "exc_info", "exc_text", "filename", 
                          "funcName", "id", "levelname", "levelno", "lineno", "module", 
                          "msecs", "message", "msg", "name", "pathname", "process", 
                          "processName", "relativeCreated", "stack_info", "thread", "threadName"]:
                log_data[key] = value
        
        return json.dumps(log_data, default=self.json_default)


def setup_logging(log_level=None, log_file=None, json_format=False):
    """
    设置日志系统
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径
        json_format: 是否使用JSON格式
    """
    # 设置日志级别
    level = getattr(logging, (log_level or DEFAULT_LOG_LEVEL).upper())
    
    # 创建根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 清除现有处理器
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 设置格式化器
    if json_format:
        console_formatter = JsonFormatter()
    else:
        console_formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 如果指定了日志文件，创建文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # 创建旋转文件处理器
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(level)
        
        # 设置格式化器
        if json_format:
            file_formatter = JsonFormatter()
        else:
            file_formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
        
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # 设置其他库的日志级别
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    # 返回根日志器
    return root_logger


def get_logger(name, log_level=None):
    """
    获取日志器
    
    Args:
        name: 日志器名称
        log_level: 日志级别
        
    Returns:
        logger: 日志器
    """
    logger = logging.getLogger(name)
    
    # 如果指定了日志级别，设置级别
    if log_level:
        logger.setLevel(getattr(logging, log_level.upper()))
    
    return logger