"""
Claw 层 - 基础抽象
"""
from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field


class ClawConfig(BaseModel):
    """Claw 配置基类"""
    enabled: bool = True
    timeout_seconds: int = 30
    retry_times: int = 3


class BaseClaw(ABC):
    """
    Claw 抽象基类

    三种 Claw 类型:
    - meituan_claw:   白盒，使用官方 API（需申请）
    - protocol_claw:  灰盒，逆向抓包（抓 H5/API 协议）
    - rpa_claw:       黑盒，Playwright RPA（模拟操作）

    属性:
        name:       Claw 名称
        claw_type:  类型标签
        config:     配置
    """

    name: str = ""
    claw_type: str = ""  # meituan_api | protocol | rpa
    config: ClawConfig = Field(default_factory=ClawConfig)

    @abstractmethod
    async def call(self, method: str, path: str, **kwargs) -> Any:
        """
        发起请求

        Args:
            method: HTTP 方法 (GET/POST/PUT/DELETE)
            path:   API 路径或 URL
            **kwargs: 传递给底层请求的参数

        Returns:
            解析后的响应数据
        """
        ...

    async def health_check(self) -> bool:
        """健康检查"""
        return True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r}, type={self.claw_type!r})>"
