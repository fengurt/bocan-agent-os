"""
美团排队 Skill
基于抓包的逆向API实现（Protocol Hook Claw）

注意：此为演示版本，真实API需要：
1. 抓包获取真实的接口地址和签名算法
2. 处理加密参数（加密UA/设备指纹等）
3. 实现美团版本检测和签名算法 (version_checker.py)
"""
import time
from bocan.skill_hub.hub import BaseSkill
from bocan.core.types import SkillResult, OperationLevel
from bocan.core.manifest import TenantManifest


class MeituanQueueSkill(BaseSkill):
    """
    美团排队 Skill
    
    功能：
    - 查询当前排队状态
    - 发送等候通知
    - 自动发优惠券挽留
    
    操作等级：
    - GREEN: 查询排队状态
    - YELLOW: 发送等候通知
    - YELLOW: 自动发小额优惠券
    - RED: 退单/大额退款（只生成草稿）
    """
    
    name = "meituan_queue"
    description = "美团排队系统集成"
    required_claws = ["meituan_queue_claw"]
    
    def __init__(self):
        self.manifest: TenantManifest = None
    
    def set_manifest(self, manifest: TenantManifest):
        self.manifest = manifest
    
    def get_operation_level(self, context: dict) -> str:
        action = context.get("action", "get_queue")
        
        if action == "get_queue":
            return "green"
        elif action in ["send_notification", "apply_coupon"]:
            return "yellow"
        elif action in ["cancel_queue", "refund"]:
            return "red"
        return "green"
    
    async def execute(self, claw, context: dict) -> SkillResult:
        """
        执行美团排队相关动作
        
        Args:
            claw: ClawRouter 返回的具体 Claw 实例
            context: {
                "action": "get_queue" | "send_notification" | "apply_coupon",
                "customer_id": str (可选),
                "coupon_amount": float (可选),
                ...
            }
        """
        start = time.time()
        action = context.get("action", "get_queue")
        
        try:
            if action == "get_queue":
                result = await self._get_queue_status(claw, context)
            elif action == "send_notification":
                result = await self._send_notification(claw, context)
            elif action == "apply_coupon":
                result = await self._apply_coupon(claw, context)
            else:
                result = {"success": False, "error": f"Unknown action: {action}"}
            
            return SkillResult(
                skill_name=self.name,
                success=result.get("success", False),
                data=result,
                latency_ms=int((time.time() - start) * 1000)
            )
        
        except Exception as e:
            return SkillResult(
                skill_name=self.name,
                success=False,
                error=str(e),
                latency_ms=int((time.time() - start) * 1000)
            )
    
    async def _get_queue_status(self, claw, context: dict) -> dict:
        """
        获取排队状态
        
        Returns:
            {
                "wait_count": int,   # 等位桌数
                "avg_wait_min": int, # 预计等候时间（分钟）
                "vip_wait_count": int, # VIP等候数
            }
        """
        shop_id = context.get("shop_id", self.manifest.platforms[0].shop_id if self.manifest.platforms else "")
        
        result = await claw.execute("get_queue_status", {"shop_id": shop_id})
        
        if result.get("success"):
            # 提取关键数据
            data = result.get("data", {})
            return {
                "success": True,
                "wait_count": data.get("wait_count", 0),
                "avg_wait_min": data.get("avg_wait_time", 0),
                "platform": "meituan",
                "shop_name": self.manifest.tenant_name if self.manifest else "未知门店",
            }
        
        # 降级：返回模拟数据（演示用）
        return {
            "success": True,
            "wait_count": 8,
            "avg_wait_min": 35,
            "platform": "meituan",
            "note": "这是模拟数据，请替换为真实API",
            "shop_name": self.manifest.tenant_name if self.manifest else "金谷园饺子馆",
        }
    
    async def _send_notification(self, claw, context: dict) -> dict:
        """
        发送等候通知给顾客
        
        Args:
            customer_id: 顾客ID
            message: 通知内容
        """
        # 获取VIP信息
        if self.manifest:
            vip = self.manifest.vip_customers.get(context.get("customer_id", ""))
            if vip:
                name = vip.get("name", "顾客")
            else:
                name = "亲爱的顾客"
        else:
            name = "亲爱的顾客"
        
        wait_left = context.get("wait_left", 5)
        coupon_amount = context.get("coupon_amount", 0)
        
        message = f"亲爱的{name}，金谷园前面还有{wait_left}桌，大冷天辛苦了！"
        if coupon_amount > 0:
            message += f" 送您{coupon_amount}元代金券，入座立刻上菜！"
        
        result = await claw.execute("notify_customer", {
            "message": message,
            "customer_id": context.get("customer_id")
        })
        
        return {
            "success": result.get("success", True),
            "message": message,
            "action": "notification_sent",
            "note": "通知已发送"
        }
    
    async def _apply_coupon(self, claw, context: dict) -> dict:
        """
        自动发放优惠券挽留顾客
        
        Args:
            customer_id: 顾客ID
            amount: 优惠券金额
        """
        amount = context.get("amount", 10)
        customer_id = context.get("customer_id", "")
        
        # 检查权限（黄灯操作，不超过配置的自动发放上限）
        if self.manifest:
            policy = self.manifest.approval_policy
            if amount > policy.coupon_max_auto:
                return {
                    "success": False,
                    "error": f"优惠券金额{amount}元超过自动审批上限{policy.coupon_max_auto}元",
                    "requires_approval": True
                }
        
        return {
            "success": True,
            "coupon_sent": True,
            "amount": amount,
            "customer_id": customer_id,
            "message": f"已自动发放{amount}元代金券给顾客"
        }
