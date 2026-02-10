"""SN记录数据模型"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ProductType(str, Enum):
    """产品类型"""
    USER_MACHINE = "user_machine"      # 用户机
    USER_BOARD = "user_board"          # 用户板


class SNRecord(BaseModel):
    """SN记录模型"""
    
    sn_code: str = Field(..., description="SN编码")
    product_type: ProductType = Field(..., description="产品类型")
    order_no: Optional[str] = Field(None, description="订单号")
    customer_name: Optional[str] = Field(None, description="客户姓名")
    status: Optional[str] = Field(None, description="状态")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    
    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "sn_code": "55A3DXX-A036819",
                "product_type": "user_machine",
                "order_no": "SO20241008123000",
                "customer_name": "张三",
                "status": "completed"
            }
        }


class PickingRecord(BaseModel):
    """拣货记录模型"""
    
    sn_code: str = Field(..., description="SN编码")
    so_no: str = Field(..., description="出库单号")
    success: bool = Field(False, description="是否成功")
    message: Optional[str] = Field(None, description="操作消息")
    picked_at: Optional[datetime] = Field(None, description="拣货时间")


class ShippingRecord(BaseModel):
    """发货记录模型"""
    
    sn_code: str = Field(..., description="SN编码")
    so_no: str = Field(..., description="出库单号")
    customer_name: Optional[str] = Field(None, description="客户姓名")
    is_self_pickup: bool = Field(False, description="是否自提")
    tracking_no: Optional[str] = Field(None, description="快递单号")
    carrier: Optional[str] = Field(None, description="承运商")
    success: bool = Field(False, description="是否成功")
    message: Optional[str] = Field(None, description="操作消息")
    shipped_at: Optional[datetime] = Field(None, description="发货时间")
