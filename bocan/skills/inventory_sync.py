"""
InventorySyncSkill - 库存同步 Skill
将各外卖平台（美团/饿了么）的菜品库存状态同步到门店 POS 系统
支持批量上架/下架、售罄/补货等操作
"""
from typing import Any

from pydantic import Field

from bocan.core.types import MenuItem, OperationLevel
from bocan.skills.base import BocanBaseSkill
from bocan.skill_hub.base import SkillContext


class InventorySyncSkill(BocanBaseSkill):
    """
    库存同步 Skill

    功能：
    1. 拉取各平台当前菜品库存状态
    2. 批量同步上架/下架
    3. 售罄告警与自动补货
    4. 多平台 SKU 映射统一管理

    操作等级: GREEN（查询）/ YELLOW（下架）/ RED（全量改价）
    """

    name = "meituan_inventory"
    description = "同步美团/饿了么等外卖平台菜品库存状态，上架/下架/售罄"
    required_claws = ["meituan_api", "protocol", "rpa"]
    operation_level = OperationLevel.YELLOW

    # SKU 状态映射
    STATUS_MAP = {
        "available": 1,   # 正常售卖
        "sold_out":  0,   # 售罄
        "unlisted": -1,   # 下架
    }

    async def _execute(self, claw: Any, context: SkillContext) -> dict[str, Any]:
        """分发到具体操作"""
        action = context.extra.get("action", "get_stock")
        shop_id = context.extra.get("shop_id")

        if action == "get_stock":
            return await self._get_stock(claw, context)
        elif action == "update_stock":
            return await self._update_stock(claw, context)
        elif action == "batch_sold_out":
            return await self._batch_sold_out(claw, context)
        elif action == "batch_restock":
            return await self._batch_restock(claw, context)
        else:
            return {"error": f"Unknown action: {action!r}"}

    async def _get_stock(self, claw: Any, context: SkillContext) -> dict[str, Any]:
        """获取菜品库存列表"""
        shop_id = context.extra.get("shop_id")
        platform = context.extra.get("platform", "meituan")

        if not shop_id:
            return {"error": "shop_id is required"}

        url = f"/index.php/ajax/getSkuList"
        params = {"shopId": shop_id, "platform": platform}

        data = await claw.call("GET", url, params=params)

        skus = data.get("data", {}).get("skuList", [])
        items = []
        for sku in skus:
            items.append({
                "sku_id": str(sku.get("skuId", "")),
                "platform_sku_id": str(sku.get("platformSkuId", "")),
                "name": sku.get("name", ""),
                "price": float(sku.get("price", 0)),
                "status": sku.get("status", "unknown"),
                "stock": sku.get("stock", 0),
            })

        return {
            "shop_id": shop_id,
            "platform": platform,
            "items": items,
            "total": len(items),
        }

    async def _update_stock(
        self, claw: Any, context: SkillContext
    ) -> dict[str, Any]:
        """
        更新单个 SKU 状态
        """
        sku_id = context.extra.get("sku_id")
        status = context.extra.get("status")  # available | sold_out | unlisted
        price = context.extra.get("price")

        if not sku_id or not status:
            return {"error": "sku_id and status are required"}

        url = "/index.php/ajax/updateSkuStatus"
        payload = {
            "skuId": sku_id,
            "status": self.STATUS_MAP.get(status, 1),
        }
        if price is not None:
            payload["price"] = price

        result = await claw.call("POST", url, json=payload)
        return {"success": True, "sku_id": sku_id, "new_status": status, "result": result}

    async def _batch_sold_out(
        self, claw: Any, context: SkillContext
    ) -> dict[str, Any]:
        """
        批量售罄（支持按分类或指定 SKU 列表）
        """
        sku_ids = context.extra.get("sku_ids", [])
        category = context.extra.get("category")

        if not sku_ids and not category:
            return {"error": "sku_ids or category is required"}

        if not sku_ids and category:
            # 按分类查询 SKU 列表
            stock_data = await self._get_stock(claw, context)
            sku_ids = [
                item["sku_id"] for item in stock_data.get("items", [])
                if item.get("category") == category and item.get("status") == "available"
            ]

        results = []
        for sku_id in sku_ids:
            r = await self._update_stock(claw, SkillContext(
                tenant_id=context.tenant_id,
                manifest=context.manifest,
                extra={**context.extra, "sku_id": sku_id, "status": "sold_out"},
            ))
            results.append(r)

        return {
            "action": "batch_sold_out",
            "processed": len(results),
            "results": results,
        }

    async def _batch_restock(
        self, claw: Any, context: SkillContext
    ) -> dict[str, Any]:
        """批量补货（上架）"""
        sku_ids = context.extra.get("sku_ids", [])

        if not sku_ids:
            return {"error": "sku_ids is required"}

        results = []
        for sku_id in sku_ids:
            r = await self._update_stock(claw, SkillContext(
                tenant_id=context.tenant_id,
                manifest=context.manifest,
                extra={**context.extra, "sku_id": sku_id, "status": "available"},
            ))
            results.append(r)

        return {
            "action": "batch_restock",
            "processed": len(results),
            "results": results,
        }
