"""
博餐 Agent OS
餐饮智能体操作系统

五层架构：
1. 多模态交互层 (Interface)
2. 大脑中枢层 (Brain & Memory)
3. 技能总线层 (Skill Hub)
4. 抓手调度层 (Claw Routing)
5. 安全基建层 (Infrastructure)
"""

__version__ = "0.1.0"
__author__ = "博餐 Agent Team"

from bocan.core.agent import BocanAgent
from bocan.core.manifest import TenantManifest
from bocan.core.types import *

__all__ = [
    "BocanAgent",
    "TenantManifest",
    "OperationLevel",
    "SkillResult",
    "Task",
]
