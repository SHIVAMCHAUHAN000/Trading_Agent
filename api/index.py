"""
Vercel Serverless Entrypoint for Personal Live Quant Brain.
Exposes the FastAPI ASGI application for Vercel Serverless Functions.
"""

import os
import sys
from pathlib import Path

# Add project root directory to sys.path for Vercel runtime
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from server.app import app

# Vercel looks for `app` in api/index.py
__all__ = ["app"]
