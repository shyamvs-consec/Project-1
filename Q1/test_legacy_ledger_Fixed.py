import pytest
import asyncio
import time
import os
import sqlite3
from httpx import AsyncClient, ASGITransport
from legacy_legder_Fixed import app, init_db   # import from NEW fixed file


@pytest.fixture(autouse=True)
def setup_db():
    # Fresh DB for every test
    if os.path.exists("ledger.db"):
        os.remove("ledger.db")
    init_db()
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
        # Both calls should overlap due to asyncio.sleep
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

        # Verify balance unchanged
        conn = sqlite3.connect("ledger.db")
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE id = 1")
        balance = cursor.fetchone()[0]
        conn.close()

        assert balance == 100.0
