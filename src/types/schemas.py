from pydantic import BaseModel, Field
from typing import List, Optional

class GeminiHealResponse(BaseModel):
    proposed_playwright_call: str = Field(
        ...,
        description="The primary Playwright locator expression (e.g. page.get_by_role('button', name='Sign In') or page.get_by_test_id('submit'))."
    )
    selector_type: str = Field(
        ...,
        description="The type of selector chosen. Must be one of: 'role', 'testid', 'chained_or', 'css'."
    )
    confidence_score: float = Field(
        ...,
        description="Confidence score (from 0.0 to 1.0) indicating how likely this locator matches the intended element."
    )
    rationale: str = Field(
        ...,
        description="Explanation of why the original selector failed and why this Playwright locator is recommended."
    )
    fallback_expression: str = Field(
        ...,
        description="An alternative Playwright locator expression (e.g. using a different role, placeholder, text, or a chained .or() condition)."
    )

class HealedSelectorResponse(GeminiHealResponse):
    verification_status: str = Field(
        ...,
        description="The verification status of the selector. Must be one of: 'verified_unique', 'ambiguous_match', or 'failed'."
    )
