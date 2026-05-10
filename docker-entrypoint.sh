#!/bin/sh

set -eu

CONFIG_PATH="${GHSUM_CONFIG_PATH:-/config/config.toml}"
HOST="${GHSUM_HOST:-0.0.0.0}"
PORT="${GHSUM_PORT:-8000}"

if [ "$#" -eq 0 ]; then
    set -- serve
fi

case "$1" in
    serve)
        shift
        exec ghsum serve --config "$CONFIG_PATH" --host "$HOST" --port "$PORT" "$@"
        ;;
    schedule)
        shift
        exec ghsum schedule --config "$CONFIG_PATH" "$@"
        ;;
    run)
        shift
        exec ghsum run --config "$CONFIG_PATH" "$@"
        ;;
    ghsum)
        shift
        exec ghsum "$@"
        ;;
    *)
        exec "$@"
        ;;
esac
