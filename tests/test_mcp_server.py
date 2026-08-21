import pytest
from src.server.mcp_server import heal_selector
from src.types import settings, HealedSelectorResponse

@pytest.mark.asyncio
async def test_heal_selector_tool_mock_mode():
    # Ensure mock mode is active for this test
    old_mock = settings.awarse_mock_heal
    settings.awarse_mock_heal = True
    
    try:
        # Invoke the FastMCP tool handler directly
        response = await heal_selector(
            broken_selector="#submit-btn",
            error_message="Page.click: Timeout 1000ms exceeded.",
            dom_snapshot="<html><body><button id='healed-submit-action-button'>Submit</button></body></html>",
            target_url="http://localhost/test.html"
        )
        
        # Verify the schema and values returned
        assert isinstance(response, HealedSelectorResponse)
        assert response.proposed_selector == "#healed-submit-action-button"
        assert response.confidence_score == 1.0
        assert "Simulated healing" in response.rationale
        assert response.verification_status == "verified_unique"
        assert len(response.fallback_selectors) == 2
        assert response.fallback_selectors[0] == "button[type='submit']"
    finally:
        settings.awarse_mock_heal = old_mock
