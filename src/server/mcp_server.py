import sys
import atexit
import asyncio
from mcp.server.fastmcp import FastMCP
from src.types import settings, HealedSelectorResponse
from src.engine import GeminiHealerClient
from src.sandbox import SandboxVerifier
from src.ast import patch_source_file

# Initialize FastMCP Server
mcp = FastMCP("awarse-healer")

# Initialize Healer Client and Sandbox Verifier
healer_client = GeminiHealerClient()
verifier = SandboxVerifier()

@mcp.tool()
async def heal_selector(
    broken_selector: str,
    error_message: str,
    dom_snapshot: str,  # represents ARIA tree snapshot
    target_url: str = None,
    file_path: str = None,
    line_number: int = None,
    column_number: int = None
) -> HealedSelectorResponse:
    """
    Exposes heal_selector MCP tool. Takes failed selector, error, ARIA layout,
    evaluates candidates in Playwright sandbox, updates source file AST if coordinates provided.
    """
    print(f"[MCP Tool] heal_selector invoked for locator '{broken_selector}'")
    
    # 1. Query Gemini using the ARIA tree layout
    gemini_resp = await healer_client.get_healed_selector(
        broken_selector=broken_selector,
        error_message=error_message,
        dom_snapshot=dom_snapshot,
        target_url=target_url
    )
    
    # 2. Verify locator expression inside the headless Playwright sandbox
    resolved_locator, verification_status = await verifier.verify_and_resolve_locator(
        dom_snapshot=dom_snapshot,
        proposed_locator=gemini_resp.proposed_playwright_call,
        fallback_expression=gemini_resp.fallback_expression
    )
    
    # 3. If file path coordinates are provided and verification succeeds, apply AST/source code patch
    if file_path and line_number is not None and verification_status == "verified_unique":
        print(f"[MCP Server] Verification succeeded. Invoking AST patcher for {file_path}:{line_number}...")
        # Note: resolved_locator is the verified call expression
        patch_source_file(file_path, line_number, column_number, resolved_locator)
    
    # 4. Construct final response mapping
    return HealedSelectorResponse(
        proposed_playwright_call=resolved_locator,
        selector_type=gemini_resp.selector_type,
        confidence_score=gemini_resp.confidence_score,
        rationale=gemini_resp.rationale,
        fallback_expression=gemini_resp.fallback_expression,
        verification_status=verification_status
    )

def shutdown_server():
    """Cleanup hook to gracefully shut down the sandbox verifier browser."""
    print("[MCP Server] Shutting down AWARSE Healer Server...")
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(verifier.close())
        else:
            loop.run_until_complete(verifier.close())
    except Exception:
        try:
            asyncio.run(verifier.close())
        except Exception:
            pass

atexit.register(shutdown_server)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "sse":
        print(f"[*] Starting AWARSE Healer Server in SSE Mode on http://{settings.awarse_host}:{settings.awarse_port}")
        mcp.run(
            transport="sse",
            host=settings.awarse_host,
            port=settings.awarse_port
        )
    else:
        print("[*] Starting AWARSE Healer Server in Stdio Mode...")
        mcp.run(transport="stdio")
