import pytest
from src.sandbox.verifier import SandboxVerifier
from src.types import settings

@pytest.mark.asyncio
async def test_sandbox_verifier_unique_element():
    old_mock = settings.awarse_mock_heal
    settings.awarse_mock_heal = False
    
    verifier = SandboxVerifier()
    dom_snapshot = "<html><body><button id='unique-btn'>Click me</button></body></html>"
    try:
        # Verify uniqueness using valid Playwright expression
        is_unique = await verifier.verify_locator_expression(dom_snapshot, "page.locator('#unique-btn')")
        assert is_unique is True
        
        # Verify non-existent element
        is_unique_fake = await verifier.verify_locator_expression(dom_snapshot, "page.locator('#fake-btn')")
        assert is_unique_fake is False
    finally:
        await verifier.close()
        settings.awarse_mock_heal = old_mock

@pytest.mark.asyncio
async def test_sandbox_verifier_duplicate_elements():
    old_mock = settings.awarse_mock_heal
    settings.awarse_mock_heal = False
    
    verifier = SandboxVerifier()
    dom_snapshot = "<html><body><button class='btn'>Btn 1</button><button class='btn'>Btn 2</button></body></html>"
    try:
        # Non-unique (duplicate match count == 2)
        is_unique = await verifier.verify_locator_expression(dom_snapshot, "page.locator('.btn')")
        assert is_unique is False
    finally:
        await verifier.close()
        settings.awarse_mock_heal = old_mock

@pytest.mark.asyncio
async def test_sandbox_verifier_resolve_fallbacks():
    old_mock = settings.awarse_mock_heal
    settings.awarse_mock_heal = False
    
    verifier = SandboxVerifier()
    dom_snapshot = """
    <html>
      <body>
        <div class="buttons">
          <button class="btn duplicate">Duplicate 1</button>
          <button class="btn duplicate">Duplicate 2</button>
          <button id="correct-btn">Unique Target</button>
        </div>
      </body>
    </html>
    """
    try:
        # Proposed is duplicate, fallback contains the unique correct one
        resolved, status = await verifier.verify_and_resolve_locator(
            dom_snapshot=dom_snapshot,
            proposed_locator="page.locator('.duplicate')",
            fallback_expression="page.locator('#correct-btn')"
        )
        assert resolved == "page.locator('#correct-btn')"
        assert status == "verified_unique"
    finally:
        await verifier.close()
        settings.awarse_mock_heal = old_mock
