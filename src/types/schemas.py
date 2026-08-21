from pydantic import BaseModel, Field
from typing import List, Optional

class GeminiHealResponse(BaseModel):
    proposed_selector: str = Field(
        ...,
        description="The primary healed CSS, XPath, or Playwright selector to locate the target element."
    )
    confidence_score: float = Field(
        ...,
        description="Confidence score (from 0.0 to 1.0) indicating how likely this selector matches the intended element."
    )
    rationale: str = Field(
        ...,
        description="Detailed explanation of why the original selector failed and why this replacement selector is recommended."
    )
    fallback_selectors: List[str] = Field(
        ...,
        description="A list of exactly two alternative selectors (e.g. text-based, role-based, or test-id) in case the proposed one fails."
    )

class HealedSelectorResponse(GeminiHealResponse):
    verification_status: str = Field(
        ...,
        description="The verification status of the selector. Must be one of: 'verified_unique', 'ambiguous_match', or 'failed'."
    )
