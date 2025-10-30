#!/bin/bash
set -e

# Use PORT environment variable from Cloud Run, default to 8080
PORT=${PORT:-8080}

echo "Starting application on port $PORT"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
