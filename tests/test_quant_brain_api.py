"""
Integration tests for FastAPI endpoints, Quant Brain Chat, and TradingView Webhook.
"""

import pytest
import httpx
from server.app import app
from storage.db import init_db
from config.quant_brain_config import settings


@pytest.mark.asyncio
async def test_health_endpoint():
    await init_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] in ("HEALTHY", "DEGRADED")
        assert "uptime_seconds" in data
        assert data["database_connected"] is True


@pytest.mark.asyncio
async def test_connections_endpoint():
    await init_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/connections")
        assert res.status_code == 200
        data = res.json()
        assert "mcp_tools" in data
        assert data["mcp_tools"]["total_tools"] >= 10
        assert "market_data" in data
        assert "tradingview" in data


@pytest.mark.asyncio
async def test_chat_api_endpoint():
    await init_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/chat",
            json={"message": "Price of gold?", "session_id": "test_api_session_1"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["symbol"] == "GOLD"
        assert "response" in data
        assert len(data["response"]) > 10


@pytest.mark.asyncio
async def test_tradingview_webhook_authorized():
    await init_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "secret": settings.TRADINGVIEW_WEBHOOK_SECRET,
            "symbol": "NIFTY",
            "timeframe": "15m",
            "signal": "BOS_BULLISH",
            "price": 24850.5,
            "indicator": "SmartMoneyConcepts",
            "message": "15m Bullish BOS confirmed",
        }
        res = await client.post("/api/v1/tradingview/webhook", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "alert_id" in data["data"]


@pytest.mark.asyncio
async def test_tradingview_webhook_unauthorized():
    await init_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "secret": "wrong_secret_123",
            "symbol": "NIFTY",
            "signal": "SELL",
            "price": 24800.0,
        }
        res = await client.post("/api/v1/tradingview/webhook", json=payload)
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_watchlist_endpoints():
    await init_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Add symbol
        res1 = await client.post("/api/v1/market/watchlist", json={"symbol": "TCS"})
        assert res1.status_code == 200

        # Fetch watchlist
        res2 = await client.get("/api/v1/market/watchlist")
        assert res2.status_code == 200
        symbols = [item["symbol"] for item in res2.json()["watchlist"]]
        assert "TCS" in symbols

        # Delete symbol
        res3 = await client.delete("/api/v1/market/watchlist/TCS")
        assert res3.status_code == 200


@pytest.mark.asyncio
async def test_root_index_page():
    await init_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/")
        assert res.status_code == 200
        assert "Personal Live Quant Brain" in res.text or "LIVE QUANT BRAIN" in res.text


@pytest.mark.asyncio
async def test_telegram_webhook_info_endpoint():
    await init_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/telegram/webhook-info")
        assert res.status_code == 200

