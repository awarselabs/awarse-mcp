Output demo.gif
Set FontSize 15
Set Width 920
Set Height 540
Set Theme "tokyonight"
Set Padding 20

Type "pytest tests/test_checkout.py"
Enter
Sleep 1s

Type "============================= test session starts ============================="
Enter
Type "platform linux -- Python 3.11.9, pytest-8.1.1, pluggy-1.4.0"
Enter
Type "rootdir: /app"
Enter
Type "plugins: healwright-0.1.0"
Enter
Type "collected 1 item"
Enter
Sleep 1.5s

Type "tests/test_checkout.py F"
Enter
Sleep 1s

Type "___________________________________ test_checkout ___________________________________"
Enter
Type "    async def test_checkout(page):"
Enter
Type ">       await page.click('button#submit-btn-v1')"
Enter
Type "E       playwright._impl._api_types.TimeoutError: Timeout 3000ms exceeded."
Enter
Type "E       Call log: waiting for locator('button#submit-btn-v1')"
Enter
Sleep 2s

Type "pytest --healwright tests/test_checkout.py"
Enter
Sleep 1.5s

Type "[Healwright] 🧬 Self-Healing Interceptor activated..."
Enter
Sleep 1.2s
Type "[Healwright] 📸 Capturing ARIA snapshot layout tree..."
Enter
Sleep 1.2s
Type "[Healwright] 🤖 Querying Gemini 2.5 Pro for resilient locator..."
Enter
Sleep 1.5s
Type "[Healwright] ✅ Verified locator: page.getByRole('button', { name: 'Complete Checkout' })"
Enter
Sleep 1.2s
Type "[Healwright] 📝 Hot-patching AST source: tests/test_checkout.py (Line 24)"
Enter
Sleep 2s

Type "pytest tests/test_checkout.py"
Enter
Sleep 1.2s
Type "tests/test_checkout.py .                                           [100%]"
Enter
Sleep 1s
Type "============================== 1 passed in 0.42s =============================="
Enter
Sleep 3.5s
