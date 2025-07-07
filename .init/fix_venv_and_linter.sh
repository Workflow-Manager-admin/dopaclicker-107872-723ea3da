#!/bin/bash
# Fix script for CI: ensures venv exists in the workspace root and installs flake8

set -e

cd "$(dirname "$0")/.."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

./venv/bin/pip install --upgrade pip
./venv/bin/pip install flake8
