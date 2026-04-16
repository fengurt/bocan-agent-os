"""
CouponDispatchSkill - 优惠券发放 Skill
根据场景自动发放优惠券，支持批量发送和差异化营销
"""
from datetime import datetime, timedelta
from typing import Any, Optional

from bocan.core.types import OperationLevel, SkillResult
from bocan.skills.base import BocanBaseSkill
from bocan.skill_hub.base import SkillContext


class CouponDispatchSkill(BocanBaseSkill):
    """
    优惠券发放 Skill
    
    场景：
    - 顾客等位超时自动发券
    - 差评后补偿发券
    - 雨天/恶劣天气自动发外卖券
    - 新客首单优惠
    - 会员日/节日营销
    """
    
    NAME = "coupon_dispatch"
    VERSION = "1.0.0"
    LEVEL = OperationLevel.YELLOW  # 有金额风险
    
    SCENARIOS = {
        "wait_too_long": {
            "trigger": "等位超过40分钟",
            "coupon_type": "凉菜/小菜券",
            "amount": 5,
            "threshold_minutes": 40
        },
        "rain_day": {
            "trigger": "暴雨/台风天气",
            "coupon_type": "外卖免配送费+9折",
            "amount": 15,
            "platform": "meituan"
        },
        "bad_review": {
            "trigger": "差评后补偿",
            "coupon_type": "满100减20",
            "amount": 20,
            "requires_approval_below": 20
        },
        "vip_birthday": {
            "trigger": "VIP生日",
            "coupon_type": "免费招牌菜一份",
            "amount": 0,
            "requires_approval": True
        },
        "new_customer": {
            "trigger": "新客首单",
            "coupon_type": "首单8折",
            "amount": 0,
            "requires_approval": False
        }
    }
    
    def __init__(self):
        super().__init__(name=self.NAME, version=self.VERSION)
    
    async def execute(self, ctx: SkillContext, params: dict[str, Any]) -> SkillResult:
        """执行优惠券发放"""
        action = params.get("action", "dispatch")
        
        if action == "dispatch":
            return await self._dispatch_coupon(ctx, params)
        elif action == "dispatch_batch":
            return await self._dispatch_batch(ctx, params)
        elif action == "check_available":
            return await self._check_available(ctx, params)
        else:
            return SkillResult(
                skill_name=self.NAME,
                success=False,
                error=f"Unknown action: {action}"
            )
    
    async def _dispatch_coupon(self, ctx: SkillContext, params: dict) -> SkillResult:
        """发放单张优惠券"""
        customer_id = params.get("customer_id")
        scenario = params.get("scenario", "wait_too_long")
        coupon_template = self.SCENARIOS.get(scenario, self.SCENARIOS["wait_too_long"])
        
        if not customer_id:
            return SkillResult(
                skill_name=self.NAME,
                success=False,
                error="customer_id required"
            )
        
        # 检查 HITL 权限
        level = OperationLevel.YELLOW
        if coupon_template.get("requires_approval"):
            level = OperationLevel.RED
        
        if level == OperationLevel.RED:
            return SkillResult(
                skill_name=self.NAME,
                success=True,
                data={
                    "level": level,
                    "draft": self._generate_dispatch_draft(customer_id, scenario, coupon_template),
                    "requires_approval": True
                }
            )
        
        # 调用 Claw 发放优惠券
        claw = ctx.claw
        result = await claw.send_coupon({
            "customer_id": customer_id,
            "coupon_type": coupon_template["coupon_type"],
            "amount": coupon_template["amount"]
        })
        
        return SkillResult(
            skill_name=self.NAME,
            success=True,
            data={
                "level": level,
                "customer_id": customer_id,
                "coupon_sent": coupon_template["coupon_type"],
                "result": result
            }
        )
    
    async def _dispatch_batch(self, ctx: SkillContext, params: dict) -> SkillResult:
        """批量发放优惠券"""
        customer_ids = params.get("customer_ids", [])
        scenario = params.get("scenario")
        segment = params.get("segment", "all")  # all / vip / new / inactive
        
        if not customer_ids and segment:
            # 根据客群标签筛选
            customer_ids = await self._filter_customers(ctx, segment)
        
        coupon_template = self.SCENARIOS.get(scenario, self.SCENARIOS["wait_too_long"])
        
        claw = ctx.claw
        success_count = 0
        failed = []
        
        for cid in customer_ids:
            try:
                result = await claw.send_coupon({
                    "customer_id": cid,
                    "coupon_type": coupon_template["coupon_type"],
                    "amount": coupon_template["amount"]
                })
                if result.get("success"):
                    success_count += 1
                else:
                    failed.append({"customer_id": cid, "reason": "发送失败"})
            except Exception as e:
                failed.append({"customer_id": cid, "reason": str(e)})
        
        return SkillResult(
            skill_name=self.NAME,
            success=True,
            data={
                "level": OperationLevel.YELLOW,
                "total": len(customer_ids),
                "success": success_count,
                "failed": len(failed),
                "failed_details": failed[:10]  # 最多显示10个
            }
        )
    
    async def _check_available(self, ctx: SkillContext, params: dict) -> SkillResult:
        """查询可用优惠券"""
        claw = ctx.claw
        coupons = await claw.get_available_coupons(params)
        
        return SkillResult(
            skill_name=self.NAME,
            success=True,
            data={"coupons": coupons}
        )
    
    async def _filter_customers(self, ctx: SkillContext, segment: str) -> list[str]:
        """根据客群标签筛选顾客"""
        all_customers = ctx.manifest.vip_customers
        
        if segment == "all":
            return list(all_customers.keys())
        elif segment == "vip":
            return [cid for cid, c in all_customers.items() if c.get("vip_level", 0) > 0]
        elif segment == "inactive":
            # 30天未消费
            return [cid for cid, c in all_customers.items() if c.get("last_visit")] 
        else:
            return list(all_customers.keys())
    
    def _generate_dispatch_draft(self, customer_id: str, scenario: str, template: dict) -> str:
        """生成发放草稿"""
        return f"""【优惠券发放草稿 - 待审批】
━━━━━━━━━━━━━━━━━━━━━━
顾客ID：{customer_id}
发放场景：{template['trigger']}
券类型：{template['coupon_type']}
━━━━━━━━━━━━━━━━━━━━━━
[ ] 确认发放
[ ] 修改方案
[ ] 取消
"""
