import json
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Stdio launching parameters to communicate with local AWARSE MCP server
server_parameters = StdioServerParameters(
    command="venv/bin/python",
    args=["src/server/mcp_server.py"]
)

@pytest.fixture
async def smart_page(page):
    """
    pytest fixture wrapping Playwright page.
    Intercepts Click and Fill action failures, triggers AWARSE MCP tool over Stdio,
    heals the selector, and retries the action.
    """
    async with stdio_client(server_parameters) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize MCP session
            await session.initialize()
            print("[smart_page Fixture] Initialized connection to local AWARSE MCP server.")

            class SmartPageWrapper:
                def __init__(self, page_instance):
                    self._page = page_instance

                def __getattr__(self, name):
                    # Fallback to the default Playwright page attributes/methods
                    return getattr(self._page, name)

                async def click(self, selector: str, timeout: int = 3000, **kwargs):
                    try:
                        await self._page.click(selector, timeout=timeout, **kwargs)
                    except Exception as err:
                        print(f"[SmartPage] Click failed on '{selector}'. Running self-healing...")
                        dom_snapshot = await self._page.content()

                        # Call heal_selector tool
                        result = await session.call_tool(
                            "heal_selector",
                            arguments={
                                "broken_selector": selector,
                                "error_message": str(err),
                                "dom_snapshot": dom_snapshot,
                                "target_url": self._page.url
                            }
                        )

                        # Parse response JSON
                        healing_patch = json.loads(result.content[0].text)
                        resolved_selector = healing_patch["proposed_selector"]
                        status = healing_patch["verification_status"]

                        print(f"[SmartPage] Healed selector: '{resolved_selector}' (status: {status})")
                        
                        if status == "failed":
                            print("[SmartPage] Self-healing failed. Re-throwing exception.")
                            raise err

                        # Retry the click using the verified selector
                        await self._page.click(resolved_selector, timeout=timeout, **kwargs)

                async def fill(self, selector: str, value: str, timeout: int = 3000, **kwargs):
                    try:
                        await self._page.fill(selector, value, timeout=timeout, **kwargs)
                    except Exception as err:
                        print(f"[SmartPage] Fill failed on '{selector}'. Running self-healing...")
                        dom_snapshot = await self._page.content()

                        result = await session.call_tool(
                            "heal_selector",
                            arguments={
                                "broken_selector": selector,
                                "error_message": str(err),
                                "dom_snapshot": dom_snapshot,
                                "target_url": self._page.url
                            }
                        )

                        healing_patch = json.loads(result.content[0].text)
                        resolved_selector = healing_patch["proposed_selector"]
                        status = healing_patch["verification_status"]

                        print(f"[SmartPage] Healed selector: '{resolved_selector}' (status: {status})")

                        if status == "failed":
                            raise err

                        await self._page.fill(resolved_selector, value, timeout=timeout, **kwargs)

            # Inject the wrapper to tests
            yield SmartPageWrapper(page)
