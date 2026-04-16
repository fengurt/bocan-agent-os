"""
BaseSkill 抽象基类
所有 Skill 必须继承此类
"""
from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field

from bocan.core.types import OperationLevel, SkillResult


class SkillContext(BaseModel):
    """Skill 执行上下文"""
    tenant_id: str
    manifest: dict = Field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    extra: dict[str, Any] = Field(default_factory=dict)


class BaseSkill(ABC):
    """
    Skill 基类

    属性:
        name: 唯一名称，如 "meituan_queue"
        description: 描述，用于 Agent 理解何时调用
        required_claws: 需要的 Claw 类型列表，如 ["meituan_api", "rpa"]
        operation_level: 默认操作等级
    """

    name: str = ""
    description: str = ""
    required_claws: list[str] = Field(default_factory=list)
    operation_level: OperationLevel = OperationLevel.GREEN

    @abstractmethod
    async def execute(self, claw: Any, context: SkillContext) -> SkillResult:
        """
        执行 Skill

        Args:
            claw: ClawRouter 注入的 Claw 实例
            context: 执行上下文

        Returns:
            SkillResult: 执行结果
        """
        ...

    def get_operation_level(self, context: SkillContext) -> OperationLevel:
        """
        根据上下文动态判断操作等级
        子类可覆盖
        """
        return self.operation_level

    def validate_context(self, context: SkillContext) -> Optional[str]:
        """
        验证上下文是否合法
        返回错误信息或 None
        """
        if not context.tenant_id:
            return "tenant_id is required"
        return None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r})>"
