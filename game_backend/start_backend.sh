#!/bin/bash
# Script to start the Dopamine Clicker FastAPI backend using Uvicorn

cd "$(dirname "$0")/src/api"
# Run Uvicorn with main:app, reload for dev mode
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
