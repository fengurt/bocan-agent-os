"""
ClawRouter - 抓手路由器
根据 Skill 需求和平台配置选择正确的 Claw
"""
import logging
from typing import Optional

from bocan.core.manifest import TenantManifest
from bocan.claw.base import BaseClaw, ClawConfig
from bocan.claw.meituan_claw import MeituanApiClaw
from bocan.claw.protocol_claw import ProtocolClaw
from bocan.claw.rpa_claw import RPAClaw

logger = logging.getLogger(__name__)

# Skill name → (preferred claw_type, fallback claw_type)
SKILL_CLAW_MAP = {
    "meituan_queue": ["meituan_api", "protocol", "rpa"],
    "meituan_inventory": ["meituan_api", "protocol"],
    "coupon_skill": ["meituan_api", "protocol"],
    "review_skill": ["meituan_api", "protocol"],
    "menu_skill": ["meituan_api", "protocol"],
    "vip_skill": ["meituan_api", "protocol"],
}


class ClawRouter:
    """
    Claw 路由器
    根据 Skill 名称和租户平台配置，选择最合适的 Claw 实例
    """

    def __init__(self, manifest: TenantManifest):
        self.manifest = manifest
        self._claws: dict[str, BaseClaw] = {}
        self._init_claws()

    def _init_claws(self) -> None:
        """初始化所有可用 Claw 实例"""
        # 白盒 - 美团官方 API
        self._claws["meituan_api"] = MeituanApiClaw(
            name="meituan_api",
            config=ClawConfig(enabled="meituan" in self.manifest.get_active_platforms()),
        )

        # 灰盒 - 逆向抓包
        self._claws["protocol"] = ProtocolClaw(
            name="protocol",
            config=ClawConfig(enabled=True),
        )

        # 黑盒 - RPA
        self._claws["rpa"] = RPAClaw(
            name="rpa",
            config=ClawConfig(enabled=True),
        )

    def route(self, skill_name: str) -> BaseClaw:
        """
        为 Skill 选择最合适的 Claw

        优先级:
        1. 租户平台白名优先（如已配置美团 API key）
        2. 灰盒协议爬虫
        3. RPA兜底
        """
        preferred_types = SKILL_CLAW_MAP.get(skill_name, ["meituan_api", "protocol", "rpa"])

        for claw_type in preferred_types:
            claw = self._claws.get(claw_type)
            if claw and claw.config.enabled and await claw.health_check():
                logger.info(f"Route {skill_name!r} → {claw_type!r}")
                return claw

        # fallback: protocol
        logger.warning(f"No healthy claw for {skill_name!r}, using protocol as fallback")
        return self._claws["protocol"]

    def get_claw(self, claw_type: str) -> Optional[BaseClaw]:
        """直接获取指定类型的 Claw"""
        return self._claws.get(claw_type)

    def list_claws(self) -> dict[str, bool]:
        """列出所有 Claw 及其启用状态"""
        return {name: claw.config.enabled for name, claw in self._claws.items()}
