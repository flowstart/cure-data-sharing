import os
import base64
import hashlib
import secrets
from typing import Dict, List, Tuple, Optional, Union, Any
from passlib.context import CryptContext
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
        
    Returns:
        is_verified: 是否验证通过
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    获取密码哈希
    
    Args:
        password: 明文密码
        
    Returns:
        hashed_password: 哈希密码
    """
    return pwd_context.hash(password)


def generate_random_key(length: int = 32) -> bytes:
    """
    生成随机密钥
    
    Args:
        length: 密钥长度
        
    Returns:
        key: 随机密钥
    """
    return os.urandom(length)


def generate_secure_token(length: int = 32) -> str:
    """
    生成安全令牌
    
    Args:
        length: 令牌长度
        
    Returns:
        token: 安全令牌
    """
    return secrets.token_hex(length)


def generate_confirmation_code(length: int = 6) -> str:
    """
    生成确认码
    
    Args:
        length: 确认码长度
        
    Returns:
        code: 确认码
    """
    return ''.join(secrets.choice('0123456789') for _ in range(length))


def encrypt_aes(data: Union[str, bytes], key: bytes) -> bytes:
    """
    AES加密
    
    Args:
        data: 明文数据
        key: 密钥
        
    Returns:
        encrypted: 密文数据
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    # 初始化向量
    iv = os.urandom(16)
    
    # 创建填充器
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()
    
    # 创建加密器
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    # 返回初始化向量和密文
    return iv + ciphertext


def decrypt_aes(encrypted_data: bytes, key: bytes) -> bytes:
    """
    AES解密
    
    Args:
        encrypted_data: 密文数据
        key: 密钥
        
    Returns:
        decrypted: 明文数据
    """
    # 提取初始化向量和密文
    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    
    # 创建解密器
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    
    # 创建去填充器
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    
    return data


def hash_data(data: Union[str, bytes]) -> str:
    """
    哈希数据
    
    Args:
        data: 明文数据
        
    Returns:
        hashed: 哈希值
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    return hashlib.sha256(data).hexdigest()


def encode_base64(data: Union[str, bytes]) -> str:
    """
    Base64编码
    
    Args:
        data: 明文数据
        
    Returns:
        encoded: Base64编码数据
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    return base64.b64encode(data).decode('utf-8')


def decode_base64(data: str) -> bytes:
    """
    Base64解码
    
    Args:
        data: Base64编码数据
        
    Returns:
        decoded: 解码后的数据
    """
    return base64.b64decode(data)


def is_valid_signature(message: str, signature: str, public_key: str) -> bool:
    """
    验证签名
    
    Args:
        message: 消息
        signature: 签名
        public_key: 公钥
        
    Returns:
        is_valid: 是否有效
    """
    # 这里是一个简单的占位实现
    # 实际应用中应该使用合适的签名算法如ECDSA或RSA
    # 如果需要实现实际的签名验证，请使用
    # cryptography.hazmat.primitives.asymmetric包中的签名算法
    
    return True