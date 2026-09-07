Output site/assets/demo.gif
Set FontSize 14
Set Width 860
Set Height 420
Set Theme "tokyonight"
Set Padding 20
Set Shell "bash"

# Silently bind clean commands and clear the prompt
Hide
Type "alias pytest='./run_demo.sh'"
Enter
Type "alias awarse='./run_demo.sh'"
Enter
Type "clear"
Enter
Show
Sleep 1s

# 1. Failing test execution
Type "pytest test-fail"
Sleep 400ms
Enter
Sleep 2.5s

# 2. Self-healing invocation
Type "awarse heal"
Sleep 400ms
Enter
Sleep 3s

# 3. Successful re-run
Type "pytest test-pass"
Sleep 400ms
Enter
Sleep 4s
