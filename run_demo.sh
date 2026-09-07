#!/usr/bin/env bash

if [ "$1" == "test-fail" ]; then
    echo -e "\033[1;34m[RUN]\033[0m Playwright test runner v1.42.0"
    echo -e "Running 1 test across 1 worker"
    sleep 0.8
    echo -e "\033[1;31mFAILED\033[0m tests/e2e/test_checkout.py::test_login"
    echo -e "\033[0;33mLocator not found: button#submit-btn-v1 (Timeout 5000ms)\033[0m"
elif [ "$1" == "heal" ]; then
    echo -e "\033[1;36m[AWARSE AI]\033[0m Connecting to Playwright session via MCP..."
    sleep 0.5
    echo -e "\033[1;36m[AWARSE AI]\033[0m Analyzing DOM tree & semantic diff..."
    sleep 0.7
    echo -e "\033[1;36m[AWARSE AI]\033[0m Matched target via semantic intent (\033[1;32m98.4% confidence\033[0m)"
    echo -e "\033[1;36m[AWARSE AI]\033[0m Replaced \033[0;31mbutton#submit-btn-v1\033[0m -> \033[1;32mbutton.checkout-primary-cta\033[0m"
    sleep 0.4
    echo -e "\033[1;32m[*]\033[0m Patch applied: tests/e2e/test_checkout.py (line 24 healed)"
elif [ "$1" == "test-pass" ]; then
    echo -e "\033[1;34m[RUN]\033[0m Playwright test runner v1.42.0"
    echo -e "Running 1 test across 1 worker"
    sleep 0.6
    echo -e "\033[1;32mPASSED\033[0m tests/e2e/test_checkout.py::test_login [100%]"
    echo -e "\033[1;32m1 passed in 0.42s (1 locator auto-healed)\033[0m"
fi
