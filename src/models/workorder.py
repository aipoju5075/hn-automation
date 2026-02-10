"""工单数据模型"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class WorkOrder(BaseModel):
    """工单模型"""
    
    order_id: str = Field(..., description="工单ID")
    order_name: Optional[str] = Field(None, description="工单名称")
    sn_code: Optional[str] = Field(None, description="SN编码")
    brand: Optional[str] = Field(None, description="品牌")
    machine_type: Optional[str] = Field(None, description="机型")
    status: Optional[str] = Field(None, description="状态")
    customer_name: Optional[str] = Field(None, description="客户姓名")
    mobile: Optional[str] = Field(None, description="手机号")
    address: Optional[str] = Field(None, description="地址")
    agency: Optional[str] = Field(None, description="代理商")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "order_id": "WO202410080001",
                "order_name": "维修工单",
                "sn_code": "55A3DXX-A036819",
                "brand": "ASD",
                "status": "completed",
                "customer_name": "张三",
                "mobile": "13800138000"
            }
        }


class WorkOrderQueryResult(BaseModel):
    """工单查询结果"""
    
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页")
    page_size: int = Field(10, description="每页大小")
    orders: List[WorkOrder] = Field(default_factory=list, description="工单列表")
