#!/bin/bash
cd /home/kavia/workspace/code-generation/dopaclicker-107872-723ea3da/game_backend
source ./venv/bin/flake8 game_backend/src/api --max-line-length=120 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

