"""
博餐 Agent - 核心大脑
"""
import asyncio
import json
from datetime import datetime
from typing import Any, Optional

from bocan.core.manifest import TenantManifest
from bocan.core.types import OperationLevel, OperationResult, SkillResult, Task
from bocan.brain.planner import IntentPlanner
from bocan.brain.memory import ShortTermMemory, LongTermMemory
from bocan.skill_hub.hub import SkillHub
from bocan.claw.router import ClawRouter
from bocan.infra.vault import IdentityVault


class BocanAgent:
    """
    博餐 Agent OS 核心类
    
    负责：
    1. 接收自然语言指令
    2. 拆解任务 → Skill 调用
    3. 执行并路由到正确的 Claw
    4. 按 HITL 机制处理不同风险等级操作
    5. 记忆沉淀
    """
    
    def __init__(self, manifest: TenantManifest, config: Optional[dict] = None):
        self.manifest = manifest
        self.config = config or {}
        
        # 初始化各层
        self.brain = IntentPlanner(manifest)
        self.short_memory = ShortTermMemory()
        self.long_memory = LongTermMemory(manifest.tenant_id)
        self.skill_hub = SkillHub()
        self.claw_router = ClawRouter(manifest)
        self.vault = IdentityVault(manifest.tenant_id)
        
        # 注册所有内置 Skills
        self._register_builtin_skills()
        
    def _register_builtin_skills(self):
        """注册内置 Skills"""
        # 延迟导入避免循环
        from bocan.skills.meituan_queue import MeituanQueueSkill
        self.skill_hub.register(MeituanQueueSkill())
        
    async def execute_task(self, task: Task) -> OperationResult:
        """
        执行任务的主入口
        1. 解析意图 → 技能列表
        2. 按顺序/并行执行 Skills
        3. 判断操作等级 → HITL路由
        """
        # Step 1: 规划
        plan = self.brain.plan(task)
        
        # Step 2: 存入短时记忆
        await self.short_memory.add(task)
        
        # Step 3: 执行 Skills
        skill_results: list[SkillResult] = []
        for skill_name in plan.required_skills:
            skill = self.skill_hub.get(skill_name)
            if not skill:
                skill_results.append(SkillResult(
                    skill_name=skill_name,
                    success=False,
                    error=f"Skill {skill_name} not found"
                ))
                continue
                
            # 获取对应 Claw
            claw = self.claw_router.route(skill_name)
            result = await skill.execute(claw, plan.context)
            skill_results.append(result)
            
            # 存入短时记忆
            await self.short_memory.add(result)
        
        # Step 4: 判断操作等级
        max_level = self._max_operation_level(skill_results)
        
        # Step 5: HITL 路由
        if max_level == OperationLevel.RED:
            # 生成草稿，等待审批
            draft = self._generate_draft(task, skill_results)
            return OperationResult(
                success=True,
                level=OperationLevel.RED,
                message="操作需要人工审批",
                draft_content=draft,
                requires_approval=True
            )
        
        return OperationResult(
            success=all(r.success for r in skill_results),
            level=max_level,
            message="执行完成",
            data={"results": [r.model_dump() for r in skill_results]}
        )
    
    async def execute_with_approval(self, task: Task, approved: bool) -> OperationResult:
        """执行已审批的任务"""
        if not approved:
            return OperationResult(
                success=False,
                level=OperationLevel.RED,
                message="用户拒绝执行"
            )
        
        # 重新执行
        return await self.execute_task(task)
    
    def _max_operation_level(self, results: list[SkillResult]) -> OperationLevel:
        level_map = {"green": 0, "yellow": 1, "red": 2}
        max_r = 0
        for r in results:
            l = level_map.get(r.data.get("level", "green") if r.data else "green", 0)
            max_r = max(max_r, l)
        return [OperationLevel.GREEN, OperationLevel.YELLOW, OperationLevel.RED][max_r]
    
    def _generate_draft(self, task: Task, results: list[SkillResult]) -> str:
        """生成操作草稿"""
        return f"""【待审批操作草稿】
时间: {datetime.now().isoformat()}
任务: {task.intent}
执行结果: {json.dumps([r.model_dump() for r in results], ensure_ascii=False, indent=2)}
建议: 请确认是否执行"""
    
    def get_memory_context(self) -> dict:
        """获取记忆上下文（用于注入 LLM）"""
        return {
            "short_term": self.short_memory.get_all(),
            "long_term": self.long_memory.get_recent(5),
            "tenant": self.manifest.model_dump(exclude={"vip_customers"})
        }
    
    def chat(self, message: str) -> str:
        """
        自然语言对话入口（同步封装）
        """
        task = Task(
            id=f"task_{datetime.now().timestamp()}",
            intent=message
        )
        result = asyncio.run(self.execute_task(task))
        
        if result.requires_approval:
            return f"⏳ {result.message}\n\n{result.draft_content}"
        
        if result.success:
            return f"✅ {result.message}\n\n{json.dumps(result.data, ensure_ascii=False, indent=2)}"
        else:
            return f"❌ 操作失败: {result.message}"
