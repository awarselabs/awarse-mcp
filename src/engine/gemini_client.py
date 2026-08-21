import os
import json
from google import genai
from google.genai import types as genai_types
from src.types import settings, GeminiHealResponse

class GeminiHealerClient:
    def __init__(self):
        self.model = settings.gemini_model
        self._client = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            api_key = settings.gemini_api_key
            if not api_key:
                # If mock mode is not active, raise an error
                if not settings.awarse_mock_heal:
                    raise ValueError(
                        "GEMINI_API_KEY is not configured in settings. "
                        "Please set the GEMINI_API_KEY environment variable or configured in .env."
                    )
            self._client = genai.Client(api_key=api_key)
        return self._client

    async def get_healed_selector(
        self,
        broken_selector: str,
        error_message: str,
        dom_snapshot: str,  # Ingests the ARIA snapshot or HTML DOM
        target_url: str = None
    ) -> GeminiHealResponse:
        """
        Sends the healing request to Gemini using Structured Outputs and low temperature.
        If AWARSE_MOCK_HEAL is True, returns a mock healing patch directly.
        """
        if settings.awarse_mock_heal:
            print("[GeminiHealerClient] MOCK MODE ACTIVE: Returning mock healing response.")
            if broken_selector == "#submit-btn":
                return GeminiHealResponse(
                    proposed_playwright_call="page.get_by_role('button', name='Submit')",
                    selector_type="role",
                    confidence_score=1.0,
                    rationale="Simulated healing: element selector changed from '#submit-btn' to a stable role locator.",
                    fallback_expression="page.locator('#healed-submit-action-button')"
                )
            elif broken_selector == ".broken-username":
                return GeminiHealResponse(
                    proposed_playwright_call="page.get_by_placeholder('Username')",
                    selector_type="role",
                    confidence_score=1.0,
                    rationale="Simulated username field healing.",
                    fallback_expression="page.get_by_label('Username')"
                )
            else:
                return GeminiHealResponse(
                    proposed_playwright_call=f"page.locator('{broken_selector}')",
                    selector_type="css",
                    confidence_score=0.5,
                    rationale="Simulated fallback.",
                    fallback_expression=f"page.locator('{broken_selector}')"
                )

        # Build prompt
        prompt = f"""You are the self-healing engine of AWARSE (Autonomous Web-Automation Runtime Self-Healing Engine).
An automation action has failed because the locator could not be resolved.
Your task is to analyze the runtime context and the page's ARIA tree layout to identify the most resilient replacement locator.

### Context:
- Target URL: {target_url or 'Unknown'}
- Failed Selector / Expression: {broken_selector}
- Runtime Exception Details: {error_message}

### Page ARIA Snapshot (YAML / Compact Tree representation):
```yaml
{dom_snapshot}
```

### Locator Heuristics Strategy Rules (Strict Order of Preference):
1. **Accessibility Roles (`getByRole`)**: Use `page.getByRole(role, {{ name: '...' }})` or `page.getByRole(role, {{ description: '...' }})`. This is the most resilient strategy.
2. **Standard Label/Placeholder/TestID Locators**: Use `page.getByTestId()`, `page.getByLabel()`, or `page.getByPlaceholder()`.
3. **Resilient Chained Selectors**: Use `.or()` to chain fallbacks (e.g. `page.getByRole('button', {{ name: 'Submit' }}).or(page.locator('#healed-submit'))`).
4. **Stable CSS/XPath**: Use standard locators like `page.locator('button.submit-action')` ONLY if no accessible roles or text anchors are available.

Return your response strictly adhering to the JSON schema. Use standard Python/TS Playwright expression syntax for the proposed locator.
"""

        # Call Gemini using official SDK
        config = genai_types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GeminiHealResponse,
            temperature=0.1,
            system_instruction="You are an expert SDET and systems architect specializing in Playwright automation. You output ONLY valid JSON adhering to the specified schema."
        )

        import asyncio
        loop = asyncio.get_event_loop()
        
        response = await loop.run_in_executor(
            None,
            lambda: self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )
        )
        
        response_text = response.text.strip()
        data = json.loads(response_text)
        return GeminiHealResponse(**data)
