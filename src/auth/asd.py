"""ASD家电系统认证"""

import logging
from typing import Optional

from .base import BaseAuth

logger = logging.getLogger(__name__)


class ASDAuth(BaseAuth):
    """ASD家电系统认证器"""
    
    def __init__(
        self,
        base_url: str = "https://www.anyserves56.com",
        cookie_path: Optional[str] = None
    ):
        """
        初始化ASD家电系统认证器
        
        Args:
            base_url: 基础URL
            cookie_path: Cookie保存路径
        """
        super().__init__(base_url, cookie_path)
        self._setup_headers()
    
    def _setup_headers(self) -> None:
        """设置请求头"""
        self.session.headers.update({
            "Accept-Encoding": "identity",
            "Content-type": "application/x-www-form-urlencoded",
            "User-Agent": "okhttp/4.9.0",
            "Connection": "Keep-Alive",
            "Host": "www.anyserves56.com"
        })
    
    def login(self, username: str, password: str, **kwargs) -> bool:
        """
        登录ASD家电系统
        
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
            "language": "zh_CN"
        }
        
        try:
            response = self.post(login_url, data=data)
            result = response.json()
            
            if result.get("success"):
                logger.info("ASD家电系统登录成功")
                self._is_authenticated = True
                self.save_cookies()
                return True
            else:
                logger.error(f"ASD家电系统登录失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"ASD家电系统登录异常: {e}")
            return False
    
    def check_login(self) -> bool:
        """
        检查登录状态
        
        Returns:
            是否已登录
        """
        # ASD系统没有直接的检查接口，通过后续操作判断
        return self._is_authenticated
