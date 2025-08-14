#!/bin/sh

set -eu

# Start unified web app (scheduler + static server) via CLI
exec uv run ghsum web --host 0.0.0.0 --port 8000
