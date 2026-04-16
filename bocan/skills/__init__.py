"""
Skills - 业务技能实现
"""
from bocan.skills.base import BocanBaseSkill
from bocan.skills.meituan_queue import MeituanQueueSkill
from bocan.skills.inventory_sync import InventorySyncSkill
from bocan.skills.review_defender import ReviewDefenderSkill
from bocan.skills.coupon_dispatch import CouponDispatchSkill

__all__ = [
    "BocanBaseSkill",
    "MeituanQueueSkill",
    "InventorySyncSkill",
    "ReviewDefenderSkill",
    "CouponDispatchSkill",
]
