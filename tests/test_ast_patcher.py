import os
import pytest
from src.ast import patch_source_file

def test_ast_patcher_python_file(tmp_path):
    # 1. Setup temporary Python spec file
    code = """# Test spec file
import pytest

async def test_form(page):
    await page.locator("#submit-btn").click()
    print("Verification Done")
"""
    file_path = tmp_path / "test_form.spec.py"
    file_path.write_text(code, encoding="utf-8")
    
    # 2. Patch line 5, col 10 (spans page.locator("#submit-btn"))
    patched = patch_source_file(
        file_path=str(file_path),
        line=5,
        col=10,
        replacement="page.get_by_role('button', name='Submit')"
    )
    
    assert patched is True
    patched_code = file_path.read_text(encoding="utf-8")
    assert "page.get_by_role('button', name='Submit')" in patched_code
    assert "#submit-btn" not in patched_code
    assert 'print("Verification Done")' in patched_code  # Ensure structural formatting remains intact

def test_ast_patcher_typescript_file(tmp_path):
    # 1. Setup temporary TypeScript spec file
    code = """import { test } from '@playwright/test';

test('click test', async ({ page }) => {
  await page.locator('#submit-btn').click();
});
"""
    file_path = tmp_path / "click.spec.ts"
    file_path.write_text(code, encoding="utf-8")
    
    # 2. Patch line 4, col 8 (spans page.locator('#submit-btn'))
    # This checks coordinate matching and falls back to balanced bracket slice if Babel isn't local.
    patched = patch_source_file(
        file_path=str(file_path),
        line=4,
        col=8,
        replacement="page.getByRole('button', { name: 'Submit' })"
    )
    
    assert patched is True
    patched_code = file_path.read_text(encoding="utf-8")
    assert "page.getByRole('button', { name: 'Submit' })" in patched_code
    assert "#submit-btn" not in patched_code
