"""
MeituanQueueSkill - 美团排队 Skill
从美团 H5 平台获取实时排队数据，并支持远程叫号
核心逻辑提取自 ~/workspace/hoteldata/src/meituan_scraper.py
"""
from datetime import date, timedelta
from typing import Any
from urllib.parse import quote

from pydantic import Field

from bocan.core.types import OperationLevel, QueueStatus, SkillResult
from bocan.skills.base import BocanBaseSkill
from bocan.skill_hub.base import SkillContext

# 美团城市 ID 映射（餐饮排队也用同一套城市体系）
MEITUAN_CITY_MAP = {
    "北京": {"cityId": 1},
    "上海": {"cityId": 10},
    "广州": {"cityId": 20},
    "深圳": {"cityId": 30},
    "天津": {"cityId": 40},
    "西安": {"cityId": 42},
    "重庆": {"cityId": 45},
    "杭州": {"cityId": 50},
    "南京": {"cityId": 55},
    "武汉": {"cityId": 57},
    "成都": {"cityId": 59},
    "青岛": {"cityId": 60},
    "厦门": {"cityId": 62},
    "大连": {"cityId": 65},
    "长沙": {"cityId": 70},
    "苏州": {"cityId": 80},
    "哈尔滨": {"cityId": 105},
    "珠海": {"cityId": 108},
    "三亚": {"cityId": 111},
    "昆明": {"cityId": 114},
}


class MeituanQueueSkill(BocanBaseSkill):
    """
    美团排队 Skill

    功能：
    1. 获取实时排队数据（等位人数、预计等待时间）
    2. 叫号（通过 Claw 模拟点击或 API）
    3. 发放排队优惠（优惠券推送）

    使用协议抓取（H5 端 API 拦截），参考 meituan_scraper.py 的采集逻辑
    """

    name = "meituan_queue"
    description = "获取美团排队数据，支持叫号和等位优惠发放"
    required_claws = ["meituan_api", "protocol", "rpa"]
    operation_level = OperationLevel.GREEN  # 查询类操作，纯绿

    # 排队相关 API 端点（美团 H5）
    QUEUE_LIST_API = "/index.php/ajax/getQueueShopList"
    QUEUE_CALL_API = "/index.php/ajax/callQueue"

    async def _execute(self, claw: Any, context: SkillContext) -> dict[str, Any]:
        """根据 action 参数分发到具体方法"""
        action = context.extra.get("action", "get_queue_status")
        shop_id = context.extra.get("shop_id")
        city_name = context.extra.get("city_name", "成都")

        if action == "get_queue_status":
            return await self._get_queue_status(claw, city_name, shop_id)
        elif action == "call_next":
            return await self._call_next(claw, context)
        elif action == "notify_coupon":
            return await self._notify_waiting_coupon(claw, context)
        else:
            return {"error": f"Unknown action: {action!r}"}

    async def _get_queue_status(
        self, claw: Any, city_name: str, shop_id: str | None = None
    ) -> dict[str, Any]:
        """
        获取美团排队门店列表或指定门店排队状态

        Args:
            claw:      ClawRouter 注入的 Claw
            city_name: 城市名
            shop_id:   门店 ID（可选，不传则返回城市排队门店列表）
        """
        city_info = MEITUAN_CITY_MAP.get(city_name)
        if not city_info:
            return {"error": f"未知城市: {city_name!r}"}

        city_id = city_info["cityId"]

        if shop_id:
            # 单店详情
            return await self._get_shop_queue_detail(claw, city_id, shop_id)
        else:
            # 城市排队门店列表
            return await self._get_city_queue_list(claw, city_id, city_name)

    async def _get_city_queue_list(
        self, claw: Any, city_id: int, city_name: str
    ) -> dict[str, Any]:
        """获取城市排队门店列表"""
        params = {
            "cityId": city_id,
            "page": 1,
            "pageSize": 20,
        }

        data = await claw.call("GET", self.QUEUE_LIST_API, params=params)

        shops = data.get("data", {}).get("list", [])
        results = []
        for shop in shops:
            results.append({
                "shop_id": shop.get("shopId"),
                "shop_name": shop.get("name"),
                "wait_count": shop.get("waitCount", 0),
                "avg_wait_minutes": shop.get("avgWaitTime", 0),
                "status": shop.get("status", "unknown"),
            })

        return {
            "city": city_name,
            "total": len(results),
            "shops": results,
        }

    async def _get_shop_queue_detail(
        self, claw: Any, city_id: int, shop_id: str
    ) -> dict[str, Any]:
        """获取指定门店排队详情"""
        url = f"https://apimobile.meituan.com/queue/v1/shop/{shop_id}"
        params = {"cityId": city_id}

        data = await claw.call("GET", url, params=params)

        return {
            "shop_id": shop_id,
            "queue_data": data,
        }

    async def _call_next(self, claw: Any, context: SkillContext) -> dict[str, Any]:
        """
        叫下一个号

        通过 RPA Claw 点击叫号按钮（若为协议爬虫则调用 API）
        """
        shop_id = context.extra.get("shop_id")
        if not shop_id:
            return {"error": "shop_id is required for call_next"}

        if claw.claw_type == "rpa":
            # Playwright 模拟点击叫号按钮
            result = await claw.call(
                "goto",
                f"https://i.meituan.com/queue/{shop_id}",
                wait_time=3,
            )
            await claw.call("evaluate", """
                var buttons = document.querySelectorAll('button, div[role="button"]');
                for (var i = 0; i < buttons.length; i++) {
                    var t = buttons[i].innerText || '';
                    if (t.indexOf('叫号') !== -1 || t.indexOf('叫下一个') !== -1) {
                        buttons[i].click();
                        break;
                    }
                }
            """, wait_time=2)
            return {"success": True, "method": "rpa", "shop_id": shop_id}

        # 协议/API 方式
        url = self.QUEUE_CALL_API
        payload = {"shopId": shop_id}
        result = await claw.call("POST", url, json=payload)
        return {"success": True, "method": "api", "result": result}

    async def _notify_waiting_coupon(
        self, claw: Any, context: SkillContext
    ) -> dict[str, Any]:
        """
        向等位中的顾客发放排队优惠券
        """
        shop_id = context.extra.get("shop_id")
        coupon_id = context.extra.get("coupon_id")
        if not shop_id or not coupon_id:
            return {"error": "shop_id and coupon_id are required"}

        url = "/index.php/ajax/sendQueueCoupon"
        payload = {"shopId": shop_id, "couponId": coupon_id}
        result = await claw.call("POST", url, json=payload)
        return {"success": True, "result": result}
