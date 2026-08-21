import json
import traceback
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Launch parameters for local AWARSE MCP server
server_parameters = StdioServerParameters(
    command="venv/bin/python",
    args=["src/server/mcp_server.py"]
)

@pytest.fixture
async def smart_page(page):
    """
    pytest fixture wrapping Playwright page.
    Captures ARIA accessibility snapshots, extracts traceback call coordinates,
    invokes AWARSE MCP over stdio to heal selector and patch spec file via AST,
    and dynamically evaluates the new locator call at runtime.
    """
    async with stdio_client(server_parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("[smart_page] Connected to local AWARSE MCP server.")

            class SmartPageWrapper:
                def __init__(self, page_instance):
                    self._page = page_instance

                def __getattr__(self, name):
                    return getattr(self._page, name)

                async def click(self, selector: str, timeout: int = 3000, **kwargs):
                    try:
                        await self._page.click(selector, timeout=timeout, **kwargs)
                    except Exception as err:
                        print(f"[SmartPage] Click failed on '{selector}'. Running self-healing...")
                        
                        # 1. Capture compact ARIA snapshot
                        aria_snapshot = await self._page.aria_snapshot()
                        url = self._page.url

                        # 2. Extract spec file coordinates from the exception traceback
                        file_path, line, col = parse_traceback_coordinates(err)
                        print(f"[SmartPage] Error coordinates: {file_path}:{line}:{col}")

                        # 3. Call heal_selector tool
                        result = await session.call_tool(
                            "heal_selector",
                            arguments={
                                "broken_selector": selector,
                                "error_message": str(err),
                                "dom_snapshot": aria_snapshot,
                                "target_url": url,
                                "file_path": file_path,
                                "line_number": line,
                                "column_number": col
                            }
                        )

                        # Parse response JSON
                        healing_patch = json.loads(result.content[0].text)
                        resolved_call = healing_patch["proposed_playwright_call"]
                        status = healing_patch["verification_status"]

                        print(f"[SmartPage] Healed locator call: '{resolved_call}' (status: {status})")
                        
                        if status == "failed":
                            print("[SmartPage] Self-healing failed. Re-throwing exception.")
                            raise err

                        # 4. Evaluate the healed Playwright locator call expression dynamically in Python
                        healed_locator = eval(resolved_call, {"page": self._page})
                        
                        # Retry the click using the resolved locator
                        await healed_locator.click(timeout=timeout, **kwargs)

                async def fill(self, selector: str, value: str, timeout: int = 3000, **kwargs):
                    try:
                        await self._page.fill(selector, value, timeout=timeout, **kwargs)
                    except Exception as err:
                        print(f"[SmartPage] Fill failed on '{selector}'. Running self-healing...")
                        
                        aria_snapshot = await self._page.aria_snapshot()
                        url = self._page.url
                        file_path, line, col = parse_traceback_coordinates(err)

                        result = await session.call_tool(
                            "heal_selector",
                            arguments={
                                "broken_selector": selector,
                                "error_message": str(err),
                                "dom_snapshot": aria_snapshot,
                                "target_url": url,
                                "file_path": file_path,
                                "line_number": line,
                                "column_number": col
                            }
                        )

                        healing_patch = json.loads(result.content[0].text)
                        resolved_call = healing_patch["proposed_playwright_call"]
                        status = healing_patch["verification_status"]

                        print(f"[SmartPage] Healed locator call: '{resolved_call}' (status: {status})")

                        if status == "failed":
                            raise err

                        healed_locator = eval(resolved_call, {"page": self._page})
                        await healed_locator.fill(value, timeout=timeout, **kwargs)

            yield SmartPageWrapper(page)

def parse_traceback_coordinates(err: Exception) -> tuple[str, int, int]:
    """
    Traverses exception traceback frames to locate the line and file of the test spec.
    """
    tb = err.__traceback__
    while tb:
        frame = tb.tb_frame
        filename = frame.f_code.co_filename
        # Identify files corresponding to tests/specs
        if filename.endswith(".spec.py") or filename.endswith("_test.py") or "test_" in filename:
            # col is offset to 0 as python tracebacks do not store column positions natively
            return filename, tb.tb_lineno, 0
        tb = tb.tb_next
    return None, None, None
