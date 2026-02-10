"""加密工具模块"""

import base64
from datetime import datetime
from Crypto.Cipher import AES


class AESCipher:
    """AES加密器"""
    
    BLOCK_SIZE = 16
    
    def __init__(self, key: str, iv: str):
        """
        初始化AES加密器
        
        Args:
            key: 加密密钥
            iv: 初始化向量
        """
        self.key = key.encode("utf-8")
        self.iv = iv.encode("utf-8")
    
    @staticmethod
    def _zero_pad(data: bytes) -> bytes:
        """
        零填充，匹配CryptoJS的ZeroPadding行为
        
        Args:
            data: 原始数据
            
        Returns:
            填充后的数据
        """
        pad_len = AES.block_size - (len(data) % AES.block_size)
        return data + bytes([0] * pad_len)
    
    def encrypt(self, plaintext: str) -> str:
        """
        加密文本
        
        Args:
            plaintext: 明文
            
        Returns:
            Base64编码的密文
        """
        padded_text = self._zero_pad(plaintext.encode("utf-8"))
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        encrypted = cipher.encrypt(padded_text)
        return base64.b64encode(encrypted).decode("utf-8")
    
    def decrypt(self, ciphertext: str) -> str:
        """
        解密文本
        
        Args:
            ciphertext: Base64编码的密文
            
        Returns:
            明文
        """
        encrypted = base64.b64decode(ciphertext)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        decrypted = cipher.decrypt(encrypted)
        # 去除零填充
        return decrypted.rstrip(b"\x00").decode("utf-8")


class PasswordEncryptor:
    """密码加密器 - 按日期生成动态密钥"""
    
    def __init__(self, iv: str = "dongjunyaoguoqip", key_prefix: str = "asd0", key_suffix: str = "bjsf"):
        """
        初始化密码加密器
        
        Args:
            iv: 初始化向量
            key_prefix: 密钥前缀
            key_suffix: 密钥后缀
        """
        self.iv = iv
        self.key_prefix = key_prefix
        self.key_suffix = key_suffix
    
    def _generate_key(self, date: datetime = None) -> str:
        """
        生成加密密钥
        
        Args:
            date: 日期，默认为当前日期
            
        Returns:
            密钥字符串
        """
        if date is None:
            date = datetime.now()
        date_str = date.strftime("%Y%m%d")
        return f"{self.key_prefix}{date_str}{self.key_suffix}"
    
    def encrypt(self, password: str, date: datetime = None) -> str:
        """
        加密密码
        
        Args:
            password: 原始密码
            date: 日期，默认为当前日期
            
        Returns:
            加密后的密码
        """
        key = self._generate_key(date)
        cipher = AESCipher(key, self.iv)
        return cipher.encrypt(password)
