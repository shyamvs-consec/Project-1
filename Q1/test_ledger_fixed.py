import pytest
import asyncio
import time
from httpx import AsyncClient, ASGITransport
from legacy_fixed import app, init_db
import aiosqlite
import os

@pytest.fixture(autouse=True)
async def setup_db():
    if os.path.exists("ledger.db"):
        os.remove("ledger.db")
    await init_db()
    yield

@pytest.mark.asyncio
async def test_search_sql_injection():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/search?q=alice")
        assert res.status_code == 200
        assert res.json()[0]["username"] == "alice"

        inj = "alice' OR '1'='1"
        res = await ac.get(f"/search?q={inj}")
        assert res.json() == []

@pytest.mark.asyncio
async def test_transaction_concurrency():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        start = time.time()
        await asyncio.gather(
            ac.post("/transaction", json={"user_id": 1, "amount": 1}),
            ac.post("/transaction", json={"user_id": 2, "amount": 1}),
        )
        duration = time.time() - start
        assert duration < 4.0

@pytest.mark.asyncio
async def test_atomic_update_failure():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/transaction",
            json={"user_id": 1, "amount": 1_000_000},
        )
        assert res.status_code == 400

        async with aiosqlite.connect("ledger.db") as db:
            row = await (await db.execute(
                "SELECT balance FROM users WHERE id = 1"
            )).fetchone()
            assert row[0] == 100.0
