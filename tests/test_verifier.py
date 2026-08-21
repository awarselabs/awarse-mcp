import pytest
from src.sandbox.verifier import SandboxVerifier
from src.types import settings

@pytest.mark.asyncio
async def test_sandbox_verifier_unique_element():
    # Make sure we run with real Playwright for this verification test
    old_mock = settings.awarse_mock_heal
    settings.awarse_mock_heal = False
    
    verifier = SandboxVerifier()
    dom_snapshot = "<html><body><button id='unique-btn'>Click me</button></body></html>"
    try:
        # Verify uniqueness
        is_unique = await verifier.verify_selector(dom_snapshot, "#unique-btn")
        assert is_unique is True
        
        # Verify non-existent element
        is_unique_fake = await verifier.verify_selector(dom_snapshot, "#fake-btn")
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
        is_unique = await verifier.verify_selector(dom_snapshot, ".btn")
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
        # Proposed is duplicate, fallbacks contains the unique correct one
        resolved, status = await verifier.verify_and_resolve_selector(
            dom_snapshot=dom_snapshot,
            proposed_selector=".duplicate",
            fallback_selectors=["#fake-btn", "#correct-btn"]
        )
        assert resolved == "#correct-btn"
        assert status == "verified_unique"
    finally:
        await verifier.close()
        settings.awarse_mock_heal = old_mock
