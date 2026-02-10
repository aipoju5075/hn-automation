"""配置管理模块"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv


class Config:
    """配置管理类"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        初始化配置
        
        Args:
            config_path: 配置文件路径
        """
        # 加载环境变量
        load_dotenv()
        
        # 加载YAML配置
        self._config = self._load_yaml(config_path)
        
        # 从环境变量覆盖敏感配置
        self._load_from_env()
    
    def _load_yaml(self, path: str) -> Dict[str, Any]:
        """加载YAML配置文件"""
        config_file = Path(path)
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        # 工单系统
        if os.getenv("WORKORDER_USERNAME"):
            self._config.setdefault("credentials", {}).setdefault("workorder", {})
            self._config["credentials"]["workorder"]["username"] = os.getenv("WORKORDER_USERNAME")
            self._config["credentials"]["workorder"]["password"] = os.getenv("WORKORDER_PASSWORD")
        
        # ASD系统
        if os.getenv("ASD_USERNAME"):
            self._config.setdefault("credentials", {}).setdefault("asd", {})
            self._config["credentials"]["asd"]["username"] = os.getenv("ASD_USERNAME")
            self._config["credentials"]["asd"]["password"] = os.getenv("ASD_PASSWORD")
        
        # 物流系统
        if os.getenv("LOGISTICS_USERNAME"):
            self._config.setdefault("credentials", {}).setdefault("logistics", {})
            self._config["credentials"]["logistics"]["username"] = os.getenv("LOGISTICS_USERNAME")
            self._config["credentials"]["logistics"]["password"] = os.getenv("LOGISTICS_PASSWORD")
        
        # 自提人员列表
        if os.getenv("SELF_PICKUP_STAFF"):
            staff_list = [s.strip() for s in os.getenv("SELF_PICKUP_STAFF").split(",")]
            self._config.setdefault("business", {})["self_pickup_staff"] = staff_list
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项（支持点号分隔的路径）
        
        Args:
            key: 配置键，如 "system.interval"
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    @property
    def system(self) -> Dict[str, Any]:
        """系统配置"""
        return self._config.get("system", {})
    
    @property
    def urls(self) -> Dict[str, Any]:
        """URL配置"""
        return self._config.get("urls", {})
    
    @property
    def credentials(self) -> Dict[str, Any]:
        """凭证配置"""
        return self._config.get("credentials", {})
    
    @property
    def paths(self) -> Dict[str, str]:
        """路径配置"""
        return self._config.get("paths", {})
    
    @property
    def self_pickup_staff(self) -> List[str]:
        """自提人员列表"""
        return self._config.get("business", {}).get("self_pickup_staff", [])


# 全局配置实例
_config_instance: Optional[Config] = None


def get_config(config_path: str = "config/settings.yaml") -> Config:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance
