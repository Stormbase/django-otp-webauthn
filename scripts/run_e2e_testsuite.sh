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
if [ "$CI" ]; then
  EXTRA_ARGS="--tracing on"
else
  EXTRA_ARGS="--headed"
fi

DJANGO_ALLOW_ASYNC_UNSAFE=1 python -m pytest --browser chromium $EXTRA_ARGS tests/e2e/ $@
