import re
import asyncio
from playwright.async_api import async_playwright, Playwright, Browser, Page
from src.types import settings

def translate_locator_to_python(expr: str) -> str:
    """
    Translates a TS-style or Python-style Playwright locator expression into executable Python code.
    Examples:
      - "page.getByRole('button', { name: 'Sign In', exact: true })"
        -> "page.get_by_role('button', name='Sign In', exact=True)"
      - "page.locator('button').and(page.locator('.submit'))"
        -> "page.locator('button').and_(page.locator('.submit'))"
    """
    # 1. Map standard JS camelCase locator methods to Python snake_case equivalents
    methods_map = {
        "getByRole": "get_by_role",
        "getByText": "get_by_text",
        "getByLabel": "get_by_label",
        "getByPlaceholder": "get_by_placeholder",
        "getByAltText": "get_by_alt_text",
        "getByTitle": "get_by_title",
        "getByTestId": "get_by_test_id",
        "frameLocator": "frame_locator",
        # Match standard method boundaries for logical operations
        ".and(": ".and_(",
        ".or(": ".or_(",
    }
    
    out = expr
    for ts_name, py_name in methods_map.items():
        out = out.replace(ts_name, py_name)
        
    # 2. Convert JS-style options object literals { name: '...', exact: true } to Python kwargs
    def object_replacer(match):
        content = match.group(1)
        # Extract pairs matching key: value where value is string, boolean, or number
        items = re.findall(r'([a-zA-Z0-9_]+)\s*:\s*(\'[^\\\']*\'|"[^\\"]*"|true|false|[0-9.]+)', content)
        pairs = []
        for k, v in items:
            if v == "true":
                v = "True"
            elif v == "false":
                v = "False"
            pairs.append(f"{k}={v}")
        return ", ".join(pairs)

    # Match inner braces { ... }
    out = re.sub(r'\{\s*([^{}]+)\s*\}', object_replacer, out)
    # Clean redundant commas that might have resulted from conversion
    out = re.sub(r',\s*,', ',', out)
    
    return out

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

    async def verify_locator_expression(self, dom_snapshot: str, expression: str) -> bool:
        """
        Loads the DOM snapshot or ARIA snapshot into a sandboxed page and checks if the locator
        expression is unique (count == 1) and visible.
        """
        if settings.healwright_mock_heal:
            # Under mock heal mode, simulate uniqueness check for verification target
            return "Submit" in expression or "Username" in expression or "healed" in expression

        await self._ensure_browser()
        context = await self._browser.new_context()
        page = await context.new_page()
        try:
            # Load sanitized DOM content
            await page.set_content(dom_snapshot)
            try:
                py_expression = translate_locator_to_python(expression)
                # Safely evaluate Playwright locator expression on sandboxed page
                locator = eval(py_expression, {"page": page})
                count = await locator.count()
                if count == 1:
                    # Check if the element is visible
                    return await locator.is_visible()
                return False
            except Exception as e:
                print(f"[SandboxVerifier] Locator evaluation failed for '{expression}' [py: '{py_expression}']: {e}")
                return False
        finally:
            await page.close()
            await context.close()

    async def verify_and_resolve_locator(
        self,
        dom_snapshot: str,
        proposed_locator: str,
        fallback_expression: str
    ) -> tuple[str, str]:
        """
        Evaluates the proposed Playwright locator and the fallback expression.
        Returns a tuple of (resolved_locator, status).
        """
        if settings.healwright_mock_heal:
            print("[SandboxVerifier] MOCK MODE ACTIVE: Bypassing browser verification, assuming verified_unique.")
            return proposed_locator, "verified_unique"

        # 1. Try proposed locator
        print(f"[SandboxVerifier] Verifying proposed locator: '{proposed_locator}'")
        if await self.verify_locator_expression(dom_snapshot, proposed_locator):
            return proposed_locator, "verified_unique"
        
        # Get count for classification
        proposed_count = 0
        try:
            py_expr = translate_locator_to_python(proposed_locator)
            proposed_count = await self._get_locator_count(dom_snapshot, py_expr)
        except:
            pass

        # 2. Try fallback expression
        print(f"[SandboxVerifier] Verifying fallback expression: '{fallback_expression}'")
        if await self.verify_locator_expression(dom_snapshot, fallback_expression):
            return fallback_expression, "verified_unique"
        
        fallback_count = 0
        try:
            py_expr = translate_locator_to_python(fallback_expression)
            fallback_count = await self._get_locator_count(dom_snapshot, py_expr)
        except:
            pass

        # Classify the failure status
        if proposed_count > 1 or fallback_count > 1:
            if proposed_count > 1:
                return proposed_locator, "ambiguous_match"
            return fallback_expression, "ambiguous_match"

        return proposed_locator, "failed"

    async def _get_locator_count(self, dom_snapshot: str, py_expression: str) -> int:
        await self._ensure_browser()
        context = await self._browser.new_context()
        page = await context.new_page()
        try:
            await page.set_content(dom_snapshot)
            locator = eval(py_expression, {"page": page})
            return await locator.count()
        finally:
            await page.close()
            await context.close()
