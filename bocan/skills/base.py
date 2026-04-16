"""
BocanBaseSkill - Skill 实现基类
继承自 SkillHub 的 BaseSkill，扩展业务上下文
"""
from typing import Any

from bocan.core.types import OperationLevel, SkillResult
from bocan.skill_hub.base import BaseSkill, SkillContext


class BocanBaseSkill(BaseSkill):
    """
    Skill 实现基类
    所有具体 Skill 继承此类，提供通用业务方法
    """

    @property
    def skill_name(self) -> str:
        """获取 Skill 名称，兼容 NAME 和 name 属性"""
        return getattr(self, 'NAME', None) or getattr(self, 'name', None) or self.__class__.__name__

    async def execute(self, claw: Any, context: SkillContext) -> SkillResult:
        """
        执行 Skill，带错误处理和计时
        """
        import time
        start = time.monotonic()

        # 上下文校验
        error = self.validate_context(context)
        skill_name = self.skill_name
        if error:
            return SkillResult(
                skill_name=skill_name,
                success=False,
                error=error,
                latency_ms=int((time.monotonic() - start) * 1000),
            )

        try:
            result = await self._execute(claw, context)
            return SkillResult(
                skill_name=skill_name,
                success=True,
                data=result,
                latency_ms=int((time.monotonic() - start) * 1000),
            )
        except Exception as e:
            return SkillResult(
                skill_name=skill_name,
                success=False,
                error=f"{type(e).__name__}: {e}",
                latency_ms=int((time.monotonic() - start) * 1000),
            )

    async def _execute(self, claw: Any, context: SkillContext) -> dict[str, Any]:
        """
        子类实现具体业务逻辑
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement _execute")
