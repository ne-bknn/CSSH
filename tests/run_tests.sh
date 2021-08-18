#!/bin/bash

set -Eeuo pipefail
PYTHONPATH="$(pwd)/bot"
export PYTHONPATH

pytest
