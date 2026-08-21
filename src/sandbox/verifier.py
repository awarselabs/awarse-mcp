import asyncio
from playwright.async_api import async_playwright, Playwright, Browser, Page
from src.types import settings

class SandboxVerifier:
    def __init__(self):
        self._playwright: Playwright = None
        self._browser: Browser = None
        self._lock = asyncio.Lock()

    async def _ensure_browser(self):
        async with self._lock:
            if self._browser is None:
                print("[SandboxVerifier] Starting headless Playwright Chromium instance...")
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(headless=True)

    async def close(self):
        async with self._lock:
            if self._browser:
                print("[SandboxVerifier] Shutting down Playwright Chromium instance...")
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

    async def verify_selector(self, dom_snapshot: str, selector: str) -> bool:
        """
        Loads the DOM snapshot into a sandboxed page and checks if the selector is unique (count == 1).
        """
        if settings.awarse_mock_heal:
            # Under mock heal mode, simulate uniqueness check for verification target
            return selector in ("#healed-submit-action-button", "#username")

        await self._ensure_browser()
        context = await self._browser.new_context()
        page = await context.new_page()
        try:
            await page.set_content(dom_snapshot)
            try:
                count = await page.locator(selector).count()
                return count == 1
            except Exception as e:
                print(f"[SandboxVerifier] Selector '{selector}' threw syntax error or failed count: {e}")
                return False
        finally:
            await page.close()
            await context.close()

    async def verify_and_resolve_selector(
        self,
        dom_snapshot: str,
        proposed_selector: str,
        fallback_selectors: list
    ) -> tuple[str, str]:
        """
        Evaluates the proposed selector and fallbacks.
        Returns a tuple of (resolved_selector, status).
        Statuses:
        - "verified_unique": if one selector matched exactly 1 element.
        - "ambiguous_match": if selectors match multiple elements.
        - "failed": if no selectors match any elements.
        """
        if settings.awarse_mock_heal:
            print("[SandboxVerifier] MOCK MODE ACTIVE: Bypassing browser verification, assuming verified_unique.")
            return proposed_selector, "verified_unique"

        # 1. Try proposed selector
        print(f"[SandboxVerifier] Verifying proposed selector: '{proposed_selector}'")
        if await self.verify_selector(dom_snapshot, proposed_selector):
            return proposed_selector, "verified_unique"
        
        # Get count for classification
        proposed_count = 0
        try:
            proposed_count = await self._get_count(dom_snapshot, proposed_selector)
        except:
            pass

        # 2. Try fallback selectors
        fallback_results = []
        for idx, fallback in enumerate(fallback_selectors):
            print(f"[SandboxVerifier] Proposing fallback #{idx + 1}: '{fallback}'")
            if await self.verify_selector(dom_snapshot, fallback):
                return fallback, "verified_unique"
            try:
                fallback_count = await self._get_count(dom_snapshot, fallback)
                fallback_results.append(fallback_count)
            except:
                fallback_results.append(0)

        # None matched exactly 1 element. Classify the failure.
        if proposed_count > 1 or any(count > 1 for count in fallback_results):
            # Recommend the first selector that was ambiguous (matched multiple)
            if proposed_count > 1:
                return proposed_selector, "ambiguous_match"
            for idx, count in enumerate(fallback_results):
                if count > 1:
                    return fallback_selectors[idx], "ambiguous_match"

        # No match at all
        return proposed_selector, "failed"

    async def _get_count(self, dom_snapshot: str, selector: str) -> int:
        await self._ensure_browser()
        context = await self._browser.new_context()
        page = await context.new_page()
        try:
            await page.set_content(dom_snapshot)
            return await page.locator(selector).count()
        finally:
            await page.close()
            await context.close()
