import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from web3 import Web3

from core.blockchain.ethereum import EthereumClient
from app.config import settings
from db.crud.user import UserCrud
from db.crud.attribute import AttributeCrud

logger = logging.getLogger(__name__)

class AttributeService:
    """属性服务类，负责用户属性的管理和验证"""
    
    def __init__(
        self,
        ethereum_client: EthereumClient = None,
        user_crud: UserCrud = None,
        attribute_crud: AttributeCrud = None
    ):
        """
        初始化属性服务
        
        Args:
            ethereum_client: 以太坊客户端实例
            user_crud: 用户CRUD实例
            attribute_crud: 属性CRUD实例
        """
        self.ethereum_client = ethereum_client or EthereumClient()
        self.user_crud = user_crud
        self.attribute_crud = attribute_crud
        
        # 加载属性管理合约
        try:
            contract_address = settings.ATTRIBUTE_AUTHORITY_CONTRACT_ADDRESS
            abi_path = "core/blockchain/contracts/abi/AttributeAuthority.json"
            self.attribute_authority = self.ethereum_client.load_contract(contract_address, abi_path)
            logger.info(f"Loaded AttributeAuthority contract at {contract_address}")
        except Exception as e:
            logger.error(f"Failed to load AttributeAuthority contract: {str(e)}")
            self.attribute_authority = None
    
    def issue_attribute(
        self,
        issuer_id: int,
        user_id: int,
        name: str,
        value: str,
        expiration_days: int = 0,
        description: str = None
    ) -> Dict:
        """
        为用户颁发属性
        
        Args:
            issuer_id: 颁发者ID
            user_id: 用户ID
            name: 属性名称
            value: 属性值
            expiration_days: 过期天数，0表示永不过期
            description: 属性描述
            
        Returns:
            attribute: 颁发的属性信息
        """
        # 获取颁发者和用户信息
        issuer = self.user_crud.get(issuer_id)
        user = self.user_crud.get(user_id)
        
        if not issuer or not user:
            raise ValueError("Issuer or user not found")
        
        # 检查颁发者是否有权限
        if not issuer.is_admin and not issuer.is_issuer:
            raise ValueError("Issuer does not have required permissions")
        
        # 在区块链上颁发属性
        if self.attribute_authority:
            try:
                # 检查颁发者是否有ISSUER角色
                issuer_role = self.ethereum_client.call_contract_function(
                    self.attribute_authority,
                    "hasRole",
                    Web3.keccak(text="ISSUER_ROLE"),
                    issuer.blockchain_address
                )
                
                if not issuer_role:
                    raise ValueError("Issuer does not have ISSUER_ROLE on blockchain")
                
                # 颁发属性
                logger.info(f"Issuing attribute {name}={value} to user {user_id} on blockchain")
                tx_hash = self.ethereum_client.send_contract_transaction(
                    self.attribute_authority,
                    "issueAttribute",
                    user.blockchain_address,
                    name,
                    value,
                    expiration_days
                )
                
                # 等待交易确认
                receipt = self.ethereum_client.get_transaction_receipt(tx_hash)
                
                # 从事件日志中提取attributeId
                blockchain_attribute_id = None
                for log in receipt.get('logs', []):
                    # 解析AttributeIssued事件
                    # 事件定义: event AttributeIssued(address indexed user, bytes32 indexed attributeId, string name, string value, uint256 expiresAt)
                    if log.get('topics') and len(log.get('topics')) >= 3:
                        # 第二个主题是attributeId
                        blockchain_attribute_id = log.get('topics')[2].hex()
                        break
                
                logger.info(f"Attribute issued on blockchain with id: {blockchain_attribute_id}")
            except Exception as e:
                logger.error(f"Failed to issue attribute on blockchain: {str(e)}")
                blockchain_attribute_id = None
                tx_hash = None
        else:
            logger.warning("Attribute authority contract not available, skipping blockchain issuance")
            blockchain_attribute_id = None
            tx_hash = None
        
        # 计算过期时间
        if expiration_days > 0:
            expires_at = datetime.now().replace(microsecond=0) + timedelta(days=expiration_days)
        else:
            expires_at = None
        
        # 在数据库中保存属性记录
        attribute_record = {
            "user_id": user_id,
            "issuer_id": issuer_id,
            "name": name,
            "value": value,
            "description": description,
            "issued_at": datetime.now().replace(microsecond=0),
            "expires_at": expires_at,
            "blockchain_attribute_id": blockchain_attribute_id,
            "blockchain_tx_hash": tx_hash
        }
        
        # 保存到数据库
        if self.attribute_crud:
            db_attribute = self.attribute_crud.create(attribute_record)
            attribute_record["id"] = db_attribute.id
        
        logger.info(f"Attribute {name}={value} issued to user {user_id}")
        return attribute_record
    
    def revoke_attribute(
        self,
        revoker_id: int,
        attribute_id: int
    ) -> Dict:
        """
        撤销用户属性
        
        Args:
            revoker_id: 撤销者ID
            attribute_id: 属性ID
            
        Returns:
            result: 操作结果
        """
        # 获取撤销者信息和属性信息
        revoker = self.user_crud.get(revoker_id)
        attribute = self.attribute_crud.get(attribute_id)
        
        if not revoker or not attribute:
            raise ValueError("Revoker or attribute not found")
        
        # 检查撤销权限（只有属性颁发者或管理员可以撤销）
        if not revoker.is_admin and revoker_id != attribute.issuer_id:
            raise ValueError("Not authorized to revoke this attribute")
        
        # 在区块链上撤销属性
        if self.attribute_authority and attribute.blockchain_attribute_id:
            try:
                user = self.user_crud.get(attribute.user_id)
                if not user:
                    raise ValueError("User not found")
                
                # 撤销属性
                logger.info(f"Revoking attribute {attribute_id} on blockchain")
                tx_hash = self.ethereum_client.send_contract_transaction(
                    self.attribute_authority,
                    "revokeAttribute",
                    user.blockchain_address,
                    Web3.to_bytes(hexstr=attribute.blockchain_attribute_id)
                )
                
                logger.info(f"Attribute revoked on blockchain with tx hash: {tx_hash}")
            except Exception as e:
                logger.error(f"Failed to revoke attribute on blockchain: {str(e)}")
                tx_hash = None
        else:
            logger.warning("Attribute authority contract not available or attribute not on blockchain")
            tx_hash = None
        
        # 在数据库中更新属性状态
        updates = {
            "is_revoked": True,
            "revoked_at": datetime.now().replace(microsecond=0),
            "revoked_by": revoker_id
        }
        
        if tx_hash:
            updates["blockchain_tx_hash"] = tx_hash
        
        # 更新数据库记录
        if self.attribute_crud:
            self.attribute_crud.update(attribute_id, updates)
        
        logger.info(f"Attribute {attribute_id} revoked by user {revoker_id}")
        return {
            "id": attribute_id,
            "status": "revoked",
            "revoked_at": updates["revoked_at"].isoformat(),
            "revoked_by": revoker_id,
            "blockchain_tx_hash": tx_hash
        }
    
    def validate_attribute(
        self,
        user_id: int,
        name: str,
        value: str = None
    ) -> Dict:
        """
        验证用户是否拥有有效的属性
        
        Args:
            user_id: 用户ID
            name: 属性名称
            value: 属性值（可选，如果不提供则只检查属性名称）
            
        Returns:
            result: 验证结果
        """
        # 获取用户信息
        user = self.user_crud.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # 在数据库中查找属性
        if self.attribute_crud:
            attributes = self.attribute_crud.get_by_user_and_name(user_id, name)
            
            # 如果提供了属性值，则筛选匹配的属性
            if value is not None:
                attributes = [attr for attr in attributes if attr.value == value]
            
            # 检查是否有有效的属性（未撤销且未过期）
            valid_attributes = []
            for attr in attributes:
                if attr.is_revoked:
                    continue
                
                if attr.expires_at and attr.expires_at < datetime.now():
                    continue
                
                valid_attributes.append(attr)
            
            if valid_attributes:
                # 找到有效的属性
                return {
                    "valid": True,
                    "attributes": [
                        {
                            "id": attr.id,
                            "name": attr.name,
                            "value": attr.value,
                            "issued_at": attr.issued_at.isoformat() if attr.issued_at else None,
                            "expires_at": attr.expires_at.isoformat() if attr.expires_at else None
                        }
                        for attr in valid_attributes
                    ]
                }
        
        # 如果没有找到有效的属性，尝试在区块链上验证
        if self.attribute_authority and user.blockchain_address:
            try:
                # 在区块链上验证属性
                has_attribute = self.ethereum_client.call_contract_function(
                    self.attribute_authority,
                    "hasAttribute",
                    user.blockchain_address,
                    name,
                    value or ""  # 如果value为None，使用空字符串
                )
                
                if has_attribute:
                    return {
                        "valid": True,
                        "source": "blockchain",
                        "message": "Attribute validated on blockchain"
                    }
            except Exception as e:
                logger.error(f"Failed to validate attribute on blockchain: {str(e)}")
        
        # 未找到有效属性
        return {
            "valid": False,
            "message": f"User does not have a valid attribute: {name}={value or '*'}"
        }
    
    def get_user_attributes(self, user_id: int) -> List[Dict]:
        """
        获取用户的所有属性
        
        Args:
            user_id: 用户ID
            
        Returns:
            attributes: 属性列表
        """
        result = []
        
        # 获取用户信息
        user = self.user_crud.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # 从数据库获取属性
        if self.attribute_crud:
            db_attributes = self.attribute_crud.get_by_user(user_id)
            
            for attr in db_attributes:
                # 检查属性是否过期
                is_expired = False
                if attr.expires_at and attr.expires_at < datetime.now():
                    is_expired = True
                
                result.append({
                    "id": attr.id,
                    "name": attr.name,
                    "value": attr.value,
                    "description": attr.description,
                    "issued_at": attr.issued_at.isoformat() if attr.issued_at else None,
                    "expires_at": attr.expires_at.isoformat() if attr.expires_at else None,
                    "is_revoked": attr.is_revoked,
                    "is_expired": is_expired,
                    "blockchain_attribute_id": attr.blockchain_attribute_id
                })
        
        # 如果有区块链合约，尝试获取区块链上的属性
        if self.attribute_authority and user.blockchain_address:
            try:
                # 获取区块链上的属性数量
                attr_count = self.ethereum_client.call_contract_function(
                    self.attribute_authority,
                    "getUserAttributeCount",
                    user.blockchain_address
                )
                
                # 获取每个属性ID
                blockchain_attrs = []
                for i in range(attr_count):
                    attr_id = self.ethereum_client.call_contract_function(
                        self.attribute_authority,
                        "getUserAttributeIdAt",
                        user.blockchain_address,
                        i
                    )
                    
                    # 获取属性详情
                    attr_details = self.ethereum_client.call_contract_function(
                        self.attribute_authority,
                        "getAttribute",
                        user.blockchain_address,
                        attr_id
                    )
                    
                    # 检查属性是否已存在于结果中
                    blockchain_attr_id = attr_id.hex()
                    exists = False
                    for attr in result:
                        if attr.get("blockchain_attribute_id") == blockchain_attr_id:
                            exists = True
                            break
                    
                    if not exists:
                        blockchain_attrs.append({
                            "id": None,  # 数据库ID未知
                            "name": attr_details[0],  # name
                            "value": attr_details[1],  # value
                            "description": None,
                            "issued_at": datetime.fromtimestamp(attr_details[2]).isoformat(),  # issuedAt
                            "expires_at": datetime.fromtimestamp(attr_details[3]).isoformat() if attr_details[3] > 0 else None,  # expiresAt
                            "is_revoked": attr_details[5],  # isRevoked
                            "is_expired": attr_details[3] > 0 and attr_details[3] < datetime.now().timestamp(),
                            "blockchain_attribute_id": blockchain_attr_id,
                            "source": "blockchain"
                        })
                
                # 添加区块链属性到结果
                result.extend(blockchain_attrs)
            except Exception as e:
                logger.error(f"Failed to get attributes from blockchain: {str(e)}")
        
        return result
    
    def get_valid_user_attributes(self, user_id: int) -> List[Dict]:
        """
        获取用户的所有有效属性（未撤销且未过期）
        
        Args:
            user_id: 用户ID
            
        Returns:
            attributes: 有效属性列表
        """
        all_attributes = self.get_user_attributes(user_id)
        
        # 筛选有效属性
        valid_attributes = []
        for attr in all_attributes:
            if attr["is_revoked"] or attr["is_expired"]:
                continue
            valid_attributes.append(attr)
        
        return valid_attributes
    
    def get_attribute_values(self, user_id: int) -> Dict[str, List[str]]:
        """
        获取用户的所有有效属性值，按属性名组织
        
        Args:
            user_id: 用户ID
            
        Returns:
            attribute_values: 属性值字典，键为属性名，值为属性值列表
        """
        valid_attributes = self.get_valid_user_attributes(user_id)
        
        # 按属性名组织属性值
        result = {}
        for attr in valid_attributes:
            name = attr["name"]
            value = attr["value"]
            
            if name not in result:
                result[name] = []
            
            if value not in result[name]:
                result[name].append(value)
        
        return result