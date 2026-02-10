"""工单系统认证"""

import logging
from typing import Optional, Tuple
from fake_useragent import UserAgent

from .base import BaseAuth
from ..utils.encryption import PasswordEncryptor
from ..utils.captcha import CaptchaRecognizer

logger = logging.getLogger(__name__)


class WorkOrderAuth(BaseAuth):
    """工单系统认证器"""
    
    def __init__(
        self,
        base_url: str = "https://gd.anyserves56.com",
        cookie_path: Optional[str] = None,
        captcha_path: Optional[str] = None
    ):
        """
        初始化工单系统认证器
        
        Args:
            base_url: 工单系统基础URL
            cookie_path: Cookie保存路径
            captcha_path: 验证码保存路径
        """
        super().__init__(base_url, cookie_path)
        self.captcha_path = captcha_path
        self.encryptor = PasswordEncryptor()
        self.captcha_recognizer = CaptchaRecognizer()
        self.ua = UserAgent()
        self._setup_headers()
    
    def _setup_headers(self) -> None:
        """设置请求头"""
        self.session.headers.update({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": self.ua.random
        })
    
    def get_captcha(self) -> Tuple[Optional[str], Optional[bytes]]:
        """
        获取验证码
        
        Returns:
            (验证码文本, 验证码图片字节)
        """
        url = "/index.php/Public/getImgCode.html"
        
        try:
            response = self.get(url)
            response.raise_for_status()
            
            image_bytes = response.content
            
            # 保存验证码图片
            if self.captcha_path:
                from pathlib import Path
                Path(self.captcha_path).parent.mkdir(parents=True, exist_ok=True)
                with open(self.captcha_path, "wb") as f:
                    f.write(image_bytes)
            
            # 识别验证码
            code = self.captcha_recognizer.recognize(image_bytes)
            return code, image_bytes
            
        except Exception as e:
            logger.error(f"获取验证码失败: {e}")
            return None, None
    
    def login(self, username: str, password: str, max_retry: int = 5) -> bool:
        """
        登录工单系统
        
        Args:
            username: 用户名
            password: 密码
            max_retry: 最大重试次数
            
        Returns:
            是否登录成功
        """
        login_url = "/index.php/Public/login.html"
        
        for attempt in range(max_retry):
            try:
                # 获取验证码
                code, _ = self.get_captcha()
                if not code:
                    logger.warning(f"登录尝试 {attempt + 1}/{max_retry}: 验证码获取失败")
                    continue
                
                # 加密密码
                encrypted_pwd = self.encryptor.encrypt(password)
                
                # 登录数据
                data = {
                    "username": username,
                    "accesstoken": encrypted_pwd,
                    "imgcode": code,
                    "event_submit_do_login": "submit"
                }
                
                response = self.post(login_url, data=data)
                result = response.json()
                
                if result.get("code") == 0:
                    logger.info("工单系统登录成功")
                    self._is_authenticated = True
                    self.save_cookies()
                    return True
                else:
                    logger.warning(f"登录尝试 {attempt + 1}/{max_retry} 失败: {result.get('msg')}")
                    
            except Exception as e:
                logger.error(f"登录尝试 {attempt + 1}/{max_retry} 异常: {e}")
        
        logger.error(f"登录失败，已重试 {max_retry} 次")
        return False
    
    def check_login(self) -> bool:
        """
        检查登录状态
        
        Returns:
            是否已登录
        """
        try:
            url = "/index.php/Order/order/status/120.html"
            response = self.get(url, allow_redirects=False)
            
            if response.status_code == 200 and "服务工单" in response.text:
                self._is_authenticated = True
                return True
            
            self._is_authenticated = False
            return False
            
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            self._is_authenticated = False
            return False
    
    def ensure_login(self, username: str, password: str) -> bool:
        """
        确保已登录（优先使用Cookie）
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            是否已登录
        """
        # 尝试使用Cookie登录
        if self.load_cookies() and self.check_login():
            logger.info("使用Cookie成功登录工单系统")
            return True
        
        # Cookie失效，重新登录
        logger.info("Cookie失效，尝试账号密码登录")
        return self.login(username, password)
