"""
SkillHub - 技能注册与调度中心
"""
import importlib
import logging
from typing import Optional

from bocan.skill_hub.base import BaseSkill

logger = logging.getLogger(__name__)


class SkillHub:
    """
    技能总线
    统一注册、管理 Skills，支持动态加载和按名称查找
    """

    def __init__(self):
        self._skills: dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill) -> None:
        """注册一个 Skill 实例"""
        if not skill.name:
            raise ValueError(f"Skill must have a name, got {skill!r}")
        if skill.name in self._skills:
            logger.warning(f"Skill {skill.name!r} already registered, overwriting")
        self._skills[skill.name] = skill
        logger.info(f"Registered skill: {skill.name!r}")

    def register_many(self, skills: list[BaseSkill]) -> None:
        """批量注册 Skills"""
        for skill in skills:
            self.register(skill)

    def get(self, name: str) -> Optional[BaseSkill]:
        """根据名称获取 Skill"""
        return self._skills.get(name)

    def list_all(self) -> list[str]:
        """列出所有已注册 Skill 名称"""
        return list(self._skills.keys())

    def list_by_claw(self, claw_type: str) -> list[BaseSkill]:
        """列出支持指定 Claw 类型的 Skills"""
        return [
            s for s in self._skills.values()
            if claw_type in s.required_claws
        ]

    def load_from_module(self, module_path: str) -> None:
        """
        从模块路径动态加载 Skills
        自动注册所有 BaseSkill 子类（除 BaseSkill 本身）
        """
        spec = importlib.util.spec_from_file_location("dynamic_skills", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path!r}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for attr_name in dir(module):
            obj = getattr(module, attr_name)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseSkill)
                and obj is not BaseSkill
            ):
                self.register(obj())

    def load_from_package(self, package: str) -> None:
        """从包名动态加载所有 BaseSkill 子类"""
        try:
            mod = importlib.import_module(package)
        except ImportError as e:
            logger.error(f"Failed to import package {package!r}: {e}")
            return

        for attr_name in dir(mod):
            obj = getattr(mod, attr_name)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseSkill)
                and obj is not BaseSkill
            ):
                self.register(obj())

    def __len__(self) -> int:
        return len(self._skills)

    def __repr__(self) -> str:
        return f"<SkillHub(skills={self.list_all()})>"
