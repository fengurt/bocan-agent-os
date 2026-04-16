"""
意图规划器 (Intent Planner)
将自然语言拆解为标准任务流水线
"""
from bocan.core.manifest import TenantManifest
from bocan.core.types import Task


class IntentPlanner:
    """
    简单的规则 + LLM 混合规划器
    
    规则映射（快速路径）：
    - 包含"排队"/"多少人" → queue_status
    - 包含"下架"/"售完"/"估清" → inventory_update  
    - 包含"优惠券"/"代金券" → coupon_dispatch
    - 包含"好评"/"回复" → review_reply
    """
    
    SKILL_MAP = {
        "queue": ["meituan_queue"],
        "inventory": ["meituan_inventory"],
        "coupon": ["coupon_skill"],
        "review": ["review_skill"],
        "menu": ["menu_skill"],
        "vip": ["vip_skill"],
    }
    
    def __init__(self, manifest: TenantManifest):
        self.manifest = manifest
        self.active_platforms = manifest.get_active_platforms()
    
    def plan(self, task: Task) -> "ExecutionPlan":
        """将任务拆解为执行计划"""
        intent = task.intent.lower()
        
        # 规则匹配（快速路径）
        skills = []
        
        if any(k in intent for k in ["排队", "桌", "等位", "叫号"]):
            skills.extend(self.SKILL_MAP["queue"])
        
        if any(k in intent for k in ["下架", "售完", "估清", "补货", "上架", "改价"]):
            skills.extend(self.SKILL_MAP["inventory"])
        
        if any(k in intent for k in ["优惠券", "代金券", "免单", "折扣"]):
            skills.extend(self.SKILL_MAP["coupon"])
        
        if any(k in intent for k in ["好评", "回复", "差评", "投诉"]):
            skills.extend(self.SKILL_MAP["review"])
        
        if any(k in intent for k in ["菜单", "菜品", "推荐"]):
            skills.extend(self.SKILL_MAP["menu"])
        
        if any(k in intent for k in ["vip", "会员", "熟客", "老客"]):
            skills.extend(self.SKILL_MAP["vip"])
        
        # 去重
        skills = list(dict.fromkeys(skills))
        
        return ExecutionPlan(
            intent=task.intent,
            required_skills=skills,
            context=task.context,
            reasoning=self._reason_intent(intent)
        )
    
    def _reason_intent(self, intent: str) -> str:
        """推理过程记录"""
        return f"检测到关键词匹配，涉及Skills: {', '.join(self.SKILL_MAP.keys())}"


class ExecutionPlan:
    def __init__(self, intent: str, required_skills: list, context: dict, reasoning: str):
        self.intent = intent
        self.required_skills = required_skills
        self.context = context
        self.reasoning = reasoning
