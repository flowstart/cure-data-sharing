import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from web3 import Web3

from core.crypto.cp_abe import CPABEManager
from core.blockchain.ethereum import EthereumClient
from core.storage.ipfs import IPFSClient
from app.config import settings
from db.crud.data import DataCrud
from db.crud.user import UserCrud

logger = logging.getLogger(__name__)

class DataService:
    """数据服务类，负责数据的加密、存储和共享"""
    
    def __init__(
        self,
        cpabe_manager: CPABEManager = None,
        ethereum_client: EthereumClient = None,
        ipfs_client: IPFSClient = None,
        data_crud: DataCrud = None,
        user_crud: UserCrud = None
    ):
        """
        初始化数据服务
        
        Args:
            cpabe_manager: CP-ABE管理器实例
            ethereum_client: 以太坊客户端实例
            ipfs_client: IPFS客户端实例
            data_crud: 数据CRUD实例
            user_crud: 用户CRUD实例
        """
        self.cpabe_manager = cpabe_manager or CPABEManager()
        self.ethereum_client = ethereum_client or EthereumClient()
        self.ipfs_client = ipfs_client or IPFSClient()
        self.data_crud = data_crud
        self.user_crud = user_crud
        
        # 加载主密钥和公钥
        try:
            self.master_key, self.public_key = self.cpabe_manager.load_keys(
                settings.MASTER_KEY_PATH,
                settings.PUBLIC_KEY_PATH
            )
            logger.info("Loaded CP-ABE keys")
        except Exception as e:
            # 如果密钥不存在，生成新的密钥
            logger.warning(f"Failed to load CP-ABE keys, generating new keys: {str(e)}")
            self.master_key, self.public_key = self.cpabe_manager.setup()
            self.cpabe_manager.save_keys(
                self.master_key,
                self.public_key,
                settings.MASTER_KEY_PATH,
                settings.PUBLIC_KEY_PATH
            )
        
        # 加载数据注册合约
        try:
            contract_address = settings.DATA_REGISTRY_CONTRACT_ADDRESS
            abi_path = "core/blockchain/contracts/abi/DataRegistry.json"
            self.data_registry = self.ethereum_client.load_contract(contract_address, abi_path)
            logger.info(f"Loaded DataRegistry contract at {contract_address}")
        except Exception as e:
            logger.error(f"Failed to load DataRegistry contract: {str(e)}")
            self.data_registry = None
    
    def publish_data(
        self,
        owner_id: int,
        data: Any,
        title: str,
        description: str,
        data_type: str,
        access_policy: str,
        tags: List[str] = None,
        metadata: Dict = None
    ) -> Dict:
        """
        发布数据（加密并上传到IPFS，注册到区块链）
        
        Args:
            owner_id: 数据拥有者ID
            data: 要发布的数据
            title: 数据标题
            description: 数据描述
            data_type: 数据类型
            access_policy: CP-ABE访问策略
            tags: 标签列表
            metadata: 元数据
            
        Returns:
            published_data: 已发布的数据信息
        """
        # 获取用户信息
        user = self.user_crud.get(owner_id)
        if not user:
            raise ValueError(f"User with ID {owner_id} not found")
        
        # 准备元数据
        if metadata is None:
            metadata = {}
        
        if tags is None:
            tags = []
        
        # 为数据生成唯一ID
        data_id = str(uuid.uuid4())
        
        # 将数据转换为JSON字符串
        if isinstance(data, dict) or isinstance(data, list):
            data_str = json.dumps(data)
        else:
            data_str = str(data)
        
        # 使用CP-ABE加密数据
        logger.info(f"Encrypting data with policy: {access_policy}")
        encrypted_data, _ = self.cpabe_manager.encrypt(self.public_key, data_str, access_policy)
        
        # 准备IPFS元数据
        ipfs_metadata = {
            "title": title,
            "description": description,
            "data_type": data_type,
            "owner_address": user.blockchain_address,
            "created_at": datetime.now().isoformat(),
            "tags": tags,
            "user_metadata": metadata
        }
        
        # 将加密数据上传到IPFS
        logger.info("Uploading encrypted data to IPFS")
        ipfs_cid = self.ipfs_client.add_encrypted_data(encrypted_data, ipfs_metadata)
        
        # 将数据固定到IPFS节点
        self.ipfs_client.pin_cid(ipfs_cid)
        
        # 准备区块链访问策略（JSON格式）
        blockchain_policy = json.dumps({
            "policy_type": "cp_abe",
            "policy_string": access_policy,
            "encryption_method": "CP-ABE BSW07"
        })
        
        # 准备区块链元数据
        blockchain_metadata = json.dumps({
            "title": title,
            "description": description,
            "data_type": data_type,
            "tags": tags,
            "ipfs_gateway_url": self.ipfs_client.get_gateway_url(ipfs_cid)
        })
        
        # 在区块链上注册数据
        if self.data_registry:
            logger.info("Registering data on blockchain")
            tx_hash = self.ethereum_client.send_contract_transaction(
                self.data_registry,
                "registerDataAsset",
                ipfs_cid,
                blockchain_policy,
                blockchain_metadata
            )
            
            # 等待交易确认
            receipt = self.ethereum_client.get_transaction_receipt(tx_hash)
            # 从事件日志中提取dataId
            blockchain_data_id = None
            for log in receipt.get('logs', []):
                # 解析DataAssetRegistered事件
                # 事件定义: event DataAssetRegistered(bytes32 indexed dataId, address indexed owner, string ipfsCid, uint256 timestamp)
                if log.get('topics') and len(log.get('topics')) >= 3:
                    # 第一个主题是事件签名，第二个主题是dataId
                    blockchain_data_id = log.get('topics')[1].hex()
                    break
        else:
            logger.warning("Data registry contract not available, skipping blockchain registration")
            blockchain_data_id = None
            tx_hash = None
        
        # 在数据库中保存数据记录
        data_record = {
            "id": data_id,
            "owner_id": owner_id,
            "title": title,
            "description": description,
            "data_type": data_type,
            "ipfs_cid": ipfs_cid,
            "access_policy": access_policy,
            "blockchain_data_id": blockchain_data_id,
            "blockchain_tx_hash": tx_hash,
            "tags": tags,
            "metadata": metadata,
            "created_at": datetime.now()
        }
        
        # 保存到数据库
        if self.data_crud:
            db_data = self.data_crud.create(data_record)
            data_record["db_id"] = db_data.id
        
        logger.info(f"Data published successfully with ID: {data_id}")
        return data_record
    
    def access_data(
        self,
        user_id: int,
        data_id: str,
        purpose: str = None
    ) -> Dict:
        """
        访问数据（从IPFS读取加密数据并解密）
        
        Args:
            user_id: 用户ID
            data_id: 数据ID
            purpose: 访问目的
            
        Returns:
            data: 解密后的数据
        """
        # 获取用户信息
        user = self.user_crud.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # 获取数据记录
        data_record = self.data_crud.get_by_data_id(data_id)
        if not data_record:
            raise ValueError(f"Data with ID {data_id} not found")
        
        # 从IPFS获取加密数据
        logger.info(f"Retrieving encrypted data from IPFS with CID: {data_record.ipfs_cid}")
        encrypted_data = self.ipfs_client.get_encrypted_data(data_record.ipfs_cid)
        
        # 获取用户的CP-ABE密钥
        if not user.cpabe_key:
            raise ValueError(f"User {user_id} does not have a CP-ABE key")
        
        user_key = self.cpabe_manager.deserialize_user_key(user.cpabe_key)
        
        # 解密数据
        try:
            logger.info(f"Attempting to decrypt data for user {user_id}")
            decrypted_data = self.cpabe_manager.decrypt(
                self.public_key,
                user_key,
                encrypted_data["encrypted_data"]
            )
            
            # 在区块链上记录访问
            if self.data_registry and data_record.blockchain_data_id:
                try:
                    # 将字符串转换为bytes32
                    blockchain_data_id = Web3.to_bytes(hexstr=data_record.blockchain_data_id)
                    
                    # 记录访问
                    logger.info(f"Recording access on blockchain")
                    tx_hash = self.ethereum_client.send_contract_transaction(
                        self.data_registry,
                        "recordAccess",
                        blockchain_data_id,
                        user.blockchain_address,
                        purpose or "Data access through platform"
                    )
                    
                    logger.info(f"Access recorded on blockchain with tx hash: {tx_hash}")
                except Exception as e:
                    logger.error(f"Failed to record access on blockchain: {str(e)}")
            
            # 记录访问日志到数据库
            # ...
            
            # 尝试解析JSON
            try:
                data = json.loads(decrypted_data)
                return {
                    "data": data,
                    "metadata": encrypted_data.get("metadata", {}),
                    "data_id": data_id,
                    "accessed_at": datetime.now().isoformat(),
                    "is_json": True
                }
            except json.JSONDecodeError:
                # 如果不是有效的JSON，直接返回字符串
                return {
                    "data": decrypted_data,
                    "metadata": encrypted_data.get("metadata", {}),
                    "data_id": data_id,
                    "accessed_at": datetime.now().isoformat(),
                    "is_json": False
                }
                
        except Exception as e:
            logger.error(f"Failed to decrypt data: {str(e)}")
            raise ValueError(f"Failed to decrypt data. Likely you don't have the required attributes: {str(e)}")
    
    def generate_user_key(self, user_id: int, attributes: List[str]) -> str:
        """
        为用户生成CP-ABE属性密钥
        
        Args:
            user_id: 用户ID
            attributes: 用户属性列表
            
        Returns:
            user_key_b64: Base64编码的用户密钥
        """
        # 获取用户信息
        user = self.user_crud.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # 生成用户密钥
        logger.info(f"Generating CP-ABE key for user {user_id} with attributes: {attributes}")
        user_key = self.cpabe_manager.keygen(self.public_key, self.master_key, attributes)
        
        # 序列化用户密钥
        user_key_b64 = self.cpabe_manager.serialize_user_key(user_key)
        
        # 更新用户记录
        if self.user_crud:
            self.user_crud.update(user_id, {"cpabe_key": user_key_b64})
        
        return user_key_b64
    
    def update_data(
        self,
        owner_id: int,
        data_id: str,
        data: Any = None,
        title: str = None,
        description: str = None,
        access_policy: str = None,
        tags: List[str] = None,
        metadata: Dict = None
    ) -> Dict:
        """
        更新数据信息
        
        Args:
            owner_id: 数据拥有者ID
            data_id: 数据ID
            data: 新的数据内容（如果需要更新）
            title: 新的标题
            description: 新的描述
            access_policy: 新的访问策略
            tags: 新的标签列表
            metadata: 新的元数据
            
        Returns:
            updated_data: 更新后的数据信息
        """
        # 获取数据记录
        data_record = self.data_crud.get_by_data_id(data_id)
        if not data_record:
            raise ValueError(f"Data with ID {data_id} not found")
        
        # 验证拥有者
        if data_record.owner_id != owner_id:
            raise ValueError("You are not the owner of this data")
        
        # 准备更新的记录
        updates = {}
        if title is not None:
            updates["title"] = title
        if description is not None:
            updates["description"] = description
        if tags is not None:
            updates["tags"] = tags
        if metadata is not None:
            updates["metadata"] = metadata
        
        # 如果需要更新数据内容或访问策略，则需要重新加密并上传到IPFS
        if data is not None or access_policy is not None:
            # 如果没有提供新的访问策略，使用现有的策略
            new_policy = access_policy or data_record.access_policy
            
            # 如果没有提供新的数据，则需要先获取并解密当前数据
            if data is None:
                # 创建一个临时的对象，模拟用户以拥有者身份访问数据
                owner = self.user_crud.get(owner_id)
                if not owner or not owner.cpabe_key:
                    raise ValueError("Owner does not have a valid CP-ABE key")
                
                # 从IPFS获取加密数据
                encrypted_data = self.ipfs_client.get_encrypted_data(data_record.ipfs_cid)
                
                # 解密数据
                user_key = self.cpabe_manager.deserialize_user_key(owner.cpabe_key)
                decrypted_data = self.cpabe_manager.decrypt(
                    self.public_key,
                    user_key,
                    encrypted_data["encrypted_data"]
                )
                
                # 使用解密后的数据
                data_str = decrypted_data
            else:
                # 使用新的数据
                if isinstance(data, dict) or isinstance(data, list):
                    data_str = json.dumps(data)
                else:
                    data_str = str(data)
            
            # 使用新的策略加密数据
            logger.info(f"Re-encrypting data with policy: {new_policy}")
            encrypted_data, _ = self.cpabe_manager.encrypt(self.public_key, data_str, new_policy)
            
            # 准备IPFS元数据
            ipfs_metadata = {
                "title": title or data_record.title,
                "description": description or data_record.description,
                "data_type": data_record.data_type,
                "owner_address": self.user_crud.get(owner_id).blockchain_address,
                "updated_at": datetime.now().isoformat(),
                "tags": tags or data_record.tags,
                "user_metadata": metadata or data_record.metadata
            }
            
            # 将加密数据上传到IPFS
            logger.info("Uploading updated encrypted data to IPFS")
            new_ipfs_cid = self.ipfs_client.add_encrypted_data(encrypted_data, ipfs_metadata)
            
            # 将数据固定到IPFS节点
            self.ipfs_client.pin_cid(new_ipfs_cid)
            
            # 更新记录中的IPFS CID和访问策略
            updates["ipfs_cid"] = new_ipfs_cid
            if access_policy is not None:
                updates["access_policy"] = new_policy
            
            # 在区块链上更新数据
            if self.data_registry and data_record.blockchain_data_id:
                try:
                    # 准备区块链访问策略
                    blockchain_policy = json.dumps({
                        "policy_type": "cp_abe",
                        "policy_string": new_policy,
                        "encryption_method": "CP-ABE BSW07"
                    })
                    
                    # 准备区块链元数据
                    blockchain_metadata = json.dumps({
                        "title": title or data_record.title,
                        "description": description or data_record.description,
                        "data_type": data_record.data_type,
                        "tags": tags or data_record.tags,
                        "ipfs_gateway_url": self.ipfs_client.get_gateway_url(new_ipfs_cid)
                    })
                    
                    # 将字符串转换为bytes32
                    blockchain_data_id = Web3.to_bytes(hexstr=data_record.blockchain_data_id)
                    
                    # 更新区块链上的数据资产
                    logger.info(f"Updating data asset on blockchain")
                    tx_hash = self.ethereum_client.send_contract_transaction(
                        self.data_registry,
                        "updateDataAsset",
                        blockchain_data_id,
                        new_ipfs_cid,
                        blockchain_policy,
                        blockchain_metadata
                    )
                    
                    updates["blockchain_tx_hash"] = tx_hash
                    logger.info(f"Data asset updated on blockchain with tx hash: {tx_hash}")
                except Exception as e:
                    logger.error(f"Failed to update data asset on blockchain: {str(e)}")
        
        # 更新数据库记录
        if updates and self.data_crud:
            updated_record = self.data_crud.update(data_record.id, updates)
            logger.info(f"Data record updated in database: {data_id}")
            return {
                "id": data_id,
                "db_id": updated_record.id,
                "owner_id": updated_record.owner_id,
                "title": updated_record.title,
                "description": updated_record.description,
                "data_type": updated_record.data_type,
                "ipfs_cid": updated_record.ipfs_cid,
                "access_policy": updated_record.access_policy,
                "blockchain_data_id": updated_record.blockchain_data_id,
                "blockchain_tx_hash": updated_record.blockchain_tx_hash,
                "tags": updated_record.tags,
                "metadata": updated_record.metadata,
                "updated_at": datetime.now().isoformat()
            }
        else:
            return {
                "id": data_id,
                "message": "No updates performed"
            }
    
    def revoke_data(self, owner_id: int, data_id: str) -> Dict:
        """
        撤销数据访问
        
        Args:
            owner_id: 数据拥有者ID
            data_id: 数据ID
            
        Returns:
            result: 操作结果
        """
        # 获取数据记录
        data_record = self.data_crud.get_by_data_id(data_id)
        if not data_record:
            raise ValueError(f"Data with ID {data_id} not found")
        
        # 验证拥有者
        if data_record.owner_id != owner_id:
            raise ValueError("You are not the owner of this data")
        
        # 在区块链上撤销数据
        if self.data_registry and data_record.blockchain_data_id:
            try:
                # 将字符串转换为bytes32
                blockchain_data_id = Web3.to_bytes(hexstr=data_record.blockchain_data_id)
                
                # 撤销数据资产
                logger.info(f"Revoking data asset on blockchain")
                tx_hash = self.ethereum_client.send_contract_transaction(
                    self.data_registry,
                    "revokeDataAsset",
                    blockchain_data_id
                )
                
                logger.info(f"Data asset revoked on blockchain with tx hash: {tx_hash}")
                
                # 更新数据库记录
                if self.data_crud:
                    updates = {
                        "is_revoked": True,
                        "revoked_at": datetime.now(),
                        "blockchain_tx_hash": tx_hash
                    }
                    self.data_crud.update(data_record.id, updates)
                
                return {
                    "id": data_id,
                    "status": "revoked",
                    "blockchain_tx_hash": tx_hash,
                    "revoked_at": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Failed to revoke data asset on blockchain: {str(e)}")
                raise
        else:
            # 仅在数据库中标记为已撤销
            if self.data_crud:
                updates = {
                    "is_revoked": True,
                    "revoked_at": datetime.now()
                }
                self.data_crud.update(data_record.id, updates)
            
            return {
                "id": data_id,
                "status": "revoked",
                "revoked_at": datetime.now().isoformat()
            }
    
    def get_user_data(self, user_id: int) -> List[Dict]:
        """
        获取用户拥有的数据列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            data_list: 数据列表
        """
        if not self.data_crud:
            return []
        
        # 获取用户拥有的数据
        data_records = self.data_crud.get_by_owner(user_id)
        
        # 转换为字典列表
        result = []
        for record in data_records:
            result.append({
                "id": record.data_id,
                "title": record.title,
                "description": record.description,
                "data_type": record.data_type,
                "ipfs_cid": record.ipfs_cid,
                "access_policy": record.access_policy,
                "blockchain_data_id": record.blockchain_data_id,
                "tags": record.tags,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None,
                "is_revoked": record.is_revoked,
                "revoked_at": record.revoked_at.isoformat() if record.revoked_at else None
            })
        
        return result