import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from web3 import Web3

from core.blockchain.ethereum import EthereumClient
from app.config import settings
from db.crud.audit import AuditCrud
from db.crud.data import DataCrud
from db.crud.user import UserCrud

logger = logging.getLogger(__name__)

class AuditService:
    """审计服务类，负责日志记录和审计查询"""
    
    def __init__(
        self,
        ethereum_client: EthereumClient = None,
        audit_crud: AuditCrud = None,
        data_crud: DataCrud = None,
        user_crud: UserCrud = None
    ):
        """
        初始化审计服务
        
        Args:
            ethereum_client: 以太坊客户端实例
            audit_crud: 审计CRUD实例
            data_crud: 数据CRUD实例
            user_crud: 用户CRUD实例
        """
        self.ethereum_client = ethereum_client
        self.audit_crud = audit_crud
        self.data_crud = data_crud
        self.user_crud = user_crud
        
        # 加载数据注册合约
        try:
            contract_address = settings.DATA_REGISTRY_CONTRACT_ADDRESS
            abi_path = "core/blockchain/contracts/abi/DataRegistry.json"
            self.data_registry = self.ethereum_client.load_contract(contract_address, abi_path)
            logger.info(f"Loaded DataRegistry contract at {contract_address}")
        except Exception as e:
            logger.error(f"Failed to load DataRegistry contract: {str(e)}")
            self.data_registry = None
    
    def log_action(
        self,
        user_id: int,
        action_type: str,
        resource_type: str,
        resource_id: str = None,
        details: Dict = None,
        ip_address: str = None,
        user_agent: str = None,
        request_id: str = None
    ) -> Dict:
        """
        记录用户操作
        
        Args:
            user_id: 用户ID
            action_type: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            details: 详细信息
            ip_address: IP地址
            user_agent: 用户代理
            request_id: 请求ID
            
        Returns:
            log: 日志记录
        """
        # 准备日志数据
        log_data = {
            "user_id": user_id,
            "action_type": action_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
            "request_id": request_id,
            "timestamp": datetime.now()
        }
        
        # 记录日志
        if self.audit_crud:
            log = self.audit_crud.create_audit_log(log_data)
            logger.info(f"Audit log created: {action_type} on {resource_type} by user {user_id}")
            return log
        else:
            # 如果没有审计CRUD实例，只记录到日志系统
            logger.info(f"Audit log (no DB): {action_type} on {resource_type} by user {user_id}")
            return log_data
    
    def log_data_access(
        self,
        user_id: int,
        data_id: str,
        purpose: str = None,
        is_successful: bool = True,
        error_message: str = None,
        ip_address: str = None,
        user_agent: str = None,
        blockchain_tx_hash: str = None
    ) -> Dict:
        """
        记录数据访问
        
        Args:
            user_id: 用户ID
            data_id: 数据ID
            purpose: 访问目的
            is_successful: 是否成功
            error_message: 错误消息
            ip_address: IP地址
            user_agent: 用户代理
            blockchain_tx_hash: 区块链交易哈希
            
        Returns:
            log: 访问日志记录
        """
        # 准备日志数据
        log_data = {
            "user_id": user_id,
            "data_id": data_id,
            "purpose": purpose,
            "is_successful": is_successful,
            "error_message": error_message,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "blockchain_tx_hash": blockchain_tx_hash,
            "timestamp": datetime.now()
        }
        
        # 记录日志
        if self.audit_crud:
            log = self.audit_crud.create_data_access_log(log_data)
            logger.info(f"Data access log created: {data_id} by user {user_id}, status: {'success' if is_successful else 'failed'}")
            return log
        else:
            # 如果没有审计CRUD实例，只记录到日志系统
            logger.info(f"Data access log (no DB): {data_id} by user {user_id}, status: {'success' if is_successful else 'failed'}")
            return log_data
    
    def get_audit_logs(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        user_id: int = None,
        action_type: str = None,
        resource_type: str = None,
        resource_id: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[Dict]:
        """
        获取审计日志
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户ID
            action_type: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            page: 页码
            page_size: 每页大小
            
        Returns:
            logs: 日志列表
        """
        if not self.audit_crud:
            return []
        
        # 计算分页参数
        skip = (page - 1) * page_size
        
        # 查询日志
        logs = self.audit_crud.get_audit_logs(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            skip=skip,
            limit=page_size
        )
        
        # 转换为字典列表
        result = []
        for log in logs:
            log_dict = log.__dict__.copy()
            
            # 添加用户名
            if log.user_id and self.user_crud:
                user = self.user_crud.get(log.user_id)
                if user:
                    log_dict["username"] = user.username
            
            result.append(log_dict)
        
        return result
    
    def get_data_access_logs(
        self,
        data_id: str,
        start_date: datetime = None,
        end_date: datetime = None,
        user_id: int = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[Dict]:
        """
        获取数据访问日志
        
        Args:
            data_id: 数据ID
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户ID
            page: 页码
            page_size: 每页大小
            
        Returns:
            logs: 日志列表
        """
        if not self.audit_crud:
            return []
        
        # 计算分页参数
        skip = (page - 1) * page_size
        
        # 查询日志
        logs = self.audit_crud.get_data_access_logs(
            data_id=data_id,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            skip=skip,
            limit=page_size
        )
        
        # 转换为字典列表
        result = []
        for log in logs:
            log_dict = log.__dict__.copy()
            
            # 添加用户名
            if log.user_id and self.user_crud:
                user = self.user_crud.get(log.user_id)
                if user:
                    log_dict["username"] = user.username
            
            result.append(log_dict)
        
        return result
    
    def get_blockchain_access_logs(self, data_id: str) -> List[Dict]:
        """
        获取区块链上的数据访问日志
        
        Args:
            data_id: 数据ID
            
        Returns:
            logs: 日志列表
        """
        result = []
        
        # 获取数据记录
        if not self.data_crud:
            return result
        
        data = self.data_crud.get_by_data_id(data_id)
        if not data or not data.blockchain_data_id:
            return result
        
        # 如果合约不可用，返回空列表
        if not self.data_registry:
            return result
        
        try:
            # 将字符串转换为bytes32
            blockchain_data_id = Web3.to_bytes(hexstr=data.blockchain_data_id)
            
            # 获取访问记录数量
            record_count = self.ethereum_client.call_contract_function(
                self.data_registry,
                "getAccessRecordCount",
                blockchain_data_id
            )
            
            # 获取每条访问记录
            for i in range(record_count):
                # 获取记录详情
                record = self.ethereum_client.call_contract_function(
                    self.data_registry,
                    "getAccessRecordAt",
                    blockchain_data_id,
                    i
                )
                
                # 添加到结果
                result.append({
                    "user_address": record[0],
                    "timestamp": datetime.fromtimestamp(record[1]).isoformat(),
                    "purpose": record[2],
                    "index": i
                })
            
            return result
        except Exception as e:
            logger.error(f"Failed to get blockchain access logs: {str(e)}")
            return []
    
    def check_data_ownership(self, data_id: str, user_id: int) -> bool:
        """
        检查用户是否是数据的拥有者
        
        Args:
            data_id: 数据ID
            user_id: 用户ID
            
        Returns:
            is_owner: 是否是拥有者
        """
        if not self.data_crud:
            return False
        
        # 获取数据记录
        data = self.data_crud.get_by_data_id(data_id)
        
        # 检查数据是否存在且用户是否是拥有者
        return data is not None and data.owner_id == user_id
    
    def get_user_activity(
        self,
        user_id: int,
        start_date: datetime = None,
        end_date: datetime = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        获取用户活动统计
        
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            page: 页码
            page_size: 每页大小
            
        Returns:
            activity: 活动统计
        """
        if not self.audit_crud:
            return {
                "logs": [],
                "summary": {
                    "total": 0,
                    "by_action": {},
                    "by_resource": {}
                }
            }
        
        # 获取审计日志
        logs = self.get_audit_logs(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )
        
        # 获取数据访问日志
        access_logs = self.audit_crud.get_user_data_access_logs(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # 计算统计信息
        total_actions = len(logs)
        total_access = len(access_logs)
        
        # 按操作类型分组
        action_types = {}
        for log in logs:
            action = log.get("action_type")
            action_types[action] = action_types.get(action, 0) + 1
        
        # 按资源类型分组
        resource_types = {}
        for log in logs:
            resource = log.get("resource_type")
            resource_types[resource] = resource_types.get(resource, 0) + 1
        
        # 数据访问成功率
        success_count = sum(1 for log in access_logs if log.is_successful)
        success_rate = (success_count / total_access) * 100 if total_access > 0 else 0
        
        # 返回活动统计
        return {
            "logs": logs,
            "summary": {
                "total_actions": total_actions,
                "total_data_access": total_access,
                "success_rate": success_rate,
                "by_action": action_types,
                "by_resource": resource_types
            }
        }