Output demo.gif
Set FontSize 15
Set Width 900
Set Height 520
Set Theme "tokyonight"

Type "pytest test_checkout.py"
Enter
Sleep 2s

Type "# Running Playwright specs..."
Enter
Sleep 1.5s

Type "FAILED test_checkout.py::test_login - Locator not found: button#submit-btn-v1"
Enter
Sleep 1s

Type "awarse heal --last-failed"
Enter
Sleep 2s

Type "[AWARSE] Inspecting current DOM structure..."
Enter
Sleep 1s
Type "[AWARSE] Detected shift: button#submit-btn-v1 -> button.checkout-primary-cta"
Enter
Sleep 1s
Type "[*] Patch applied: test_checkout.py (line 24 healed)"
Enter
Sleep 1.5s

Type "pytest test_checkout.py"
Enter
Sleep 2s
Type "PASSED test_checkout.py::test_login [100%]"
Enter
Sleep 3s
