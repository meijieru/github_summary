#!/bin/sh

# Start the scheduler in the background
uv run github-summary schedule-run &

# Start the HTTP server in the foreground
cd output && python3 -m http.server --bind 0.0.0.0 --directory . 8000 --cgi
