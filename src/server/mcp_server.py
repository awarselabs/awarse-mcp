import sys
from mcp.server.fastmcp import FastMCP
from src.types import settings, HealedSelectorResponse
from src.engine import sanitize_dom_snapshot, GeminiHealerClient
from src.sandbox import SandboxVerifier

# Initialize FastMCP Server
mcp = FastMCP("awarse-healer")

# Initialize Healer Client and Sandbox Verifier
healer_client = GeminiHealerClient()
verifier = SandboxVerifier()

@mcp.tool()
async def heal_selector(
    broken_selector: str,
    error_message: str,
    dom_snapshot: str,
    target_url: str = None
) -> HealedSelectorResponse:
    """
    MCP Tool to analyze a broken Playwright selector, sanitize the DOM snapshot,
    query Gemini to identify replacement selector candidates, verify their uniqueness
    in a sandboxed headless browser, and return a verified patch.
    """
    print(f"[MCP Tool] heal_selector invoked for selector '{broken_selector}'")
    
    # 1. Sanitize DOM snapshot to save tokens
    sanitized_dom = sanitize_dom_snapshot(dom_snapshot)
    
    # 2. Query Gemini for healed candidates
    gemini_resp = await healer_client.get_healed_selector(
        broken_selector=broken_selector,
        error_message=error_message,
        sanitized_dom=sanitized_dom,
        target_url=target_url
    )
    
    # 3. Verify selector candidates in sandbox
    resolved_selector, verification_status = await verifier.verify_and_resolve_selector(
        dom_snapshot=sanitized_dom,
        proposed_selector=gemini_resp.proposed_selector,
        fallback_selectors=gemini_resp.fallback_selectors
    )
    
    # 4. Construct final response
    return HealedSelectorResponse(
        proposed_selector=resolved_selector,
        confidence_score=gemini_resp.confidence_score,
        rationale=gemini_resp.rationale,
        fallback_selectors=gemini_resp.fallback_selectors,
        verification_status=verification_status
    )

import atexit
import asyncio

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
    # Handle command-line transport arguments
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
