"""
RPAClaw - 黑盒 RPA Claw
使用 Playwright 模拟浏览器操作，适用于 JS 加密/验证码/账号绑定等场景
"""
import asyncio
import logging
from typing import Any, Optional

from bocan.claw.base import BaseClaw, ClawConfig

logger = logging.getLogger(__name__)


class RPAClaw(BaseClaw):
    """
    Playwright RPA Claw（黑盒）
    模拟真实浏览器操作，适用于:
    - JS 加密的登录/请求
    - 验证码（滑块、点选）
    - 账号绑定等需要 Cookie/Session 的操作
    """

    def __init__(
        self,
        name: str = "rpa",
        config: ClawConfig = None,
        playwright_browser: str = "chromium",
    ):
        super().__init__(name=name, claw_type="rpa", config=config or ClawConfig())
        self._browser_type = playwright_browser
        self._page_pool: list[Any] = []  # Playwright Page pool
        self._lock = asyncio.Lock()

    async def call(self, method: str, path: str, **kwargs) -> Any:
        """
        执行 RPA 操作

        Args:
            method: 操作类型 (goto | click | fill | evaluate | screenshot)
            path:   URL 或目标选择器
            **kwargs: 操作参数
        """
        action = method.lower()
        page = await self._acquire_page()

        try:
            if action == "goto":
                return await self._rpa_goto(page, path, **kwargs)
            elif action == "click":
                return await self._rpa_click(page, path, **kwargs)
            elif action == "fill":
                return await self._rpa_fill(page, path, **kwargs)
            elif action == "evaluate":
                return await self._rpa_evaluate(page, path, **kwargs)
            elif action == "screenshot":
                return await self._rpa_screenshot(page, path, **kwargs)
            else:
                raise ValueError(f"Unknown RPA action: {action!r}")
        finally:
            await self._release_page(page)

    async def _acquire_page(self) -> Any:
        """获取一个 Playwright Page"""
        async with self._lock:
            try:
                pw = __import__("playwright", fromlist=["async_"]).async_
            except ImportError:
                raise ImportError(
                    "Playwright not installed. Run: pip install playwright && playwright install"
                )

            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
                )
            )
            page = await context.new_page()
            return page

    async def _release_page(self, page: Any) -> None:
        """释放 Page"""
        try:
            context = page.context
            await context.close()
        except Exception as e:
            logger.debug(f"Error releasing page: {e}")

    async def _rpa_goto(self, page: Any, url: str, **kwargs) -> dict:
        wait_time = kwargs.pop("wait_time", 3)
        await page.goto(url, **kwargs)
        await asyncio.sleep(wait_time)
        return {"url": page.url, "title": await page.title()}

    async def _rpa_click(self, page: Any, selector: str, **kwargs) -> dict:
        wait_time = kwargs.pop("wait_time", 1)
        await page.click(selector, **kwargs)
        await asyncio.sleep(wait_time)
        return {"success": True}

    async def _rpa_fill(self, page: Any, selector: str, value: str, **kwargs) -> dict:
        wait_time = kwargs.pop("wait_time", 0.5)
        await page.fill(selector, value, **kwargs)
        await asyncio.sleep(wait_time)
        return {"success": True}

    async def _rpa_evaluate(self, page: Any, js_code: str, **kwargs) -> Any:
        return await page.evaluate(js_code, **kwargs)

    async def _rpa_screenshot(self, page: Any, path: str, **kwargs) -> dict:
        full_page = kwargs.pop("full_page", False)
        await page.screenshot(path=path, full_page=full_page, **kwargs)
        return {"saved_to": path}

    async def health_check(self) -> bool:
        """检查 Playwright 是否可用"""
        try:
            pw = __import__("playwright", fromlist=["async_"]).async_
            return True
        except ImportError:
            return False
