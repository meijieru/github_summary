#!/bin/sh

set -eu

# Start unified web app (scheduler + static server)
exec uv run uvicorn github_summary.web:web_app --host 0.0.0.0 --port 8000
