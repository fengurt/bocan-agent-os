"""
ProtocolClaw - 灰盒协议 Claw
通过逆向分析抓包获取 API 接口，直接构造请求
适用于美团 H5 / 移动端 API 协议
"""
import time
from typing import Any

import httpx

from bocan.claw.base import BaseClaw, ClawConfig
from bocan.infra.anti_crawl import AntiCrawlHelper
from bocan.infra.rate_limiter import RateLimiter


class ProtocolClaw(BaseClaw):
    """
    协议爬虫 Claw（灰盒）
    通过分析 App/H5 网络请求，直接调用后端 API
    适用于美团外卖、酒店 H5 等平台
    """

    def __init__(
        self,
        name: str = "protocol",
        config: ClawConfig = None,
        rate_limiter: RateLimiter = None,
        anti_crawl: AntiCrawlHelper = None,
    ):
        super().__init__(name=name, claw_type="protocol", config=config or ClawConfig())
        self._client: httpx.AsyncClient | None = None
        self._rate_limiter = rate_limiter or RateLimiter()
        self._anti_crawl = anti_crawl or AntiCrawlHelper()
        self._default_headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                          "Mobile/15E148 MicroMessenger/8.0.0",
            "Accept": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://i.meituan.com/",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout_seconds,
                headers=self._default_headers,
            )
        return self._client

    async def call(self, method: str, path: str, **kwargs) -> Any:
        """
        发起协议请求

        Args:
            method: HTTP 方法
            path:   完整 URL 或路径（自动拼接 Referer）
            **kwargs: 其他请求参数
        """
        await self._rate_limiter.acquire()
        self._anti_crawl.apply_jitter()

        url = path if path.startswith("http") else f"https://i.meituan.com{path}"

        # 从 kwargs 提取请求配置
        params = kwargs.pop("params", {})
        json_data = kwargs.pop("json", None)
        headers_extra = kwargs.pop("headers", {})

        headers = {**self._default_headers, **headers_extra}

        # Proxy 轮换
        proxy = self._anti_crawl.get_next_proxy()
        kwargs["proxies"] = {"https": proxy} if proxy else {}

        client = await self._get_client()

        if method.upper() == "GET":
            resp = await client.get(url, params=params, headers=headers, **kwargs)
        else:
            resp = await client.post(url, json=json_data, params=params, headers=headers, **kwargs)

        resp.raise_for_status()
        return resp.json()

    async def get(self, path: str, **kwargs) -> Any:
        return await self.call("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> Any:
        return await self.call("POST", path, **kwargs)

    async def health_check(self) -> bool:
        """灰盒 Claw 始终可用"""
        return True

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
