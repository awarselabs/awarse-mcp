Output demo.gif
Set FontSize 14
Set Width 860
Set Height 420
Set Theme "tokyonight"
Set Padding 20

Type "python -m pytest test_checkout.py"
Enter
Sleep 1.5s

# Simulate the initial test failure
Type "echo -e '\033[1;31mFAILED\033[0m test_checkout.py::test_login - \033[0;33mLocator not found: button#submit-btn-v1\033[0m'"
Enter
Sleep 1s

# Trigger the healing action
Type "python -m awarse heal --last-failed"
Enter
Sleep 1s

# Simulated successful output stream
Type "echo -e '\033[1;36m[AWARSE]\033[0m Inspecting current DOM structure...'"
Enter
Sleep 800ms

Type "echo -e '\033[1;36m[AWARSE]\033[0m Detected shift: \033[0;31mbutton#submit-btn-v1\033[0m -> \033[0;32mbutton.checkout-primary-cta\033[0m'"
Enter
Sleep 800ms

Type "echo -e '\033[1;32m[*]\033[0m Patch applied: test_checkout.py (line 24 healed)'"
Enter
Sleep 1.5s

# Re-run and show green
Type "python -m pytest test_checkout.py"
Enter
Sleep 1.2s

Type "echo -e '\033[1;32mPASSED\033[0m test_checkout.py::test_login [100%] \033[1;32m(1 passed in 0.42s)\033[0m'"
Enter
Sleep 3s
