"""
核心数据类型定义
"""
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class OperationLevel(str, Enum):
    """操作风险等级"""
    GREEN = "green"  # 绿灯：读操作，Agent全自动
    YELLOW = "yellow"  # 黄灯：软写操作，Agent执行但记录日志
    RED = "red"  # 红灯：硬写操作，只生成草稿需人工审批


class OperationResult(BaseModel):
    """操作执行结果"""
    success: bool
    level: OperationLevel
    message: str = ""
    data: Optional[Any] = None
    draft_content: Optional[str] = None  # RED级操作返回草稿
    requires_approval: bool = False  # 是否需要人工审批


class SkillResult(BaseModel):
    """Skill执行结果"""
    skill_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    latency_ms: int = 0


class Task(BaseModel):
    """Agent任务"""
    id: str
    intent: str  # 自然语言意图
    required_skills: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class QueueStatus(BaseModel):
    """排队状态"""
    platform: str  # meituan / krry / xmd
    shop_id: str
    shop_name: str
    wait_count: int = 0
    avg_wait_minutes: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)


class MenuItem(BaseModel):
    """菜品"""
    sku_id: str
    platform_sku_id: str  # 各平台原始ID
    name: str
    price: float
    status: str = "available"  # available / sold_out / unknown
    category: Optional[str] = None


class Customer(BaseModel):
    """顾客"""
    customer_id: str
    name: Optional[str] = None
    phone: Optional[str] = None
    vip_level: int = 0  # 0=普通, 1=黄金, 2=钻石
    preferences: dict[str, Any] = Field(default_factory=dict)  # 忌口等
    tags: list[str] = Field(default_factory=list)  # ['带孩子', '不吃香菜']
