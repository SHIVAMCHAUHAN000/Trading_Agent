"""
Canonical Vercel FastAPI entrypoint (app/main.py).
Exposes the FastAPI application instance 'app' for Vercel Serverless Functions.
"""

from main import app

__all__ = ["app"]
