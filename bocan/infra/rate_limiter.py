"""
RateLimiter - 限流器
基于令牌桶算法的异步限流，支持多组独立限制
"""
import asyncio
import time
from typing import NamedTuple


class RateLimit(NamedTuple):
    """限流配置"""
    rate: float      # 每秒多少个请求
    burst: int = 1   # 突发容量


class TokenBucket:
    """令牌桶实现"""

    def __init__(self, rate: float, burst: int = 1):
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """获取令牌，阻塞直到获得"""
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.last_update
                self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
                self.last_update = now

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return

                wait_time = (tokens - self.tokens) / self.rate
                await asyncio.sleep(wait_time)


class RateLimiter:
    """
    异步限流器
    支持多组独立限流（如 per-platform, per-endpoint）
    """

    def __init(self):
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = asyncio.Lock()
        self._default_limits: dict[str, RateLimit] = {
            "default":    RateLimit(rate=5.0, burst=2),
            "meituan":    RateLimit(rate=2.0, burst=1),
            "protocol":   RateLimit(rate=1.0, burst=1),
            "rpa":        RateLimit(rate=0.2, burst=1),
        }

    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = asyncio.Lock()
        self._default_limits: dict[str, RateLimit] = {
            "default":  RateLimit(rate=5.0, burst=2),
            "meituan":  RateLimit(rate=2.0, burst=1),
            "protocol": RateLimit(rate=1.0, burst=1),
            "rpa":      RateLimit(rate=0.2, burst=1),
        }

    def _ensure_bucket(self, key: str) -> TokenBucket:
        if key not in self._buckets:
            limit = self._default_limits.get(key, self._default_limits["default"])
            self._buckets[key] = TokenBucket(rate=limit.rate, burst=limit.burst)
        return self._buckets[key]

    async def acquire(self, key: str = "default", tokens: int = 1) -> None:
        """
        限流获取

        Args:
            key:    限流分组标识
            tokens: 需要的令牌数
        """
        bucket = self._ensure_bucket(key)
        await bucket.acquire(tokens)

    def set_limit(self, key: str, rate: float, burst: int = 1) -> None:
        """动态调整限流参数"""
        self._buckets[key] = TokenBucket(rate=rate, burst=burst)
