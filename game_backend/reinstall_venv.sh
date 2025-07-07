#!/bin/bash
# Remove existing venv, create new, and reinstall dependencies

cd "$(dirname "$0")/.."
rm -rf venv
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r game_backend/requirements.txt
# Ensure uvicorn gets installed
venv/bin/pip install uvicorn
