Output demo.gif
Set FontSize 14
Set Width 860
Set Height 420
Set Theme "tokyonight"
Set Padding 20
Set Shell "bash"

# 1. Type the initial test run
Type "pytest tests/e2e/test_checkout.py"
Sleep 500ms
Enter

# Run the failure output invisibly via bash
Hide
Type "echo -e '\033[1;31mFAILED\033[0m tests/e2e/test_checkout.py::test_login - \033[0;33mLocator not found: button#submit-btn-v1\033[0m'"
Enter
Show
Sleep 1.5s

# 2. Type the MCP trigger command
Type "awarse heal --last-failed"
Sleep 500ms
Enter

# Run the healing diagnostics invisibly
Hide
Type "echo -e '\033[1;36m[AWARSE]\033[0m Inspecting current DOM structure...'"
Enter
Show
Sleep 800ms

Hide
Type "echo -e '\033[1;36m[AWARSE]\033[0m Detected shift: \033[0;31mbutton#submit-btn-v1\033[0m -> \033[0;32mbutton.checkout-primary-cta\033[0m'"
Enter
Show
Sleep 900ms

Hide
Type "echo -e '\033[1;32m[*]\033[0m Patch applied: test_checkout.py (line 24 healed)'"
Enter
Show
Sleep 1.5s

# 3. Re-run tests to show green
Type "pytest tests/e2e/test_checkout.py"
Sleep 500ms
Enter

Hide
Type "echo -e '\033[1;32mPASSED\033[0m tests/e2e/test_checkout.py::test_login [100%] \033[1;32m(1 passed in 0.38s)\033[0m'"
Enter
Show
Sleep 3s
