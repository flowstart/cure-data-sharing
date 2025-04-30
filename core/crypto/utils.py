import os
import json
import base64
import hashlib
from typing import Dict, List, Tuple, Any, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes, hmac
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


def generate_random_key(length: int = 32) -> bytes:
    """
    生成随机密钥
    
    Args:
        length: 密钥长度
        
    Returns:
        key: 随机密钥
    """
    return os.urandom(length)


def generate_salt(length: int = 16) -> bytes:
    """
    生成随机盐
    
    Args:
        length: 盐长度
        
    Returns:
        salt: 随机盐
    """
    return os.urandom(length)


def derive_key(password: str, salt: bytes, length: int = 32, iterations: int = 100000) -> bytes:
    """
    从密码派生密钥
    
    Args:
        password: 密码
        salt: 盐
        length: 密钥长度
        iterations: 迭代次数
        
    Returns:
        key: 派生的密钥
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    return kdf.derive(password.encode('utf-8'))


def encrypt_aes_gcm(plaintext: bytes, key: bytes) -> Tuple[bytes, bytes, bytes]:
    """
    使用AES-GCM加密
    
    Args:
        plaintext: 明文
        key: 密钥
        
    Returns:
        (ciphertext, iv, tag): 密文、初始化向量和认证标签
    """
    # 生成初始化向量
    iv = os.urandom(12)
    
    # 创建加密器
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
        backend=default_backend()
    ).encryptor()
    
    # 加密数据
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    
    # 获取认证标签
    tag = encryptor.tag
    
    return ciphertext, iv, tag


def decrypt_aes_gcm(ciphertext: bytes, key: bytes, iv: bytes, tag: bytes) -> bytes:
    """
    使用AES-GCM解密
    
    Args:
        ciphertext: 密文
        key: 密钥
        iv: 初始化向量
        tag: 认证标签
        
    Returns:
        plaintext: 明文
    """
    # 创建解密器
    decryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag),
        backend=default_backend()
    ).decryptor()
    
    # 解密数据
    return decryptor.update(ciphertext) + decryptor.finalize()


def encrypt_with_password(data: bytes, password: str) -> Dict[str, str]:
    """
    使用密码加密数据
    
    Args:
        data: 要加密的数据
        password: 密码
        
    Returns:
        encrypted_data: 加密后的数据，包含密文、盐、初始化向量和认证标签
    """
    # 生成盐
    salt = generate_salt()
    
    # 从密码派生密钥
    key = derive_key(password, salt)
    
    # 加密数据
    ciphertext, iv, tag = encrypt_aes_gcm(data, key)
    
    # 返回加密数据
    return {
        "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
        "salt": base64.b64encode(salt).decode('utf-8'),
        "iv": base64.b64encode(iv).decode('utf-8'),
        "tag": base64.b64encode(tag).decode('utf-8')
    }


def decrypt_with_password(encrypted_data: Dict[str, str], password: str) -> bytes:
    """
    使用密码解密数据
    
    Args:
        encrypted_data: 加密数据，包含密文、盐、初始化向量和认证标签
        password: 密码
        
    Returns:
        data: 解密后的数据
    """
    # 解码加密数据
    ciphertext = base64.b64decode(encrypted_data["ciphertext"])
    salt = base64.b64decode(encrypted_data["salt"])
    iv = base64.b64decode(encrypted_data["iv"])
    tag = base64.b64decode(encrypted_data["tag"])
    
    # 从密码派生密钥
    key = derive_key(password, salt)
    
    # 解密数据
    return decrypt_aes_gcm(ciphertext, key, iv, tag)


def hash_data(data: bytes) -> str:
    """
    计算数据的哈希值
    
    Args:
        data: 要哈希的数据
        
    Returns:
        hash_value: 哈希值
    """
    return hashlib.sha256(data).hexdigest()


def create_hmac(data: bytes, key: bytes) -> bytes:
    """
    创建HMAC
    
    Args:
        data: 要认证的数据
        key: 密钥
        
    Returns:
        hmac_value: HMAC值
    """
    h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
    h.update(data)
    return h.finalize()


def verify_hmac(data: bytes, key: bytes, hmac_value: bytes) -> bool:
    """
    验证HMAC
    
    Args:
        data: 认证的数据
        key: 密钥
        hmac_value: HMAC值
        
    Returns:
        is_valid: HMAC是否有效
    """
    h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
    h.update(data)
    try:
        h.verify(hmac_value)
        return True
    except:
        return False


def encrypt_json(json_data: Dict[str, Any], key: bytes) -> Dict[str, str]:
    """
    加密JSON数据
    
    Args:
        json_data: JSON数据
        key: 密钥
        
    Returns:
        encrypted_data: 加密后的数据
    """
    # 将JSON转换为字节
    data = json.dumps(json_data).encode('utf-8')
    
    # 加密数据
    ciphertext, iv, tag = encrypt_aes_gcm(data, key)
    
    # 返回加密数据
    return {
        "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
        "iv": base64.b64encode(iv).decode('utf-8'),
        "tag": base64.b64encode(tag).decode('utf-8')
    }


def decrypt_json(encrypted_data: Dict[str, str], key: bytes) -> Dict[str, Any]:
    """
    解密JSON数据
    
    Args:
        encrypted_data: 加密数据
        key: 密钥
        
    Returns:
        json_data: 解密后的JSON数据
    """
    # 解码加密数据
    ciphertext = base64.b64decode(encrypted_data["ciphertext"])
    iv = base64.b64decode(encrypted_data["iv"])
    tag = base64.b64decode(encrypted_data["tag"])
    
    # 解密数据
    data = decrypt_aes_gcm(ciphertext, key, iv, tag)
    
    # 将字节转换为JSON
    return json.loads(data.decode('utf-8'))


def split_secret(secret: bytes, threshold: int, shares: int) -> List[Tuple[int, bytes]]:
    """
    使用Shamir's Secret Sharing将秘密分割为多份
    
    Args:
        secret: 秘密
        threshold: 恢复秘密所需的份数
        shares: 总份数
        
    Returns:
        shares: 份额列表，每个份额是(索引, 值)对
    """
    # 这是一个简单的实现，实际应用中应使用专门的库如PyCryptodome
    if threshold > shares:
        raise ValueError("Threshold cannot be greater than the number of shares")
    
    if threshold < 2:
        raise ValueError("Threshold must be at least 2")
    
    # 生成随机系数
    coefficients = [secret] + [generate_random_key(len(secret)) for _ in range(threshold - 1)]
    
    # 生成份额
    result = []
    for i in range(1, shares + 1):
        x = i
        y = bytes([0] * len(secret))
        
        # 计算多项式值
        for j, coef in enumerate(coefficients):
            term = bytes([pow(x, j, 256) * coef[k] % 256 for k in range(len(secret))])
            y = bytes([(y[k] + term[k]) % 256 for k in range(len(secret))])
        
        result.append((i, y))
    
    return result


def combine_secret(shares: List[Tuple[int, bytes]]) -> bytes:
    """
    使用Shamir's Secret Sharing恢复秘密
    
    Args:
        shares: 份额列表，每个份额是(索引, 值)对
        
    Returns:
        secret: 恢复的秘密
    """
    # 这是一个简单的实现，实际应用中应使用专门的库如PyCryptodome
    if not shares:
        raise ValueError("No shares provided")
    
    # 获取秘密长度
    secret_len = len(shares[0][1])
    
    # 用拉格朗日插值恢复秘密
    secret = bytes([0] * secret_len)
    for i, share_i in shares:
        numerator = 1
        denominator = 1
        
        for j, share_j in shares:
            if i != j:
                numerator = (numerator * j) % 256
                denominator = (denominator * ((j - i) % 256)) % 256
        
        # 计算拉格朗日系数
        lagrange_coef = (numerator * pow(denominator, 254, 256)) % 256
        
        # 更新秘密
        term = bytes([(lagrange_coef * share_i[k]) % 256 for k in range(secret_len)])
        secret = bytes([(secret[k] + term[k]) % 256 for k in range(secret_len)])
    
    return secret