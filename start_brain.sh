#!/usr/bin/env bash
# Linux / macOS launcher for Personal Live Quant Brain

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

if [ -f "./.venv/bin/python" ]; then
    PYTHON_BIN="./.venv/bin/python"
else
    PYTHON_BIN="python3"
fi

if [ ! -f ".env" ]; then
    echo "No .env found. Copying .env.example to .env..."
    cp .env.example .env
fi

echo "========================================================"
echo "       STARTING PERSONAL LIVE QUANT BRAIN"
echo "========================================================"
echo "Using Python: $PYTHON_BIN"
echo "Dashboard available at: http://127.0.0.1:8000"
echo "Press Ctrl+C to stop services."
echo ""

exec $PYTHON_BIN deployment/run_production.py
