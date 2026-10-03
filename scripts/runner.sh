#!/usr/bin/env bash

set -euo pipefail

# # Move to project root
# cd "$(dirname "$0")/.."

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-1}"
TIMEOUT="${TIMEOUT:-120}"

echo "======================================"
echo " Starting MDM Platform"
echo "======================================"
echo "Host    : ${HOST}"
echo "Port    : ${PORT}"
echo "Workers : ${WORKERS}"
echo "Timeout : ${TIMEOUT}s"
echo "======================================"

exec uv run gunicorn \
    config.wsgi:application \
    --bind "${HOST}:${PORT}" \
    --workers "${WORKERS}" \
    --timeout "${TIMEOUT}" \
    --access-logfile - \
    --error-logfile -