from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func
from datetime import datetime

from app.api.models.data import Data, DataAccessLog

class DataCrud:
    """数据资产CRUD操作类"""
    
    def __init__(self, db: Session):
        """
        初始化
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def get(self, data_id: int) -> Optional[Data]:
        """
        通过ID获取数据
        
        Args:
            data_id: 数据ID（数据库主键）
            
        Returns:
            Data: 数据对象，如果不存在则为None
        """
        return self.db.query(Data).filter(Data.id == data_id).first()
    
    def get_by_data_id(self, data_id: str) -> Optional[Data]:
        """
        通过数据ID获取数据
        
        Args:
            data_id: 数据ID（UUID）
            
        Returns:
            Data: 数据对象，如果不存在则为None
        """
        return self.db.query(Data).filter(Data.data_id == data_id).first()
    
    def get_by_owner(self, owner_id: int) -> List[Data]:
        """
        获取所有者的所有数据
        
        Args:
            owner_id: 所有者ID
            
        Returns:
            List[Data]: 数据对象列表
        """
        return self.db.query(Data).filter(Data.owner_id == owner_id).all()
    
    def get_active_by_owner(self, owner_id: int) -> List[Data]:
        """
        获取所有者的所有未撤销数据
        
        Args:
            owner_id: 所有者ID
            
        Returns:
            List[Data]: 数据对象列表
        """
        return self.db.query(Data).filter(
            Data.owner_id == owner_id,
            Data.is_revoked == False
        ).all()
    
    def create(self, data: Dict[str, Any]) -> Data:
        """
        创建数据
        
        Args:
            data: 数据字典
            
        Returns:
            Data: 创建的数据对象
        """
        db_data = Data(**data)
        self.db.add(db_data)
        self.db.commit()
        self.db.refresh(db_data)
        return db_data
    
    def update(self, data_id: int, data: Dict[str, Any]) -> Data:
        """
        更新数据
        
        Args:
            data_id: 数据ID（数据库主键）
            data: 数据字典
            
        Returns:
            Data: 更新后的数据对象
        """
        db_data = self.get(data_id)
        if not db_data:
            raise ValueError(f"Data with ID {data_id} not found")
        
        for key, value in data.items():
            setattr(db_data, key, value)
        
        self.db.commit()
        self.db.refresh(db_data)
        return db_data
    
    def delete(self, data_id: int) -> bool:
        """
        删除数据
        
        Args:
            data_id: 数据ID（数据库主键）
            
        Returns:
            bool: 是否成功删除
        """
        db_data = self.get(data_id)
        if not db_data:
            return False
        
        self.db.delete(db_data)
        self.db.commit()
        return True
    
    def search_data(self, 
                    query: str = None, 
                    data_type: str = None, 
                    tags: List[str] = None, 
                    owner_id: int = None,
                    skip: int = 0,
                    limit: int = 100) -> List[Data]:
        """
        搜索数据
        
        Args:
            query: 搜索查询
            data_type: 数据类型
            tags: 标签列表
            owner_id: 所有者ID
            skip: 跳过的数量
            limit: 限制的数量
            
        Returns:
            List[Data]: 数据对象列表
        """
        search_query = self.db.query(Data).filter(Data.is_revoked == False)
        
        # 按标题或描述搜索
        if query:
            search_query = search_query.filter(
                or_(
                    Data.title.ilike(f"%{query}%"),
                    Data.description.ilike(f"%{query}%")
                )
            )
        
        # 按数据类型过滤
        if data_type:
            search_query = search_query.filter(Data.data_type == data_type)
        
        # 按标签过滤
        if tags:
            for tag in tags:
                search_query = search_query.filter(Data.tags.contains([tag]))
        
        # 按所有者过滤
        if owner_id:
            search_query = search_query.filter(Data.owner_id == owner_id)
        
        # 分页
        return search_query.offset(skip).limit(limit).all()
    
    def log_access(self, log_data: Dict[str, Any]) -> DataAccessLog:
        """
        记录数据访问
        
        Args:
            log_data: 访问日志数据
            
        Returns:
            DataAccessLog: 创建的访问日志对象
        """
        db_log = DataAccessLog(**log_data)
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return db_log
    
    def get_access_logs(self, data_id: str) -> List[DataAccessLog]:
        """
        获取数据访问日志
        
        Args:
            data_id: 数据ID（UUID）
            
        Returns:
            List[DataAccessLog]: 访问日志对象列表
        """
        return self.db.query(DataAccessLog).filter(DataAccessLog.data_id == data_id).all()
    
    def get_user_access_logs(self, user_id: int) -> List[DataAccessLog]:
        """
        获取用户访问日志
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[DataAccessLog]: 访问日志对象列表
        """
        return self.db.query(DataAccessLog).filter(DataAccessLog.user_id == user_id).all()
    
    def count_by_owner(self, owner_id: int) -> int:
        """
        统计所有者的数据数量
        
        Args:
            owner_id: 所有者ID
            
        Returns:
            int: 数据数量
        """
        return self.db.query(Data).filter(Data.owner_id == owner_id).count()
    
    def count_access_logs(self, data_id: str) -> int:
        """
        统计数据访问日志数量
        
        Args:
            data_id: 数据ID（UUID）
            
        Returns:
            int: 访问日志数量
        """
        return self.db.query(DataAccessLog).filter(DataAccessLog.data_id == data_id).count()
    
    def get_by_blockchain_id(self, blockchain_data_id: str) -> Optional[Data]:
        """
        通过区块链数据ID获取数据
        
        Args:
            blockchain_data_id: 区块链数据ID
            
        Returns:
            Data: 数据对象，如果不存在则为None
        """
        return self.db.query(Data).filter(Data.blockchain_data_id == blockchain_data_id).first()
    
    def get_data_by_tag(self, tag: str) -> List[Data]:
        """
        通过标签获取数据
        
        Args:
            tag: 标签
            
        Returns:
            List[Data]: 数据对象列表
        """
        return self.db.query(Data).filter(
            Data.tags.contains([tag]),
            Data.is_revoked == False
        ).all()
    
    def get_top_data_types(self) -> List[Tuple[str, int]]:
        """
        获取排名靠前的数据类型
        
        Returns:
            List[Tuple[str, int]]: 数据类型和数量的元组列表
        """
        return self.db.query(
            Data.data_type,
            func.count(Data.id).label("count")
        ).group_by(Data.data_type).order_by(desc("count")).all()