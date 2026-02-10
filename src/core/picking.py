"""拣货处理器"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any

from ..auth.asd import ASDAuth
from ..models.sn_record import SNRecord, PickingRecord

logger = logging.getLogger(__name__)


class PickingProcessor:
    """拣货处理器"""
    
    def __init__(self, auth: ASDAuth):
        """
        初始化拣货处理器
        
        Args:
            auth: ASD系统认证器
        """
        self.auth = auth
    
    def pick_sn(self, sn_code: str) -> PickingRecord:
        """
        执行单个SN的拣货操作
        
        流程：
        1. 查询SN -> 获取商品信息
        2. 创建出货单 -> 获取soNo
        3. 查询拣货详情
        4. 确认拣货
        
        Args:
            sn_code: SN编码
            
        Returns:
            拣货记录
        """
        record = PickingRecord(sn_code=sn_code, so_no="", success=False)
        
        try:
            # 步骤1：查询SN
            step1_result = self._query_sn(sn_code)
            if not step1_result:
                record.message = "查询SN失败"
                return record
            
            # 步骤2：创建出货单
            step2_result = self._create_order(step1_result)
            if not step2_result:
                record.message = "创建出货单失败"
                return record
            
            so_no = step2_result
            record.so_no = so_no
            
            # 步骤3：查询拣货详情
            step3_result = self._query_pick_detail(so_no)
            if not step3_result:
                record.message = "查询拣货详情失败"
                return record
            
            # 步骤4：确认拣货
            step4_success = self._confirm_pick(so_no, sn_code)
            if not step4_success:
                record.message = "确认拣货失败"
                return record
            
            record.success = True
            record.message = "拣货成功"
            record.picked_at = datetime.now()
            logger.info(f"SN {sn_code} 拣货成功")
            
        except Exception as e:
            record.message = f"拣货异常: {str(e)}"
            logger.error(f"SN {sn_code} 拣货异常: {e}")
        
        return record
    
    def pick_batch(self, sn_list: List[SNRecord]) -> List[PickingRecord]:
        """
        批量拣货
        
        Args:
            sn_list: SN记录列表
            
        Returns:
            拣货记录列表
        """
        records = []
        total = len(sn_list)
        
        for idx, sn_record in enumerate(sn_list, 1):
            logger.info(f"[{idx}/{total}] 处理拣货: {sn_record.sn_code}")
            record = self.pick_sn(sn_record.sn_code)
            records.append(record)
        
        # 统计
        success_count = sum(1 for r in records if r.success)
        logger.info(f"批量拣货完成: {success_count}/{total} 成功")
        
        return records
    
    def _query_sn(self, sn_code: str) -> Dict[str, Any]:
        """
        查询SN信息
        
        Args:
            sn_code: SN编码
            
        Returns:
            SN信息字典
        """
        url = "/wms-web/rfweb/rfController/querySoSkuBySn"
        data = {"data": json.dumps({"snCode": sn_code})}
        
        response = self.auth.post(url, data=data)
        result = response.json()
        
        if result.get("data"):
            return result["data"]
        
        logger.warning(f"查询SN {sn_code} 无结果: {result}")
        return {}
    
    def _create_order(self, item_data: Dict[str, Any]) -> str:
        """
        创建出货单
        
        Args:
            item_data: 商品信息
            
        Returns:
            出货单号(soNo)
        """
        url = "/wms-web/rfweb/rfController/saveWmsSoOrder"
        
        order_data = {
            "customerCode": None,
            "customerName": None,
            "items": [item_data],
            "soType": "YHJCK",
            "whCode": None,
            "whName": None
        }
        
        data = {"data": json.dumps(order_data)}
        response = self.auth.post(url, data=data)
        result = response.json()
        
        so_no = result.get("data", "")
        if so_no:
            return so_no
        
        logger.warning(f"创建出货单失败: {result}")
        return ""
    
    def _query_pick_detail(self, so_no: str) -> bool:
        """
        查询拣货详情
        
        Args:
            so_no: 出货单号
            
        Returns:
            是否成功
        """
        url = "/wms-web/rfweb/rfController/WMSRF_PK_QueryPickDetail"
        
        query_data = {
            "allocId": None,
            "currentIndex": 1,
            "pickNo": None,
            "soDeliver": "Y",
            "soNo": so_no,
            "toId": None
        }
        
        data = {"data": json.dumps(query_data)}
        response = self.auth.post(url, data=data)
        result = response.json()
        
        return result.get("success", False) or "data" in result
    
    def _confirm_pick(self, so_no: str, sn_code: str) -> bool:
        """
        确认拣货
        
        Args:
            so_no: 出货单号
            sn_code: SN编码
            
        Returns:
            是否成功
        """
        url = "/wms-web/rfweb/rfController/pickBySnCode"
        
        pick_data = {
            "soNo": so_no,
            "snCode": sn_code
        }
        
        data = {"data": json.dumps(pick_data)}
        response = self.auth.post(url, data=data)
        result = response.json()
        
        return result.get("success", False)
