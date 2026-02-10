"""大物流系统认证"""

import logging
from typing import Optional

from .base import BaseAuth

logger = logging.getLogger(__name__)


class LogisticsAuth(BaseAuth):
    """大物流系统认证器"""
    
    def __init__(
        self,
        base_url: str = "https://www.anyserves56.com",
        cookie_path: Optional[str] = None
    ):
        """
        初始化大物流系统认证器
        
        Args:
            base_url: 基础URL
            cookie_path: Cookie保存路径
        """
        super().__init__(base_url, cookie_path)
        self._setup_headers()
    
    def _setup_headers(self) -> None:
        """设置请求头"""
        self.session.headers.update({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": "www.anyserves56.com",
            "Origin": "https://www.anyserves56.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36",
            "X-Requested-With": "XMLHttpRequest"
        })
    
    def login(self, username: str, password: str, **kwargs) -> bool:
        """
        登录大物流系统
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            是否登录成功
        """
        login_url = "/wms-web/security/login"
        
        data = {
            "username": username,
            "password": password,
            "authCode": "",
            "language": "zh_CN"
        }
        
        try:
            response = self.post(login_url, data=data)
            result = response.json()
            
            if result.get("success"):
                logger.info("大物流系统登录成功")
                self._is_authenticated = True
                self.save_cookies()
                return True
            else:
                logger.error(f"大物流系统登录失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"大物流系统登录异常: {e}")
            return False
    
    def check_login(self) -> bool:
        """
        检查登录状态
        
        Returns:
            是否已登录
        """
        # 通过查询接口检查
        try:
            url = "/wms-web/oubweb/outboundSoController/collectSoOrderGroupByStatus.shtml"
            response = self.post(url, data={"page.currentPage": "1", "page.limitCount": "1"})
            
            if response.status_code == 200:
                self._is_authenticated = True
                return True
            
            self._is_authenticated = False
            return False
            
        except Exception:
            self._is_authenticated = False
            return False
