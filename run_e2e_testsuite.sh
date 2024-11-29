#!/bin/sh
set -e

# This script is used to install and run the e2e testsuite.
# Usage:
#
# Run the testsuite:
# ./run_e2e_testsuite.sh
#
# Run a specific test:
# ./run_e2e_testsuite.sh -k test_my_test_name
#
# Run all tests with tracing enabled:
# ./run_e2e_testsuite.sh --tracing on

playwright install chromium
DJANGO_ALLOW_ASYNC_UNSAFE=1 python -m pytest --browser chromium --headed tests/e2e/ $@
