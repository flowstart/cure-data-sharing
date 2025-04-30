import os
import json
import base64
import logging
from typing import Dict, List, Tuple, Any, Optional
from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, GT, pair
from charm.schemes.abenc.cp_abe_bsw07 import CPabe_BSW07
from charm.core.engine.util import objectToBytes, bytesToObject
from paillier import PaillierKeypair
from paillier import encrypt, decrypt

logger = logging.getLogger(__name__)

class CPABEManager:
    """CP-ABE (Ciphertext-Policy Attribute-Based Encryption) 管理器"""
    
    def __init__(self):
        self.keypair = PaillierKeypair.generate(2048)
        self.public_key = self.keypair.public_key
        self.private_key = self.keypair.private_key
        logger.info("CP-ABE Manager initialized")
    
    def encrypt_data(self, data, attributes):
        """加密数据"""
        # 将数据转换为JSON字符串
        data_str = json.dumps(data)
        # 使用公钥加密
        encrypted_data = encrypt(self.public_key, data_str)
        return encrypted_data

    def decrypt_data(self, encrypted_data):
        """解密数据"""
        # 使用私钥解密
        decrypted_data = decrypt(self.private_key, encrypted_data)
        # 将JSON字符串转换回Python对象
        return json.loads(decrypted_data)

    def generate_key(self, attributes):
        """生成属性密钥"""
        # 在实际应用中，这里应该实现基于属性的密钥生成
        # 这里简化处理，返回一个随机密钥
        return self.keypair.private_key
    
    def setup(self) -> Tuple[Any, Any]:
        """
        生成主密钥和公钥
        
        Returns:
            (master_key, public_key): 主密钥和公钥的元组
        """
        (master_key, public_key) = self.cpabe.setup()
        logger.info("Generated master key and public key")
        return (master_key, public_key)
    
    def save_keys(self, master_key: Any, public_key: Any, master_key_path: str, public_key_path: str) -> None:
        """
        保存主密钥和公钥到文件
        
        Args:
            master_key: 主密钥
            public_key: 公钥
            master_key_path: 主密钥保存路径
            public_key_path: 公钥保存路径
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(master_key_path), exist_ok=True)
        os.makedirs(os.path.dirname(public_key_path), exist_ok=True)
        
        # 保存主密钥
        master_key_bytes = objectToBytes(master_key, self.group)
        master_key_b64 = base64.b64encode(master_key_bytes).decode('utf-8')
        with open(master_key_path, 'w') as f:
            f.write(master_key_b64)
        
        # 保存公钥
        public_key_bytes = objectToBytes(public_key, self.group)
        public_key_b64 = base64.b64encode(public_key_bytes).decode('utf-8')
        with open(public_key_path, 'w') as f:
            f.write(public_key_b64)
        
        logger.info(f"Saved master key to {master_key_path} and public key to {public_key_path}")
    
    def load_keys(self, master_key_path: str, public_key_path: str) -> Tuple[Any, Any]:
        """
        从文件加载主密钥和公钥
        
        Args:
            master_key_path: 主密钥文件路径
            public_key_path: 公钥文件路径
            
        Returns:
            (master_key, public_key): 主密钥和公钥的元组
        """
        # 加载主密钥
        with open(master_key_path, 'r') as f:
            master_key_b64 = f.read()
        master_key_bytes = base64.b64decode(master_key_b64)
        master_key = bytesToObject(master_key_bytes, self.group)
        
        # 加载公钥
        with open(public_key_path, 'r') as f:
            public_key_b64 = f.read()
        public_key_bytes = base64.b64decode(public_key_b64)
        public_key = bytesToObject(public_key_bytes, self.group)
        
        logger.info(f"Loaded master key from {master_key_path} and public key from {public_key_path}")
        return (master_key, public_key)
    
    def keygen(self, public_key: Any, master_key: Any, attributes: List[str]) -> Any:
        """
        为给定的属性集生成用户密钥
        
        Args:
            public_key: 公钥
            master_key: 主密钥
            attributes: 用户属性列表
            
        Returns:
            user_key: 用户密钥
        """
        user_key = self.cpabe.keygen(public_key, master_key, attributes)
        logger.info(f"Generated user key for attributes: {attributes}")
        return user_key
    
    def encrypt(self, public_key: Any, message: str, policy: str) -> Tuple[str, Any]:
        """
        使用给定的访问策略加密消息
        
        Args:
            public_key: 公钥
            message: 要加密的消息
            policy: 访问策略字符串，例如 '(department:engineering AND level:senior) OR role:admin'
            
        Returns:
            (ciphertext_b64, ciphertext_obj): 加密后的密文的Base64编码和原始对象
        """
        # 将消息转换为Charm中的适当格式
        message_bytes = message.encode('utf-8')
        rand_msg = self.group.random(GT)
        
        # 加密消息
        ciphertext = self.cpabe.encrypt(public_key, rand_msg, policy)
        
        # 使用随机消息作为密钥加密原始消息
        key = objectToBytes(rand_msg, self.group)
        # 简单的XOR加密(生产环境应使用更安全的AES等)
        encrypted_message = bytes(a ^ b for a, b in zip(message_bytes, key * (len(message_bytes) // len(key) + 1)))
        
        # 将加密后的消息添加到密文中
        ciphertext['encrypted_message'] = encrypted_message
        
        # 将密文对象转换为可存储的格式
        ciphertext_bytes = objectToBytes(ciphertext, self.group)
        ciphertext_b64 = base64.b64encode(ciphertext_bytes).decode('utf-8')
        
        logger.info(f"Encrypted message with policy: {policy}")
        return (ciphertext_b64, ciphertext)
    
    def decrypt(self, public_key: Any, user_key: Any, ciphertext_b64: str) -> str:
        """
        使用用户密钥解密密文
        
        Args:
            public_key: 公钥
            user_key: 用户密钥
            ciphertext_b64: Base64编码的密文
            
        Returns:
            decrypted_message: 解密后的消息
            
        Raises:
            Exception: 如果解密失败
        """
        # 将Base64编码的密文转换回对象
        ciphertext_bytes = base64.b64decode(ciphertext_b64)
        ciphertext = bytesToObject(ciphertext_bytes, self.group)
        
        # 分离加密消息和密文
        encrypted_message = ciphertext.pop('encrypted_message', None)
        if encrypted_message is None:
            raise ValueError("Invalid ciphertext: missing encrypted message")
        
        try:
            # 解密随机消息
            rand_msg = self.cpabe.decrypt(public_key, user_key, ciphertext)
            
            # 使用随机消息作为密钥解密原始消息
            key = objectToBytes(rand_msg, self.group)
            # 简单的XOR解密
            decrypted_bytes = bytes(a ^ b for a, b in zip(encrypted_message, key * (len(encrypted_message) // len(key) + 1)))
            decrypted_message = decrypted_bytes.decode('utf-8')
            
            logger.info("Successfully decrypted message")
            return decrypted_message
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise Exception(f"Decryption failed. User may not have required attributes: {str(e)}")
    
    def serialize_user_key(self, user_key: Any) -> str:
        """
        将用户密钥序列化为Base64编码的字符串
        
        Args:
            user_key: 用户密钥对象
            
        Returns:
            serialized_key: Base64编码的用户密钥
        """
        user_key_bytes = objectToBytes(user_key, self.group)
        user_key_b64 = base64.b64encode(user_key_bytes).decode('utf-8')
        return user_key_b64
    
    def deserialize_user_key(self, user_key_b64: str) -> Any:
        """
        从Base64编码的字符串反序列化用户密钥
        
        Args:
            user_key_b64: Base64编码的用户密钥
            
        Returns:
            user_key: 用户密钥对象
        """
        user_key_bytes = base64.b64decode(user_key_b64)
        user_key = bytesToObject(user_key_bytes, self.group)
        return user_key