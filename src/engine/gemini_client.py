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
        sanitized_dom: str,
        target_url: str = None
    ) -> GeminiHealResponse:
        """
        Sends the healing request to Gemini using Structured Outputs and low temperature.
        If AWARSE_MOCK_HEAL is True, returns a mock healing patch directly.
        """
        if settings.awarse_mock_heal:
            # Simulated response for verification and testing
            print("[GeminiHealerClient] MOCK MODE ACTIVE: Returning mock healing response.")
            # Customize mock response depending on broken selector for more robust testing
            if broken_selector == "#submit-btn":
                return GeminiHealResponse(
                    proposed_selector="#healed-submit-action-button",
                    confidence_score=1.0,
                    rationale="Simulated healing: element selector changed from '#submit-btn' to '#healed-submit-action-button' due to DOM mutation.",
                    fallback_selectors=["button[type='submit']", "button:has-text('Submit')"]
                )
            elif broken_selector == ".broken-username":
                return GeminiHealResponse(
                    proposed_selector="#username",
                    confidence_score=1.0,
                    rationale="Simulated username field healing.",
                    fallback_selectors=["input[name='username']", "input[placeholder='Username']"]
                )
            else:
                return GeminiHealResponse(
                    proposed_selector=broken_selector,
                    confidence_score=0.5,
                    rationale="Simulated fallback (no-op).",
                    fallback_selectors=[broken_selector, broken_selector]
                )

        # Build prompt
        prompt = f"""You are the self-healing engine of AWARSE (Autonomous Web-Automation Runtime Self-Healing Engine).
An automation selector has failed at runtime. Your task is to identify the best replacement selector based on the target element's context in the sanitized DOM snapshot.

### Context:
- Target URL: {target_url or 'Unknown'}
- Failed Selector: {broken_selector}
- Error Message: {error_message}

### Sanitized DOM Snapshot:
```html
{sanitized_dom}
```

### Guidelines for Selector Generation:
1. Prioritize resilient locating strategies:
   - Use stable accessibility identifiers (e.g. Playwright 'getByRole', 'getByLabel', 'getByPlaceholder', 'getByText', or 'getByTestId').
   - Use persistent 'data-testid' or 'data-test' attributes.
   - Use stable text anchors and element types.
   - Avoid brittle selectors like auto-generated Tailwind class hashes, absolute XPaths, or index-dependent paths.
2. Ensure you propose a primary selector ('proposed_selector') and exactly two distinct 'fallback_selectors'.
3. Provide a clear rationale describing what broke (e.g., dynamic class changes, element restructuring) and why the new selector was chosen.

Provide your response strictly conforming to the JSON schema.
"""

        # Call Gemini using official SDK
        config = genai_types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GeminiHealResponse,
            temperature=0.1,
            system_instruction="You are a senior SDET and expert web-automation engineer. You always output valid JSON adhering to the specified schema."
        )

        # google-genai client does synchronous calls via model.generate_content.
        # We wrap in asyncio.to_thread to prevent blocking the async event loop.
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
        
        # Parse the structured response
        response_text = response.text.strip()
        
        # Parse text into Pydantic model
        data = json.loads(response_text)
        return GeminiHealResponse(**data)
