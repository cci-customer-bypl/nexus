#!/usr/bin/env bash

set -euo pipefail

echo "======================================"
echo " Initializing MDM Platform"
echo "======================================"

echo "[1/3] Running Django system checks..."
uv run python manage.py check

echo "[2/3] Applying database migrations..."
uv run python manage.py migrate --noinput

echo "[3/3] Ensuring superuser exists..."
uv run python manage.py init_admin

echo "======================================"
echo " MDM Platform initialization complete"
echo "======================================"