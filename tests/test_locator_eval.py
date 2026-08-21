import pytest
from src.sandbox.verifier import translate_locator_to_python, SandboxVerifier
from src.types import settings

def test_translate_locator_to_python():
    # Test method translation and JS options object conversion
    ts_expr1 = "page.getByRole('button', { name: 'Sign In', exact: true })"
    py_expr1 = translate_locator_to_python(ts_expr1)
    assert py_expr1 == "page.get_by_role('button', name='Sign In', exact=True)"

    # Test nested arguments and string matching
    ts_expr2 = "page.getByPlaceholder('Username', { exact: false })"
    py_expr2 = translate_locator_to_python(ts_expr2)
    assert py_expr2 == "page.get_by_placeholder('Username', exact=False)"

    # Test logical operators conversion (and -> and_, or -> or_)
    ts_expr3 = "page.locator('button').and(page.locator('.submit'))"
    py_expr3 = translate_locator_to_python(ts_expr3)
    assert py_expr3 == "page.locator('button').and_(page.locator('.submit'))"

    # Test already Python-style call returns unchanged
    py_expr_native = "page.get_by_role('button', name='Submit')"
    assert translate_locator_to_python(py_expr_native) == py_expr_native

@pytest.mark.asyncio
async def test_sandbox_verifier_with_locator_expressions():
    old_mock = settings.awarse_mock_heal
    settings.awarse_mock_heal = False

    verifier = SandboxVerifier()
    dom_snapshot = "<html><body><button id='healed-submit-btn' name='submit-action'>Submit Form</button></body></html>"
    try:
        # Test dynamic evaluation of getByRole expression on Page context
        res = await verifier.verify_locator_expression(dom_snapshot, "page.getByRole('button', { name: 'Submit Form' })")
        assert res is True

        # Test evaluation with mismatched parameters (returns False)
        res_fake = await verifier.verify_locator_expression(dom_snapshot, "page.getByRole('button', { name: 'Sign In' })")
        assert res_fake is False
    finally:
        await verifier.close()
        settings.awarse_mock_heal = old_mock
