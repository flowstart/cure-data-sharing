import io
import json
import logging
from typing import Dict, List, Union, BinaryIO, Any, Optional
import requests
import base64
import ipfshttpclient
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

class IPFSClient:
    """IPFS分布式存储客户端"""
    
    def __init__(self, api_url: str = None, gateway_url: str = None):
        """
        初始化IPFS客户端
        
        Args:
            api_url: IPFS API URL，如果为None则使用配置中的URL
            gateway_url: IPFS网关URL，如果为None则使用配置中的URL
        """
        self.api_url = api_url or settings.IPFS_API_URL
        self.gateway_url = gateway_url or settings.IPFS_GATEWAY_URL
        
        try:
            # 连接到IPFS节点
            self.client = ipfshttpclient.connect(self.api_url)
            logger.info(f"Connected to IPFS node at {self.api_url}")
        except Exception as e:
            logger.error(f"Failed to connect to IPFS node at {self.api_url}: {str(e)}")
            raise ConnectionError(f"Failed to connect to IPFS node: {str(e)}")
    
    def add_file(self, file_path: Union[str, Path]) -> str:
        """
        将文件添加到IPFS
        
        Args:
            file_path: 文件路径
            
        Returns:
            cid: 内容标识符(CID)
        """
        try:
            result = self.client.add(str(file_path))
            cid = result['Hash']
            logger.info(f"Added file {file_path} to IPFS with CID: {cid}")
            return cid
        except Exception as e:
            logger.error(f"Failed to add file {file_path} to IPFS: {str(e)}")
            raise
    
    def add_bytes(self, data: bytes, filename: str = "file") -> str:
        """
        将字节数据添加到IPFS
        
        Args:
            data: 字节数据
            filename: 文件名
            
        Returns:
            cid: 内容标识符(CID)
        """
        try:
            result = self.client.add_bytes(data, name=filename)
            logger.info(f"Added bytes data to IPFS with CID: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to add bytes data to IPFS: {str(e)}")
            raise
    
    def add_json(self, json_data: Dict) -> str:
        """
        将JSON数据添加到IPFS
        
        Args:
            json_data: JSON数据
            
        Returns:
            cid: 内容标识符(CID)
        """
        try:
            # 将JSON数据转换为字节
            json_bytes = json.dumps(json_data).encode('utf-8')
            # 添加到IPFS
            cid = self.add_bytes(json_bytes, filename="data.json")
            logger.info(f"Added JSON data to IPFS with CID: {cid}")
            return cid
        except Exception as e:
            logger.error(f"Failed to add JSON data to IPFS: {str(e)}")
            raise
    
    def add_encrypted_data(self, encrypted_data: str, metadata: Dict = None) -> str:
        """
        将加密数据添加到IPFS
        
        Args:
            encrypted_data: Base64编码的加密数据
            metadata: 可选的元数据
            
        Returns:
            cid: 内容标识符(CID)
        """
        try:
            # 准备数据
            data = {
                "encrypted_data": encrypted_data,
                "metadata": metadata or {}
            }
            
            # 添加到IPFS
            cid = self.add_json(data)
            logger.info(f"Added encrypted data to IPFS with CID: {cid}")
            return cid
        except Exception as e:
            logger.error(f"Failed to add encrypted data to IPFS: {str(e)}")
            raise
    
    def get_file(self, cid: str, output_path: Union[str, Path] = None) -> Optional[bytes]:
        """
        从IPFS获取文件
        
        Args:
            cid: 内容标识符(CID)
            output_path: 输出文件路径，如果为None则返回文件内容
            
        Returns:
            file_content: 如果output_path为None，则返回文件内容，否则返回None
        """
        try:
            if output_path:
                # 确保输出目录存在
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 下载文件
                self.client.get(cid, str(output_path.parent))
                # 重命名文件
                downloaded_file = Path(output_path.parent) / cid
                if downloaded_file.exists():
                    downloaded_file.rename(output_path)
                logger.info(f"Downloaded file from IPFS with CID: {cid} to {output_path}")
                return None
            else:
                # 获取文件内容
                content = self.client.cat(cid)
                logger.info(f"Retrieved file content from IPFS with CID: {cid}")
                return content
        except Exception as e:
            logger.error(f"Failed to get file from IPFS with CID {cid}: {str(e)}")
            raise
    
    def get_json(self, cid: str) -> Dict:
        """
        从IPFS获取JSON数据
        
        Args:
            cid: 内容标识符(CID)
            
        Returns:
            json_data: JSON数据
        """
        try:
            # 获取文件内容
            content = self.client.cat(cid)
            # 解析JSON
            json_data = json.loads(content.decode('utf-8'))
            logger.info(f"Retrieved JSON data from IPFS with CID: {cid}")
            return json_data
        except Exception as e:
            logger.error(f"Failed to get JSON data from IPFS with CID {cid}: {str(e)}")
            raise
    
    def get_encrypted_data(self, cid: str) -> Dict:
        """
        从IPFS获取加密数据
        
        Args:
            cid: 内容标识符(CID)
            
        Returns:
            data: 包含加密数据和元数据的字典
        """
        try:
            # 获取JSON数据
            data = self.get_json(cid)
            
            # 验证数据格式
            if "encrypted_data" not in data:
                raise ValueError(f"Invalid data format: missing 'encrypted_data' field")
            
            logger.info(f"Retrieved encrypted data from IPFS with CID: {cid}")
            return data
        except Exception as e:
            logger.error(f"Failed to get encrypted data from IPFS with CID {cid}: {str(e)}")
            raise
    
    def pin_cid(self, cid: str) -> bool:
        """
        将CID固定到IPFS节点
        
        Args:
            cid: 内容标识符(CID)
            
        Returns:
            success: 操作是否成功
        """
        try:
            self.client.pin.add(cid)
            logger.info(f"Pinned CID {cid} to IPFS node")
            return True
        except Exception as e:
            logger.error(f"Failed to pin CID {cid}: {str(e)}")
            return False
    
    def unpin_cid(self, cid: str) -> bool:
        """
        从IPFS节点取消固定CID
        
        Args:
            cid: 内容标识符(CID)
            
        Returns:
            success: 操作是否成功
        """
        try:
            self.client.pin.rm(cid)
            logger.info(f"Unpinned CID {cid} from IPFS node")
            return True
        except Exception as e:
            logger.error(f"Failed to unpin CID {cid}: {str(e)}")
            return False
    
    def get_gateway_url(self, cid: str) -> str:
        """
        获取IPFS网关URL
        
        Args:
            cid: 内容标识符(CID)
            
        Returns:
            url: 网关URL
        """
        # 确保网关URL以/结尾
        gateway_url = self.gateway_url
        if not gateway_url.endswith('/'):
            gateway_url += '/'
        
        # 格式化URL
        url = f"{gateway_url}ipfs/{cid}"
        return url
    
    def is_valid_cid(self, cid: str) -> bool:
        """
        检查CID是否有效
        
        Args:
            cid: 内容标识符(CID)
            
        Returns:
            is_valid: CID是否有效
        """
        try:
            # 尝试检索CID的头部信息
            self.client.ls(cid)
            return True
        except Exception:
            return False