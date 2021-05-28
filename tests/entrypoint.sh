#!/bin/bash

set -Eeuo pipefail

./wait_for.sh
./run_tests.sh
