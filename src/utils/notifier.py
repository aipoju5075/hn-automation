"""通知模块 - 基于 pushplus 的消息推送

用于在系统出现异常时及时通知管理员
"""

import logging
import traceback
from datetime import datetime
from typing import Optional
import requests


class PushNotifier:
    """PushPlus 消息推送器"""
    
    API_URL = "http://www.pushplus.plus/send"
    
    def __init__(
        self,
        token: Optional[str] = None,
        enabled: bool = True,
        title_prefix: str = "工单系统"
    ):
        """
        初始化推送器
        
        Args:
            token: PushPlus 用户 token
            enabled: 是否启用通知
            title_prefix: 消息标题前缀
        """
        self.token = token
        self.enabled = enabled and bool(token)
        self.title_prefix = title_prefix
        self.logger = logging.getLogger(__name__)
    
    def _send(
        self,
        title: str,
        content: str,
        template: str = "markdown"
    ) -> bool:
        """
        发送消息
        
        Args:
            title: 消息标题
            content: 消息内容
            template: 消息模板类型
            
        Returns:
            是否发送成功
        """
        if not self.enabled:
            self.logger.debug("通知功能未启用，跳过发送")
            return False
        
        if not self.token:
            self.logger.warning("未配置 PushPlus token，无法发送通知")
            return False
        
        try:
            payload = {
                "token": self.token,
                "title": title,
                "content": content,
                "template": template
            }
            
            response = requests.post(
                self.API_URL,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") == 200:
                self.logger.debug(f"通知发送成功: {title}")
                return True
            else:
                self.logger.warning(f"通知发送失败: {result.get('msg', '未知错误')}")
                return False
                
        except requests.exceptions.Timeout:
            self.logger.error("发送通知超时")
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"发送通知请求失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"发送通知时发生异常: {e}")
            return False
    
    def send_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[dict] = None
    ) -> bool:
        """
        发送异常通知
        
        Args:
            error_type: 错误类型/模块
            error_message: 错误信息
            context: 额外的上下文信息
            
        Returns:
            是否发送成功
        """
        title = f"❌ {self.title_prefix} - {error_type}异常"
        
        # 构建 Markdown 格式的消息内容
        lines = [
            "## ⚠️ 系统异常告警",
            "",
            f"**异常时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**异常模块：** {error_type}",
            "",
            "### 错误信息",
            f"> {error_message}",
            ""
        ]
        
        # 添加上下文信息
        if context:
            lines.extend(["### 上下文信息", ""])
            for key, value in context.items():
                lines.append(f"- **{key}：** {value}")
            lines.append("")
        
        # 添加建议
        lines.extend([
            "---",
            "💡 **建议操作：**",
            "1. 登录服务器查看详细日志",
            "2. 检查各系统连接状态",
            "3. 确认凭证是否过期",
            "",
            f"📁 日志文件：`./logs/app.log`"
        ])
        
        content = "\n".join(lines)
        return self._send(title, content, template="markdown")
    
    def send_system_error(self, error: Exception, context: Optional[dict] = None) -> bool:
        """
        发送系统级异常通知
        
        Args:
            error: 异常对象
            context: 额外的上下文信息
            
        Returns:
            是否发送成功
        """
        error_type = error.__class__.__name__
        error_message = str(error)
        
        title = f"🚨 {self.title_prefix} - 系统异常"
        
        # 获取异常堆栈
        tb = traceback.format_exc()
        # 只取前 10 行，避免消息过长
        tb_lines = tb.strip().split("\n")[-10:]
        tb_summary = "\n".join(tb_lines)
        
        lines = [
            "## 🔥 系统异常告警",
            "",
            f"**异常时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**异常类型：** `{error_type}`",
            "",
            "### 错误信息",
            f"> {error_message}",
            "",
            "### 堆栈摘要",
            f"```python\n{tb_summary}\n```",
            ""
        ]
        
        if context:
            lines.extend(["### 上下文信息", ""])
            for key, value in context.items():
                lines.append(f"- **{key}：** {value}")
            lines.append("")
        
        lines.extend([
            "---",
            "⚠️ **请立即检查系统状态！**",
            "",
            f"📁 完整日志：`./logs/app.log`"
        ])
        
        content = "\n".join(lines)
        return self._send(title, content, template="markdown")
    
    def send_login_failure(
        self,
        system_name: str,
        username: str,
        reason: str
    ) -> bool:
        """
        发送登录失败通知
        
        Args:
            system_name: 系统名称（如：工单系统、ASD系统）
            username: 登录用户名
            reason: 失败原因
            
        Returns:
            是否发送成功
        """
        title = f"🔐 {self.title_prefix} - 登录失败"
        
        lines = [
            "## ⚠️ 系统登录失败",
            "",
            f"**告警时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**目标系统：** {system_name}",
            f"**登录账号：** `{username}`",
            "",
            "### 失败原因",
            f"> {reason}",
            "",
            "---",
            "💡 **建议操作：**",
            "1. 检查用户名和密码是否正确",
            "2. 确认账号是否被锁定",
            "3. 检查网络连接是否正常",
            "4. 查看目标系统是否维护中"
        ]
        
        content = "\n".join(lines)
        return self._send(title, content, template="markdown")
    
    def send_process_failure(
        self,
        process_name: str,
        sn_code: Optional[str],
        error_message: str,
        stats: Optional[dict] = None
    ) -> bool:
        """
        发送业务流程处理失败通知
        
        Args:
            process_name: 流程名称（如：拣货、发货）
            sn_code: 相关的 SN 码
            error_message: 错误信息
            stats: 处理统计信息
            
        Returns:
            是否发送成功
        """
        title = f"📦 {self.title_prefix} - {process_name}失败"
        
        lines = [
            f"## ❌ {process_name}处理异常",
            "",
            f"**异常时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        
        if sn_code:
            lines.append(f"**SN 编码：** `{sn_code}`")
        
        lines.extend([
            "",
            "### 错误信息",
            f"> {error_message}",
            ""
        ])
        
        if stats:
            lines.extend(["### 处理统计", ""])
            lines.append(f"- 成功：{stats.get('success', 0)} 条")
            lines.append(f"- 失败：{stats.get('failed', 0)} 条")
            lines.append(f"- 总计：{stats.get('total', 0)} 条")
            lines.append("")
        
        lines.extend([
            "---",
            "💡 **建议操作：**",
            "1. 检查该 SN 是否已在系统中处理",
            "2. 确认库存是否充足",
            "3. 查看目标系统接口状态"
        ])
        
        content = "\n".join(lines)
        return self._send(title, content, template="markdown")
    
    def send_daily_summary(
        self,
        user_machine_stats: dict,
        user_board_stats: dict,
        duration: float
    ) -> bool:
        """
        发送每日处理汇总通知
        
        Args:
            user_machine_stats: 用户机处理统计
            user_board_stats: 用户板处理统计
            duration: 执行耗时（秒）
            
        Returns:
            是否发送成功
        """
        title = f"📊 {self.title_prefix} - 处理完成汇总"
        
        lines = [
            "## ✅ 自动化处理完成",
            "",
            f"**执行时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**总耗时：** {duration:.1f} 秒",
            "",
            "### 📱 用户机处理结果",
            f"- 拣货成功：**{user_machine_stats.get('picking_success', 0)}** 条",
            f"- 发货成功：**{user_machine_stats.get('shipping_success', 0)}** 条",
            "",
            "### 🔌 用户板处理结果",
            f"- 拣货成功：**{user_board_stats.get('picking_success', 0)}** 条",
            f"- 发货成功：**{user_board_stats.get('shipping_success', 0)}** 条",
            "",
            "---",
            "🎉 所有流程已正常完成，系统运行正常"
        ]
        
        content = "\n".join(lines)
        return self._send(title, content, template="markdown")


# 全局通知器实例
_notifier_instance: Optional[PushNotifier] = None


def get_notifier(
    token: Optional[str] = None,
    enabled: bool = True,
    title_prefix: str = "工单系统"
) -> PushNotifier:
    """
    获取全局通知器实例
    
    Args:
        token: PushPlus token
        enabled: 是否启用
        title_prefix: 标题前缀
        
    Returns:
        PushNotifier 实例
    """
    global _notifier_instance
    if _notifier_instance is None:
        _notifier_instance = PushNotifier(
            token=token,
            enabled=enabled,
            title_prefix=title_prefix
        )
    return _notifier_instance


def init_notifier(config: dict) -> PushNotifier:
    """
    从配置初始化通知器
    
    Args:
        config: 配置字典，需包含 notification 配置
        
    Returns:
        PushNotifier 实例
    """
    global _notifier_instance
    
    notification_config = config.get("notification", {})
    token = notification_config.get("token") or notification_config.get("pushplus_token")
    enabled = notification_config.get("enabled", True)
    title_prefix = notification_config.get("title_prefix", "工单系统")
    
    _notifier_instance = PushNotifier(
        token=token,
        enabled=enabled,
        title_prefix=title_prefix
    )
    
    return _notifier_instance
