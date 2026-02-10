"""发货处理器"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
from dateutil.relativedelta import relativedelta

from ..auth.logistics import LogisticsAuth
from ..models.sn_record import ShippingRecord

logger = logging.getLogger(__name__)


class ShippingProcessor:
    """发货处理器"""
    
    def __init__(
        self,
        auth: LogisticsAuth,
        self_pickup_staff: Optional[List[str]] = None
    ):
        """
        初始化发货处理器
        
        Args:
            auth: 物流系统认证器
            self_pickup_staff: 自提人员名单
        """
        self.auth = auth
        self.self_pickup_staff = set(self_pickup_staff or [])
    
    def get_pending_shipments(
        self,
        days_back: int = 29
    ) -> List[Dict[str, Any]]:
        """
        获取待发货数据
        
        Args:
            days_back: 查询天数范围
            
        Returns:
            待发货数据列表
        """
        # 计算时间范围
        now = datetime.now()
        end_time = datetime(now.year, now.month, now.day, 23, 59, 29)
        start_time = (now - relativedelta(days=days_back)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        all_records = []
        current_page = 1
        
        while True:
            params = self._build_query_params(start_time, end_time, current_page)
            
            try:
                # 先获取总数概况
                collect_url = "/wms-web/oubweb/outboundSoController/collectSoOrderGroupByStatus.shtml"
                self.auth.post(collect_url, data=params)
                
                # 获取列表数据
                query_url = "/wms-web/oubweb/outboundSoController/query.shtml"
                query_string = urlencode(params)
                full_url = f"{query_url}?{query_string}"
                
                response = self.auth.get(full_url)
                result = response.json()
                
                rows = result.get("rows", [])
                if not rows:
                    break
                
                all_records.extend(rows)
                current_page += 1
                
                # 安全限制
                if current_page > 100:
                    logger.warning("查询页数超过100，可能存在数据异常")
                    break
                    
            except Exception as e:
                logger.error(f"获取待发货数据失败: {e}")
                break
        
        logger.info(f"获取到 {len(all_records)} 条待发货记录")
        return all_records
    
    def _build_query_params(
        self,
        start_time: datetime,
        end_time: datetime,
        page: int
    ) -> Dict[str, str]:
        """构建查询参数"""
        return {
            "soNo": "",
            "workOrderNo": "",
            "omsOrderNo": "",
            "soType": "",
            "orderTimeFm": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "orderTimeTo": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "skuBrand": "",
            "tpyeCode": "",
            "ownerName": "",
            "ownerCode": "",
            "skuName": "",
            "skuCode": "",
            "logisticNo": "",
            "carrierName": "",
            "carrierCode": "",
            "shipperWh": "",
            "lotAtt13": "",
            "printStatus": "",
            "pickNo": "",
            "status": "00,10,20,30,40,50,60,70,80",
            "page.currentPage": str(page),
            "page.limitCount": "10",
            "wsdStatus": "60,70,50"
        }
    
    def ship(
        self,
        row_data: Dict[str, Any],
        customer_name: Optional[str] = None
    ) -> ShippingRecord:
        """
        执行发货
        
        Args:
            row_data: 发货数据行
            customer_name: 客户姓名
            
        Returns:
            发货记录
        """
        sn_code = row_data.get("invSn", "")
        so_no = row_data.get("soNo", "")
        
        record = ShippingRecord(
            sn_code=sn_code,
            so_no=so_no,
            customer_name=customer_name,
            success=False
        )
        
        try:
            # 判断是否自提
            is_self_pickup = customer_name in self.self_pickup_staff
            record.is_self_pickup = is_self_pickup
            
            # 构建VAS数据
            if is_self_pickup:
                # 自提 - 无快递信息
                vas_data = self._build_self_pickup_vas(so_no)
                record.message = f"自提: {customer_name}"
            else:
                # 外发 - 需要快递单号（暂时留空）
                vas_data = self._build_shipping_vas(so_no, "", "")
                record.message = f"外发: {customer_name or '未知'}"
            
            # 准备行数据
            row_copy = row_data.copy()
            row_copy["id"] = "1"
            row_copy["rowId"] = "1"
            row_copy["_index"] = "1"
            
            # 执行发货请求
            url = "/wms-web/oubweb/outboundShippmentController/shipmentByAllocListNew.shtml"
            data = {
                "vasSave": json.dumps(vas_data),
                "allocDetails": json.dumps([row_copy]),
                "allocateInWh": '""',
                "soNos": ""
            }
            
            response = self.auth.post(url, data=data)
            result = response.json()
            
            if result.get("success", False):
                record.success = True
                record.shipped_at = datetime.now()
                logger.info(f"SN {sn_code} 发货成功")
            else:
                record.message = f"发货失败: {result.get('msg', '未知错误')}"
                logger.warning(f"SN {sn_code} 发货失败: {result}")
                
        except Exception as e:
            record.message = f"发货异常: {str(e)}"
            logger.error(f"SN {sn_code} 发货异常: {e}")
        
        return record
    
    def ship_batch(
        self,
        records: List[Dict[str, Any]],
        customer_name_map: Optional[Dict[str, str]] = None
    ) -> List[ShippingRecord]:
        """
        批量发货
        
        Args:
            records: 发货数据列表
            customer_name_map: SN到客户姓名的映射
            
        Returns:
            发货记录列表
        """
        results = []
        total = len(records)
        name_map = customer_name_map or {}
        
        for idx, row in enumerate(records, 1):
            sn_code = row.get("invSn", "")
            customer_name = name_map.get(sn_code)
            
            logger.info(f"[{idx}/{total}] 处理发货: {sn_code}")
            record = self.ship(row, customer_name)
            results.append(record)
        
        # 统计
        success_count = sum(1 for r in results if r.success)
        self_pickup_count = sum(1 for r in results if r.is_self_pickup and r.success)
        shipping_count = success_count - self_pickup_count
        
        logger.info(
            f"批量发货完成: {success_count}/{total} 成功 "
            f"(自提: {self_pickup_count}, 外发: {shipping_count})"
        )
        
        return results
    
    def _build_self_pickup_vas(self, so_no: str) -> List[Dict[str, Any]]:
        """构建自提VAS数据"""
        return [{
            "tpType": "3",
            "carrierName": "",
            "carrierCode": "",
            "allocateInWhNames": None,
            "transitWarehouse": None,
            "cttaName": None,
            "logisticType": None,
            "def1": None,
            "weight": None,
            "cubic": None,
            "insuredValue": None,
            "contactTel": None,
            "tpNo": None,
            "packageNo": None,
            "snCode": None,
            "soNo": so_no
        }]
    
    def _build_shipping_vas(
        self,
        so_no: str,
        tracking_no: str,
        carrier: str
    ) -> List[Dict[str, Any]]:
        """构建外发VAS数据"""
        carrier_map = {
            "顺丰速运": "shunfeng",
            "": ""
        }
        
        return [{
            "tpType": "0",
            "carrierName": carrier or "顺丰速运",
            "carrierCode": carrier_map.get(carrier, "shunfeng"),
            "allocateInWhNames": None,
            "transitWarehouse": None,
            "cttaName": None,
            "logisticType": None,
            "def1": None,
            "weight": None,
            "cubic": None,
            "insuredValue": None,
            "contactTel": None,
            "tpNo": tracking_no,
            "packageNo": None,
            "snCode": None,
            "soNo": so_no
        }]
