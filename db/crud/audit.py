from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func
from datetime import datetime

from app.api.models.audit import AuditLog
from app.api.models.data import DataAccessLog

class AuditCrud:
    """审计日志CRUD操作类"""
    
    def __init__(self, db: Session):
        """
        初始化
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def create_audit_log(self, log_data: Dict[str, Any]) -> AuditLog:
        """
        创建审计日志
        
        Args:
            log_data: 日志数据
            
        Returns:
            AuditLog: 创建的审计日志对象
        """
        db_log = AuditLog(**log_data)
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return db_log
    
    def create_data_access_log(self, log_data: Dict[str, Any]) -> DataAccessLog:
        """
        创建数据访问日志
        
        Args:
            log_data: 日志数据
            
        Returns:
            DataAccessLog: 创建的数据访问日志对象
        """
        db_log = DataAccessLog(**log_data)
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return db_log
    
    def get_audit_log(self, log_id: int) -> Optional[AuditLog]:
        """
        获取审计日志
        
        Args:
            log_id: 日志ID
            
        Returns:
            AuditLog: 审计日志对象，如果不存在则为None
        """
        return self.db.query(AuditLog).filter(AuditLog.id == log_id).first()
    
    def get_data_access_log(self, log_id: int) -> Optional[DataAccessLog]:
        """
        获取数据访问日志
        
        Args:
            log_id: 日志ID
            
        Returns:
            DataAccessLog: 数据访问日志对象，如果不存在则为None
        """
        return self.db.query(DataAccessLog).filter(DataAccessLog.id == log_id).first()
    
    def get_audit_logs(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        user_id: int = None,
        action_type: str = None,
        resource_type: str = None,
        resource_id: str = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        获取审计日志列表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户ID
            action_type: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            skip: 跳过的数量
            limit: 限制的数量
            
        Returns:
            List[AuditLog]: 审计日志对象列表
        """
        query = self.db.query(AuditLog)
        
        # 过滤条件
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if action_type:
            query = query.filter(AuditLog.action_type == action_type)
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        
        # 排序和分页
        query = query.order_by(desc(AuditLog.timestamp))
        
        return query.offset(skip).limit(limit).all()
    
    def get_data_access_logs(
        self,
        data_id: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        user_id: int = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[DataAccessLog]:
        """
        获取数据访问日志列表
        
        Args:
            data_id: 数据ID
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户ID
            skip: 跳过的数量
            limit: 限制的数量
            
        Returns:
            List[DataAccessLog]: 数据访问日志对象列表
        """
        query = self.db.query(DataAccessLog)
        
        # 过滤条件
        if data_id:
            query = query.filter(DataAccessLog.data_id == data_id)
        
        if start_date:
            query = query.filter(DataAccessLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(DataAccessLog.timestamp <= end_date)
        
        if user_id:
            query = query.filter(DataAccessLog.user_id == user_id)
        
        # 排序和分页
        query = query.order_by(desc(DataAccessLog.timestamp))
        
        return query.offset(skip).limit(limit).all()
    
    def count_audit_logs(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        user_id: int = None,
        action_type: str = None,
        resource_type: str = None
    ) -> int:
        """
        统计审计日志数量
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户ID
            action_type: 操作类型
            resource_type: 资源类型
            
        Returns:
            int: 日志数量
        """
        query = self.db.query(func.count(AuditLog.id))
        
        # 过滤条件
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if action_type:
            query = query.filter(AuditLog.action_type == action_type)
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        return query.scalar()
    
    def count_data_access_logs(
        self,
        data_id: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        user_id: int = None
    ) -> int:
        """
        统计数据访问日志数量
        
        Args:
            data_id: 数据ID
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户ID
            
        Returns:
            int: 日志数量
        """
        query = self.db.query(func.count(DataAccessLog.id))
        
        # 过滤条件
        if data_id:
            query = query.filter(DataAccessLog.data_id == data_id)
        
        if start_date:
            query = query.filter(DataAccessLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(DataAccessLog.timestamp <= end_date)
        
        if user_id:
            query = query.filter(DataAccessLog.user_id == user_id)
        
        return query.scalar()
    
    def get_user_data_access_logs(
        self,
        user_id: int,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[DataAccessLog]:
        """
        获取用户的数据访问日志
        
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[DataAccessLog]: 数据访问日志对象列表
        """
        query = self.db.query(DataAccessLog).filter(DataAccessLog.user_id == user_id)
        
        # 过滤条件
        if start_date:
            query = query.filter(DataAccessLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(DataAccessLog.timestamp <= end_date)
        
        # 排序
        query = query.order_by(desc(DataAccessLog.timestamp))
        
        return query.all()
    
    def get_user_action_counts(self, user_id: int) -> Dict[str, int]:
        """
        获取用户操作类型计数
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, int]: 操作类型计数字典
        """
        result = {}
        
        counts = self.db.query(
            AuditLog.action_type,
            func.count(AuditLog.id).label("count")
        ).filter(
            AuditLog.user_id == user_id
        ).group_by(
            AuditLog.action_type
        ).all()
        
        for action_type, count in counts:
            result[action_type] = count
        
        return result
    
    def get_resource_type_counts(self) -> Dict[str, int]:
        """
        获取资源类型计数
        
        Returns:
            Dict[str, int]: 资源类型计数字典
        """
        result = {}
        
        counts = self.db.query(
            AuditLog.resource_type,
            func.count(AuditLog.id).label("count")
        ).group_by(
            AuditLog.resource_type
        ).all()
        
        for resource_type, count in counts:
            result[resource_type] = count
        
        return result
    
    def get_recent_logs(self, limit: int = 10) -> List[AuditLog]:
        """
        获取最近的审计日志
        
        Args:
            limit: 限制的数量
            
        Returns:
            List[AuditLog]: 审计日志对象列表
        """
        return self.db.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit).all()
    
    def get_recent_access_logs(self, limit: int = 10) -> List[DataAccessLog]:
        """
        获取最近的数据访问日志
        
        Args:
            limit: 限制的数量
            
        Returns:
            List[DataAccessLog]: 数据访问日志对象列表
        """
        return self.db.query(DataAccessLog).order_by(desc(DataAccessLog.timestamp)).limit(limit).all()