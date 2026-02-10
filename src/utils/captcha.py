"""验证码识别模块 - 使用百度OCR API"""

import os
import requests
import base64
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class CaptchaRecognizer:
    """验证码识别器 - 基于百度OCR"""
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        初始化验证码识别器
        
        Args:
            api_key: 百度OCR API Key，默认从环境变量 BAIDU_OCR_API_KEY 读取
            secret_key: 百度OCR Secret Key，默认从环境变量 BAIDU_OCR_SECRET_KEY 读取
        """
        self.api_key = api_key or os.getenv("BAIDU_OCR_API_KEY")
        self.secret_key = secret_key or os.getenv("BAIDU_OCR_SECRET_KEY")
        self._access_token: Optional[str] = None
        
        if not self.api_key or not self.secret_key:
            logger.warning("百度OCR API Key 或 Secret Key 未配置，验证码识别功能将不可用")
    
    def _get_access_token(self) -> Optional[str]:
        """
        获取百度OCR访问令牌
        
        Returns:
            access_token 或 None
        """
        if self._access_token:
            return self._access_token
            
        if not self.api_key or not self.secret_key:
            logger.error("百度OCR API Key 或 Secret Key 未配置")
            return None
            
        try:
            url = "https://aip.baidubce.com/oauth/2.0/token"
            params = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.secret_key
            }
            response = requests.post(url, params=params, timeout=10)
            result = response.json()
            
            if "access_token" in result:
                self._access_token = result["access_token"]
                logger.debug("成功获取百度OCR access_token")
                return self._access_token
            else:
                logger.error(f"获取access_token失败: {result}")
                return None
        except Exception as e:
            logger.error(f"获取access_token异常: {e}")
            return None
    
    def recognize(self, image_bytes: bytes) -> Optional[str]:
        """
        识别验证码
        
        Args:
            image_bytes: 验证码图片字节
            
        Returns:
            识别的验证码文本，失败返回None
        """
        access_token = self._get_access_token()
        if not access_token:
            return None
        
        try:
            # 图片转Base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # 调用百度OCR高精度版接口
            url = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = {
                'access_token': access_token,
                'image': image_base64,
                'language_type': 'ENG',  # 验证码通常是纯数字/字母，使用英文模式
                'detect_direction': 'false'
            }
            
            response = requests.post(url, headers=headers, data=data, timeout=10)
            result_json = response.json()
            
            if 'words_result' in result_json and len(result_json['words_result']) > 0:
                # 提取识别结果，去除空格
                recognized_text = ''.join([item['words'] for item in result_json['words_result']])
                recognized_text = recognized_text.replace(" ", "").replace("\n", "")
                logger.debug(f"验证码识别结果: {recognized_text}")
                return recognized_text
            else:
                error_msg = result_json.get('error_msg', '未知错误')
                logger.warning(f"验证码识别失败: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"验证码识别异常: {e}")
            return None
    
    def recognize_with_retry(self, image_bytes: bytes, expected_length: int = 4, max_retry: int = 3) -> Optional[str]:
        """
        带重试机制的验证码识别
        
        Args:
            image_bytes: 验证码图片字节
            expected_length: 期望的验证码长度
            max_retry: 最大重试次数
            
        Returns:
            识别的验证码文本，失败返回None
        """
        for attempt in range(max_retry):
            result = self.recognize(image_bytes)
            if result and len(result) == expected_length:
                return result
            logger.warning(f"验证码识别尝试 {attempt + 1}/{max_retry} 失败，结果: {result}")
        return None
