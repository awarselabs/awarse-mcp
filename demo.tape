Output demo.gif
Set FontSize 14
Set Width 860
Set Height 420
Set Theme "tokyonight"
Set Padding 20
Set Shell "bash"

Type "pytest tests/e2e/test_checkout.py"
Sleep 500ms
Enter

Hide
Type "./run_demo.sh test-fail"
Enter
Show
Sleep 1.5s

Type "awarse heal --last-failed"
Sleep 500ms
Enter

Hide
Type "./run_demo.sh heal"
Enter
Show
Sleep 2s

Type "pytest tests/e2e/test_checkout.py"
Sleep 500ms
Enter

Hide
Type "./run_demo.sh test-pass"
Enter
Show
Sleep 3s
