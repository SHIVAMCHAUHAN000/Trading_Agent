"""
Health Check & Observability API Route.
"""

from __future__ import annotations

import time
import os
try:
    import psutil
except ImportError:
    psutil = None
from typing import Any, Dict
from fastapi import APIRouter
from config.quant_brain_config import settings
from storage.db import get_db_connection

router = APIRouter(tags=["Health"])

START_TIME = time.time()


@router.get("/health")
@router.get("/api/v1/health")
async def health_check() -> Dict[str, Any]:
    """Comprehensive system health endpoint."""
    uptime_sec = round(time.time() - START_TIME, 1)

    # Test DB
    db_ok = False
    try:
        async with get_db_connection() as db:
            await db.execute("SELECT 1")
            db_ok = True
    except Exception:
        db_ok = False

    # Process metrics
    mem_mb = 0.0
    if psutil is not None:
        try:
            proc = psutil.Process(os.getpid())
            mem_mb = round(proc.memory_info().rss / (1024 * 1024), 2)
        except Exception:
            pass

    return {
        "status": "HEALTHY" if db_ok else "DEGRADED",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "uptime_seconds": uptime_sec,
        "database_connected": db_ok,
        "memory_usage_mb": mem_mb,
        "timestamp": time.time(),
    }
