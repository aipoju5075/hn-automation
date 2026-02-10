"""工单下载器"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlencode

from ..auth.workorder import WorkOrderAuth
from ..models.sn_record import SNRecord, ProductType

logger = logging.getLogger(__name__)


class WorkOrderDownloader:
    """工单下载器"""
    
    # CSV编码
    CSV_ENCODING = "gbk"
    # SN列名
    SN_COLUMN = "机号1(sn)"
    
    def __init__(self, auth: WorkOrderAuth):
        """
        初始化工单下载器
        
        Args:
            auth: 工单系统认证器
        """
        self.auth = auth
    
    def download_completed_orders(
        self,
        product_type: ProductType,
        save_path: str,
        agency: str = "114"
    ) -> bool:
        """
        下载已完成的工单
        
        Args:
            product_type: 产品类型
            save_path: 保存路径
            agency: 代理商代码
            
        Returns:
            是否下载成功
        """
        # innerType: 1=用户机, 2=用户板
        inner_type = 1 if product_type == ProductType.USER_MACHINE else 2
        
        params = {
            "assign": "",
            "ordername": "",
            "brand": "",
            "machinetype": "",
            "status": "9",  # 已完成状态
            "ischangetime": "",
            "keyword": "",
            "keywordoption": "mobile",
            "datetype": "2",
            "startdate": "",
            "enddate": "",
            "day": "",
            "isremind": "",
            "iscomplain": "",
            "isvip": "2",
            "agency": agency,
            "originname": "",
            "feedback": "",
            "innertype": inner_type,
            "overtime": "",
            "charge": "0",
            "company": "",
            "vip": "",
            "waitpartstatus": "0"
        }
        
        url = f"/index.php/Order/exportorder.html?{urlencode(params)}"
        
        try:
            response = self.auth.get(url)
            response.raise_for_status()
            
            # 保存文件
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"工单数据已下载: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"下载工单数据失败: {e}")
            return False
    
    def parse_sn_list(self, csv_path: str) -> List[SNRecord]:
        """
        从CSV解析SN列表
        
        Args:
            csv_path: CSV文件路径
            
        Returns:
            SN记录列表
        """
        records = []
        
        try:
            with open(csv_path, mode="r", encoding=self.CSV_ENCODING) as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    sn_value = row.get(self.SN_COLUMN, "").strip()
                    if not sn_value:
                        continue
                    
                    # 处理格式问题（去除引号）
                    if '"' in sn_value:
                        parts = sn_value.split('"')
                        sn_value = parts[1] if len(parts) > 1 else sn_value
                    
                    # 确定产品类型
                    product_type = self._detect_product_type(csv_path)
                    
                    record = SNRecord(
                        sn_code=sn_value,
                        product_type=product_type,
                        customer_name=row.get("客户姓名", ""),
                        status="completed"
                    )
                    records.append(record)
            
            logger.info(f"从 {csv_path} 解析到 {len(records)} 条SN记录")
            return records
            
        except Exception as e:
            logger.error(f"解析SN列表失败: {e}")
            return []
    
    def _detect_product_type(self, csv_path: str) -> ProductType:
        """
        根据文件路径检测产品类型
        
        Args:
            csv_path: CSV文件路径
            
        Returns:
            产品类型
        """
        path_lower = csv_path.lower()
        if "用户板" in path_lower or "board" in path_lower:
            return ProductType.USER_BOARD
        return ProductType.USER_MACHINE
