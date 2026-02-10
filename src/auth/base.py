"""认证基类"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
from requests import Session, Response
from requests.cookies import RequestsCookieJar

logger = logging.getLogger(__name__)


class BaseAuth(ABC):
    """认证基类"""
    
    def __init__(self, base_url: str, cookie_path: Optional[str] = None):
        """
        初始化认证器
        
        Args:
            base_url: 基础URL
            cookie_path: Cookie文件路径
        """
        self.base_url = base_url.rstrip("/")
        self.cookie_path = cookie_path
        self.session = Session()
        self._is_authenticated = False
    
    @property
    def is_authenticated(self) -> bool:
        """是否已认证"""
        return self._is_authenticated
    
    @abstractmethod
    def login(self, username: str, password: str, **kwargs) -> bool:
        """
        登录方法
        
        Args:
            username: 用户名
            password: 密码
            **kwargs: 额外参数
            
        Returns:
            是否登录成功
        """
        pass
    
    @abstractmethod
    def check_login(self) -> bool:
        """
        检查登录状态
        
        Returns:
            是否已登录
        """
        pass
    
    def save_cookies(self) -> None:
        """保存Cookie到文件"""
        if not self.cookie_path:
            return
        
        try:
            cookie_dict = dict(self.session.cookies)
            Path(self.cookie_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.cookie_path, "w", encoding="utf-8") as f:
                json.dump(cookie_dict, f, ensure_ascii=False, indent=2)
            logger.debug(f"Cookie已保存到: {self.cookie_path}")
        except Exception as e:
            logger.error(f"保存Cookie失败: {e}")
    
    def load_cookies(self) -> bool:
        """
        从文件加载Cookie
        
        Returns:
            是否加载成功
        """
        if not self.cookie_path or not Path(self.cookie_path).exists():
            return False
        
        try:
            with open(self.cookie_path, "r", encoding="utf-8") as f:
                cookie_dict = json.load(f)
            
            cookies = RequestsCookieJar()
            for key, value in cookie_dict.items():
                cookies.set(key, value)
            
            self.session.cookies.update(cookies)
            logger.debug(f"Cookie已从 {self.cookie_path} 加载")
            return True
        except Exception as e:
            logger.error(f"加载Cookie失败: {e}")
            return False
    
    def clear_cookies(self) -> None:
        """清除Cookie"""
        self.session.cookies.clear()
        if self.cookie_path and Path(self.cookie_path).exists():
            Path(self.cookie_path).unlink()
    
    def get(self, url: str, **kwargs) -> Response:
        """发送GET请求"""
        full_url = f"{self.base_url}{url}" if url.startswith("/") else url
        return self.session.get(full_url, **kwargs)
    
    def post(self, url: str, **kwargs) -> Response:
        """发送POST请求"""
        full_url = f"{self.base_url}{url}" if url.startswith("/") else url
        return self.session.post(full_url, **kwargs)
