"""
工单自动化处理系统 - 主程序

用于海南地区用户机和用户板的自动出库流程
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Optional

from src.utils.config import get_config
from src.utils.logger import setup_logger
from src.utils.notifier import PushNotifier, init_notifier
from src.auth.workorder import WorkOrderAuth
from src.auth.asd import ASDAuth
from src.auth.logistics import LogisticsAuth
from src.core.downloader import WorkOrderDownloader
from src.core.picking import PickingProcessor
from src.core.shipping import ShippingProcessor
from src.models.sn_record import ProductType, SNRecord


class WorkOrderAutomation:
    """工单自动化处理器"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        初始化自动化处理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = get_config(config_path)
        
        # 设置日志
        self.logger = setup_logger(
            name="workorder",
            log_file=self.config.get("paths.log"),
            level=self.config.get("system.log_level", "INFO")
        )
        
        # 初始化认证器
        self.workorder_auth: Optional[WorkOrderAuth] = None
        self.asd_auth: Optional[ASDAuth] = None
        self.logistics_auth: Optional[LogisticsAuth] = None
        
        # 初始化处理器
        self.downloader: Optional[WorkOrderDownloader] = None
        self.picking_processor: Optional[PickingProcessor] = None
        self.shipping_processor: Optional[ShippingProcessor] = None
        
        # 初始化通知器
        self.notifier = init_notifier({"notification": self.config.notification})
    
    def _init_auth(self) -> bool:
        """初始化所有认证器"""
        try:
            # 工单系统
            self.workorder_auth = WorkOrderAuth(
                base_url=self.config.get("urls.workorder.base"),
                cookie_path=self.config.get("paths.cookies"),
                captcha_path=self.config.get("paths.captcha")
            )
            
            # ASD系统
            self.asd_auth = ASDAuth(
                base_url=self.config.get("urls.asd.base"),
                cookie_path=self.config.get("paths.cookies") + ".asd"
            )
            
            # 物流系统
            self.logistics_auth = LogisticsAuth(
                base_url=self.config.get("urls.logistics.base"),
                cookie_path=self.config.get("paths.cookies") + ".logistics"
            )
            
            return True
        except Exception as e:
            self.logger.error(f"初始化认证器失败: {e}")
            self.notifier.send_error(
                error_type="认证器初始化",
                error_message=str(e),
                context={"phase": "初始化认证器"}
            )
            return False
    
    def _login_all(self) -> bool:
        """登录所有系统"""
        try:
            # 获取凭证
            wo_creds = self.config.credentials.get("workorder", {})
            asd_creds = self.config.credentials.get("asd", {})
            logistics_creds = self.config.credentials.get("logistics", {})
            
            # 工单系统登录
            self.logger.info("=========== 工单系统登录 ===========")
            wo_username = wo_creds.get("username", "")
            if not self.workorder_auth.ensure_login(
                wo_username,
                wo_creds.get("password", "")
            ):
                self.logger.error("工单系统登录失败")
                self.notifier.send_login_failure(
                    system_name="工单系统",
                    username=wo_username,
                    reason="验证码识别失败或凭证错误"
                )
                return False
            
            # ASD系统登录
            self.logger.info("=========== ASD家电系统登录 ===========")
            asd_username = asd_creds.get("username", "")
            if not self.asd_auth.login(
                asd_username,
                asd_creds.get("password", "")
            ):
                self.logger.error("ASD家电系统登录失败")
                self.notifier.send_login_failure(
                    system_name="ASD家电系统",
                    username=asd_username,
                    reason="用户名或密码错误，或系统维护中"
                )
                return False
            
            # 物流系统登录
            self.logger.info("=========== 大物流系统登录 ===========")
            logistics_username = logistics_creds.get("username", "")
            if not self.logistics_auth.login(
                logistics_username,
                logistics_creds.get("password", "")
            ):
                self.logger.error("大物流系统登录失败")
                self.notifier.send_login_failure(
                    system_name="大物流系统",
                    username=logistics_username,
                    reason="用户名或密码错误，或系统维护中"
                )
                return False
            
            # 初始化处理器
            self.downloader = WorkOrderDownloader(self.workorder_auth)
            self.picking_processor = PickingProcessor(self.asd_auth)
            self.shipping_processor = ShippingProcessor(
                self.logistics_auth,
                self.config.self_pickup_staff
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"登录过程异常: {e}")
            self.notifier.send_system_error(
                error=e,
                context={"phase": "系统登录阶段"}
            )
            return False
    
    def process_product_type(self, product_type: ProductType) -> bool:
        """
        处理指定产品类型的出库流程
        
        Args:
            product_type: 产品类型（用户机/用户板）
            
        Returns:
            是否处理成功
        """
        type_name = "用户机" if product_type == ProductType.USER_MACHINE else "用户板"
        self.logger.info(f"=========== 开始处理{type_name} ===========")
        
        try:
            # 1. 确定文件路径
            if product_type == ProductType.USER_MACHINE:
                csv_path = self.config.get("paths.user_machine_csv")
            else:
                csv_path = self.config.get("paths.user_board_csv")
            
            # 2. 下载工单
            self.logger.info("步骤1: 下载已完成工单")
            if not self.downloader.download_completed_orders(
                product_type=product_type,
                save_path=csv_path
            ):
                self.logger.error("下载工单失败")
                return False
            
            # 3. 解析SN列表
            self.logger.info("步骤2: 解析SN列表")
            sn_list = self.downloader.parse_sn_list(csv_path)
            if not sn_list:
                self.logger.warning("未找到有效的SN记录")
                return True  # 没有数据不算失败
            
            # 4. 执行拣货
            self.logger.info("步骤3: 执行拣货")
            picking_records = self.picking_processor.pick_batch(sn_list)
            
            # 统计拣货结果
            picking_success = sum(1 for r in picking_records if r.success)
            picking_failed = len(picking_records) - picking_success
            self.logger.info(f"拣货完成: {picking_success}/{len(picking_records)} 成功")
            
            # 保存统计供汇总使用
            self._last_picking_stats = {
                "picking_success": picking_success,
                "picking_failed": picking_failed,
                "total": len(picking_records)
            }
            
            # 5. 获取待发货数据
            self.logger.info("步骤4: 获取待发货数据")
            pending_shipments = self.shipping_processor.get_pending_shipments(
                days_back=self.config.get("date_range.days_back", 29)
            )
            
            if not pending_shipments:
                self.logger.warning("没有待发货记录")
                return True
            
            # 6. 执行发货
            self.logger.info("步骤5: 执行发货")
            # 构建SN到客户名的映射（可以从工单系统获取，这里简化处理）
            sn_name_map = {sn.sn_code: sn.customer_name for sn in sn_list}
            
            shipping_records = self.shipping_processor.ship_batch(
                pending_shipments,
                sn_name_map
            )
            
            # 统计发货结果
            shipping_success = sum(1 for r in shipping_records if r.success)
            shipping_failed = len(shipping_records) - shipping_success
            self.logger.info(f"发货完成: {shipping_success}/{len(shipping_records)} 成功")
            
            # 更新统计
            self._last_picking_stats["shipping_success"] = shipping_success
            self._last_picking_stats["shipping_failed"] = shipping_failed
            
            self.logger.info(f"=========== {type_name}处理完成 ===========")
            return True
            
        except Exception as e:
            self.logger.error(f"处理{type_name}时发生异常: {e}", exc_info=True)
            self.notifier.send_system_error(
                error=e,
                context={
                    "product_type": type_name,
                    "phase": "业务处理阶段"
                }
            )
            return False
    
    def run_once(self) -> bool:
        """
        执行一次完整的出库流程
        
        Returns:
            是否执行成功
        """
        start_time = datetime.now()
        self.logger.info(f"============ {start_time} 开始执行 ============")
        
        # 处理统计
        stats = {
            "user_machine": {"picking_success": 0, "shipping_success": 0},
            "user_board": {"picking_success": 0, "shipping_success": 0}
        }
        
        try:
            # 初始化认证器
            if not self._init_auth():
                return False
            
            # 登录所有系统
            if not self._login_all():
                return False
            
            # 处理用户机
            um_result = self.process_product_type(ProductType.USER_MACHINE)
            if um_result and hasattr(self, '_last_picking_stats'):
                stats["user_machine"] = self._last_picking_stats
            
            # 处理用户板
            ub_result = self.process_product_type(ProductType.USER_BOARD)
            if ub_result and hasattr(self, '_last_picking_stats'):
                stats["user_board"] = self._last_picking_stats
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            self.logger.info(f"============ {end_time} 执行完成，耗时 {duration:.2f} 秒 ============")
            # 发送每日汇总通知（可选，根据需求决定是否启用）
            self.notifier.send_daily_summary(
                user_machine_stats=stats["user_machine"],
                user_board_stats=stats["user_board"],
                duration=duration
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"执行过程中发生异常: {e}", exc_info=True)
            self.notifier.send_system_error(
                error=e,
                context={
                    "phase": "主执行流程",
                    "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S')
                }
            )
            return False
    
    def run_loop(self, interval_minutes: Optional[int] = None):
        """
        循环执行出库流程
        
        Args:
            interval_minutes: 执行间隔（分钟），默认使用配置值
        """
        interval = interval_minutes or self.config.get("system.interval", 30)
        self.logger.info(f"启动循环模式，间隔 {interval} 分钟")
        
        while True:
            self.run_once()

            next_run = datetime.now() + timedelta(minutes=interval)
            self.logger.info(f"下次执行时间: {next_run}")
            time.sleep(interval * 60)



def main():
    """主函数"""
    automation = WorkOrderAutomation()
    
    # 单次执行
    # automation.run_once()
    
    # 循环执行（默认每30分钟）
    automation.run_loop()


if __name__ == "__main__":
    main()
