"""
AntiCrawlHelper - 反爬防风控助手
提供 Proxy 轮换、请求 Jitter、浏览器指纹随机化等能力
"""
import asyncio
import random
import time
from typing import Optional


class ProxyPool:
    """Proxy 轮换池"""

    def __init__(self, proxies: list[str] | None = None):
        self._proxies = proxies or []
        self._idx = 0
        self._lock = asyncio.Lock()

    def add(self, proxy: str) -> None:
        self._proxies.append(proxy)

    def get_next(self) -> Optional[str]:
        if not self._proxies:
            return None
        proxy = self._proxies[self._idx % len(self._proxies)]
        self._idx += 1
        return proxy

    def remove(self, proxy: str) -> None:
        if proxy in self._proxies:
            self._proxies.remove(proxy)


class AntiCrawlHelper:
    """
    反爬防风控助手
    功能:
    - Proxy 轮换
    - 请求 Jitter（随机延迟）
    - Referer 链随机化
    - UA 轮换
    """

    # 常用移动端 UA
    COMMON_UA = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 "
        "Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 11; SM-G991B) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/90.0.4430.210 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
        "MicroMessenger/8.0.0",
    ]

    # 常见 Referer 链
    REFERER_CHAIN = [
        "https://i.meituan.com/",
        "https://www.meituan.com/",
        "https://hz.meituan.com/",
    ]

    def __init__(
        self,
        proxies: list[str] | None = None,
        jitter_range: tuple[float, float] = (0.5, 3.0),
    ):
        self._proxy_pool = ProxyPool(proxies)
        self._jitter_range = jitter_range

    def get_next_proxy(self) -> Optional[str]:
        """获取下一个 Proxy"""
        return self._proxy_pool.get_next()

    def add_proxy(self, proxy: str) -> None:
        self._proxy_pool.add(proxy)

    def apply_jitter(self) -> None:
        """在请求间注入随机延迟（模拟真人操作间隔）"""
        jitter = random.uniform(*self._jitter_range)
        time.sleep(jitter)

    async def apply_jitter_async(self) -> None:
        """异步版本的 Jitter"""
        jitter = random.uniform(*self._jitter_range)
        await asyncio.sleep(jitter)

    def get_random_ua(self) -> str:
        """获取随机 UA"""
        return random.choice(self.COMMON_UA)

    def get_random_referer(self, base_domain: str = "meituan.com") -> str:
        """获取随机 Referer"""
        return random.choice(self.REFERER_CHAIN)

    def get_request_headers(self) -> dict[str, str]:
        """生成防风控请求头"""
        return {
            "User-Agent": self.get_random_ua(),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept": "application/json, text/plain, */*",
            "Referer": self.get_random_referer(),
            "X-Requested-With": "XMLHttpRequest",
        }
