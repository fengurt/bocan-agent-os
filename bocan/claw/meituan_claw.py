"""
MeituanApiClaw - 美团官方 API 白盒 Claw
使用美团开放平台 API，需提前申请 AppId/AppSecret
"""
import hashlib
import time
from typing import Any

import httpx

from bocan.claw.base import BaseClaw, ClawConfig
from bocan.infra.vault import IdentityVault


class MeituanApiClaw(BaseClaw):
    """
    美团官方 API Claw（白盒）
    支持美团开放平台 API 调用
    """

    BASE_URL = "https://openapi.meituan.com"

    def __init__(
        self,
        name: str = "meituan_api",
        config: ClawConfig = None,
        vault: IdentityVault = None,
    ):
        super().__init__(name=name, claw_type="meituan_api", config=config or ClawConfig())
        self._vault = vault
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.config.timeout_seconds)
        return self._client

    async def _get_credentials(self) -> dict[str, str]:
        """从 Vault 获取凭证"""
        if self._vault is None:
            return {}
        return {
            "app_id": self._vault.get("meituan_app_id") or "",
            "app_secret": self._vault.get("meituan_app_secret") or "",
        }

    def _sign(self, params: dict[str, Any], app_secret: str) -> str:
        """生成美团 API 签名"""
        sorted_params = sorted(params.items())
        sign_str = "".join(f"{k}{v}" for k, v in sorted_params if v)
        sign_str += app_secret
        return hashlib.md5(sign_str.encode()).hexdigest()[:8]

    async def call(self, method: str, path: str, **kwargs) -> Any:
        """发起美团 API 请求"""
        creds = await self._get_credentials()
        app_id = creds.get("app_id")
        app_secret = creds.get("app_secret")

        url = f"{self.BASE_URL}{path}"
        params = kwargs.pop("params", {})
        json_data = kwargs.pop("json", None)

        # 公共参数
        common = {
            "appId": app_id,
            "timestamp": str(int(time.time())),
            "version": "1.0",
        }

        # 签名
        if app_secret:
            params = {**common, **params}
            params["sign"] = self._sign(params, app_secret)
        else:
            params = {**common, **params}

        client = await self._get_client()

        if method.upper() == "GET":
            resp = await client.get(url, params=params)
        else:
            resp = await client.post(url, params=params, json=json_data)

        resp.raise_for_status()
        return resp.json()

    async def health_check(self) -> bool:
        """检查凭证是否已配置"""
        creds = await self._get_credentials()
        return bool(creds.get("app_id") and creds.get("app_secret"))

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
