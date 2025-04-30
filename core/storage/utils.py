import os
import json
import base64
import hashlib
from typing import Dict, List, Any, Optional, BinaryIO, Union
import mimetypes
import io
import logging

logger = logging.getLogger(__name__)

def detect_content_type(file_path: str) -> str:
    """
    检测文件内容类型
    
    Args:
        file_path: 文件路径
        
    Returns:
        content_type: 内容类型
    """
    # 获取MIME类型
    content_type, _ = mimetypes.guess_type(file_path)
    
    # 如果无法检测到，默认为二进制流
    if content_type is None:
        content_type = "application/octet-stream"
    
    return content_type

def detect_content_type_from_bytes(data: bytes, filename: str = None) -> str:
    """
    从字节数据检测内容类型
    
    Args:
        data: 字节数据
        filename: 文件名（可选）
        
    Returns:
        content_type: 内容类型
    """
    # 如果提供了文件名，使用文件名检测
    if filename:
        content_type = detect_content_type(filename)
        if content_type != "application/octet-stream":
            return content_type
    
    # 尝试从内容检测（简单检测，仅支持常见类型）
    # 检测图像类型
    if data.startswith(b'\xff\xd8\xff'):
        return "image/jpeg"
    elif data.startswith(b'\x89PNG\r\n\x1a\n'):
        return "image/png"
    elif data.startswith(b'GIF87a') or data.startswith(b'GIF89a'):
        return "image/gif"
    elif data.startswith(b'BM'):
        return "image/bmp"
    
    # 检测PDF
    if data.startswith(b'%PDF'):
        return "application/pdf"
    
    # 检测ZIP
    if data.startswith(b'PK\x03\x04'):
        return "application/zip"
    
    # 尝试检测文本类型
    try:
        text = data.decode('utf-8')
        
        # 检测JSON
        if text.strip().startswith('{') and text.strip().endswith('}'):
            try:
                json.loads(text)
                return "application/json"
            except:
                pass
        
        # 检测XML
        if text.strip().startswith('<?xml') or (text.strip().startswith('<') and '>' in text):
            return "application/xml"
        
        # 默认为文本
        return "text/plain"
    except:
        # 如果无法解析为文本，则视为二进制
        pass
    
    # 默认为二进制流
    return "application/octet-stream"

def hash_file(file_path: str, algorithm: str = 'sha256') -> str:
    """
    计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法
        
    Returns:
        hash_value: 哈希值
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        # 分块读取以处理大文件
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()

def hash_data(data: Union[str, bytes], algorithm: str = 'sha256') -> str:
    """
    计算数据哈希值
    
    Args:
        data: 数据
        algorithm: 哈希算法
        
    Returns:
        hash_value: 哈希值
    """
    hash_obj = hashlib.new(algorithm)
    
    # 如果是字符串，转换为字节
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    hash_obj.update(data)
    return hash_obj.hexdigest()

def encode_base64(data: Union[str, bytes]) -> str:
    """
    Base64编码
    
    Args:
        data: 数据
        
    Returns:
        encoded_data: 编码后的数据
    """
    # 如果是字符串，转换为字节
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    return base64.b64encode(data).decode('utf-8')

def decode_base64(data: str) -> bytes:
    """
    Base64解码
    
    Args:
        data: 编码数据
        
    Returns:
        decoded_data: 解码后的数据
    """
    return base64.b64decode(data)

def save_to_temp_file(data: bytes, filename: str = None) -> str:
    """
    将数据保存到临时文件
    
    Args:
        data: 字节数据
        filename: 文件名（可选）
        
    Returns:
        temp_path: 临时文件路径
    """
    # 创建临时目录
    temp_dir = os.path.join(os.getcwd(), 'tmp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # 生成临时文件名
    if filename:
        # 安全处理文件名
        safe_filename = os.path.basename(filename)
        # 添加哈希值以避免冲突
        file_hash = hash_data(data)[:8]
        temp_filename = f"{file_hash}_{safe_filename}"
    else:
        # 使用哈希值作为文件名
        file_hash = hash_data(data)
        temp_filename = f"{file_hash}"
    
    # 完整路径
    temp_path = os.path.join(temp_dir, temp_filename)
    
    # 写入数据
    with open(temp_path, 'wb') as f:
        f.write(data)
    
    return temp_path

def read_file_chunks(file_path: str, chunk_size: int = 4096):
    """
    分块读取文件
    
    Args:
        file_path: 文件路径
        chunk_size: 块大小
        
    Yields:
        chunk: 文件块
    """
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

def file_size_format(size: int) -> str:
    """
    格式化文件大小
    
    Args:
        size: 文件大小（字节）
        
    Returns:
        formatted_size: 格式化后的大小
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    
    return f"{size:.2f} PB"

def get_file_metadata(file_path: str) -> Dict[str, Any]:
    """
    获取文件元数据
    
    Args:
        file_path: 文件路径
        
    Returns:
        metadata: 文件元数据
    """
    stat = os.stat(file_path)
    
    return {
        'name': os.path.basename(file_path),
        'path': file_path,
        'size': stat.st_size,
        'formatted_size': file_size_format(stat.st_size),
        'created_at': stat.st_ctime,
        'modified_at': stat.st_mtime,
        'content_type': detect_content_type(file_path),
        'hash': hash_file(file_path)
    }

def write_json_file(data: Dict[str, Any], file_path: str) -> None:
    """
    将JSON数据写入文件
    
    Args:
        data: JSON数据
        file_path: 文件路径
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # 写入JSON文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def read_json_file(file_path: str) -> Dict[str, Any]:
    """
    从文件读取JSON数据
    
    Args:
        file_path: 文件路径
        
    Returns:
        data: JSON数据
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_directory_if_not_exists(directory: str) -> None:
    """
    如果目录不存在则创建
    
    Args:
        directory: 目录路径
    """
    os.makedirs(directory, exist_ok=True)

def is_valid_file_path(file_path: str) -> bool:
    """
    检查文件路径是否有效
    
    Args:
        file_path: 文件路径
        
    Returns:
        is_valid: 是否有效
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return False
    
    # 检查是否是文件
    if not os.path.isfile(file_path):
        return False
    
    # 检查是否可读
    if not os.access(file_path, os.R_OK):
        return False
    
    return True