"""
ReviewDefenderSkill - 舆情监控与黄金5分钟危机公关
监控各大平台差评，自动生成道歉回复和补偿方案
"""
import re
from datetime import datetime
from typing import Any, Optional

from bocan.core.types import OperationLevel, SkillResult
from bocan.skills.base import BocanBaseSkill
from bocan.skill_hub.base import SkillContext


class ReviewDefenderSkill(BocanBaseSkill):
    """
    舆情雷达 + 黄金5分钟危机公关
    
    核心能力：
    - 轮询美团/大众点评/饿了么的评价
    - 识别差评关键词（退款/退款/难吃/头发/异物）
    - 生成高度拟人的道歉回复
    - 生成补偿方案（按 HITL 审批）
    """
    
    NAME = "review_defender"
    VERSION = "1.0.0"
    LEVEL = OperationLevel.YELLOW  # 默认YELLOW，补偿超限时升RED
    
    BAD_WORDS = [
        "退款", "退钱", "难吃", "恶心", "头发", "异物", "脏",
        "拉肚子", "食物中毒", "差", "烂", "坑", "骗", "再也不来",
        "投诉", "举报", "315", "曝光", "视频"
    ]
    
    URGENT_WORDS = [
        "头发", "异物", "食物中毒", "拉肚子", "吃到一半", "宝宝",
        "孩子", "怀孕"
    ]
    
    def __init__(self):
        super().__init__(name=self.NAME, version=self.VERSION)
    
    async def execute(self, context: SkillContext, params: dict[str, Any]) -> SkillResult:
        """执行舆情监控任务"""
        action = params.get("action", "check_new")
        
        if action == "check_new":
            return await self._check_new_reviews(context, params)
        elif action == "reply":
            return await self._generate_reply(params)
        elif action == "compensate":
            return await self._generate_compensation(params)
        else:
            return SkillResult(
                skill_name=self.NAME,
                success=False,
                error=f"Unknown action: {action}"
            )
    
    async def _check_new_reviews(self, ctx: SkillContext, params: dict) -> SkillResult:
        """检查新评价"""
        claw = ctx.claw
        shop_id = params.get("shop_id")
        if not shop_id:
            return SkillResult(skill_name=self.NAME, success=False, error="shop_id required")
        
        # 调用 Claw 抓取最新评价
        reviews = await claw.fetch_reviews(shop_id, params)
        
        new_bad_reviews = []
        for r in reviews:
            score = r.get("score", 5)
            content = r.get("content", "")
            
            # 差评检测
            if score <= 2 or any(bw in content for bw in self.BAD_WORDS):
                # 判断紧急程度
                is_urgent = any(uw in content for uw in self.URGENT_WORDS)
                new_bad_reviews.append({
                    "review_id": r.get("review_id"),
                    "platform": r.get("platform"),
                    "score": score,
                    "content": content,
                    "customer": r.get("customer_name", "匿名"),
                    "order_id": r.get("order_id"),
                    "is_urgent": is_urgent,
                    "detected_at": datetime.now().isoformat()
                })
        
        return SkillResult(
            skill_name=self.NAME,
            success=True,
            data={
                "level": OperationLevel.YELLOW,
                "new_bad_reviews": new_bad_reviews,
                "total_checked": len(reviews),
                "urgent_count": sum(1 for r in new_bad_reviews if r["is_urgent"])
            }
        )
    
    async def _generate_reply(self, params: dict) -> SkillResult:
        """生成回复草稿"""
        review_content = params.get("content", "")
        customer_name = params.get("customer", "顾客")
        score = params.get("score", 0)
        
        # 根据差评类型生成拟人化回复
        if "头发" in review_content or "异物" in review_content:
            reply = f"亲爱的{customer_name}，看到您的反馈我们真的非常震惊和抱歉！食品安全是我们的底线，出现这样的问题是我们管理失职。已第一时间反馈给后厨和店长，承诺彻查原因并整改。希望能有机会当面道歉，您的健康是我们最在意的。麻烦您私信我们您的联系方式，我们会专人跟进处理。"
        elif "难吃" in review_content:
            reply = f"亲爱的{customer_name}，感谢您的反馈！您的口味偏好我们会认真记录，争取下次做到让您满意。每个人的口味都不同，我们会继续努力提升菜品质量，也欢迎您下次来尝尝我们的新品，说不定会有惊喜哦！"
        elif "等待时间长" in review_content or "太久" in review_content:
            reply = f"亲爱的{customer_name}，非常抱歉让您久等了！您反馈的问题我们已经同步给店长，周末高峰期我们已经加开了窗口，尽量减少大家等候的时间。希望下次能给您更好的体验！"
        else:
            reply = f"亲爱的{customer_name}，感谢您的反馈！您的意见是我们进步的动力。已经转达给相关伙伴，会认真反思和改进。欢迎您下次再来体验，我们一定会做得更好！"
        
        return SkillResult(
            skill_name=self.NAME,
            success=True,
            data={"reply": reply, "level": OperationLevel.YELLOW}
        )
    
    async def _generate_compensation(self, params: dict) -> SkillResult:
        """生成补偿方案"""
        content = params.get("content", "")
        score = params.get("score", 0)
        order_amount = params.get("order_amount", 0)
        tenant = params.get("tenant")  # 租户配置
        
        # 紧急情况 + 金额大 → 需要 RED 审批
        is_urgent = any(uw in content for uw in self.URGENT_WORDS)
        
        if is_urgent or order_amount > 100:
            level = OperationLevel.RED
            coupon_amount = 0  # 不自动生成，等待审批
            coupon_type = "待定"
        elif order_amount > 50:
            coupon_amount = 20
            coupon_type = "20元无门槛代金券"
        elif order_amount > 20:
            coupon_amount = 10
            coupon_type = "10元无门槛代金券"
        else:
            coupon_amount = 5
            coupon_type = "5元下次满减券"
        
        draft = f"""【差评补偿方案 - 待审批】
━━━━━━━━━━━━━━━━━━━━━━
顾客评分：{score}星
订单金额：{order_amount}元
问题类型：{'⚠️紧急' if is_urgent else '普通'}
━━━━━━━━━━━━━━━━━━━━━━
建议补偿：{coupon_type}
补偿原因：{self._classify_problem(content)}
━━━━━━━━━━━━━━━━━━━━━━
【执行确认】
[ ] 同意发放补偿（{coupon_amount}元{coupon_type}）
[ ] 修改补偿方案（联系店长）
[ ] 仅回复不补偿
━━━━━━━━━━━━━━━━━━━━━━"""
        
        return SkillResult(
            skill_name=self.NAME,
            success=True,
            data={
                "level": level,
                "draft": draft,
                "coupon_amount": coupon_amount,
                "coupon_type": coupon_type,
                "requires_approval": level == OperationLevel.RED
            }
        )
    
    def _classify_problem(self, content: str) -> str:
        """问题分类"""
        if "头发" in content:
            return "食品安全-头发异物"
        elif "异物" in content or "石子" in content or "塑料" in content:
            return "食品安全-异物"
        elif "拉肚子" in content or "食物中毒" in content:
            return "食品安全-食安投诉"
        elif "难吃" in content or "不新鲜" in content:
            return "品质口味"
        elif "等待" in content or "太久" in content:
            return "服务效率"
        elif "态度" in content or "凶" in content or "骂" in content:
            return "服务态度"
        else:
            return "综合投诉"
