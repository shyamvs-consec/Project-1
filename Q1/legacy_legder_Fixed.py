import sqlite3
import asyncio
import time
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import uvicorn

DB_NAME = "ledger.db"
app = FastAPI()

# -------------------------------------------------------
# --- Database Setup (Do NOT modify this setup logic) ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT, balance REAL, role TEXT)''')

    users = [
        (1, 'alice', 100.0, 'user'),
        (2, 'bob', 50.0, 'user'),
        (3, 'admin', 9999.0, 'admin'),
        (4, 'charlie', 10.0, 'user')
    ]

    c.executemany(
        "INSERT OR IGNORE INTO users (id, username, balance, role) VALUES (?, ?, ?, ?)",
        users
    )
    conn.commit()
    conn.close()

init_db()
# -------------------------------------------------------

# ---------- Config ----------
MAX_RETRIES = 3
RETRY_DELAY = 0.05  # seconds


# ---------- Schemas ----------
class TransactionRequest(BaseModel):
    user_id: int
    amount: float


# ---------- Routes ----------

@app.get("/search")
def search_users(q: str = Query(...)):
    """
    SQL-injection-safe search endpoint.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, username, role FROM users WHERE username = ?",
        (q,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [{"id": r[0], "username": r[1], "role": r[2]} for r in rows]


@app.post("/transaction")
async def process_transaction(data: TransactionRequest):
    """
    Non-blocking, atomic transaction with retry on DB contention.
    """
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # Non-blocking delay (replaces time.sleep)
    await asyncio.sleep(3)

    for attempt in range(MAX_RETRIES):
        conn = sqlite3.connect(DB_NAME, timeout=5)
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN")

            cursor.execute(
                "SELECT balance FROM users WHERE id = ?",
                (data.user_id,)
            )
            row = cursor.fetchone()

            if not row:
                conn.rollback()
                raise HTTPException(status_code=404, detail="User not found")

            if row[0] < data.amount:
                conn.rollback()
                raise HTTPException(status_code=400, detail="Insufficient funds")

            cursor.execute(
                "UPDATE users SET balance = balance - ? WHERE id = ?",
                (data.amount, data.user_id)
            )

            conn.commit()
            return {
                "status": "processed",
                "deducted": data.amount,
                "remaining_balance": row[0] - data.amount
            }

        except sqlite3.OperationalError as e:
            conn.rollback()
            if "locked" in str(e).lower() and attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (2 ** attempt))
                continue
            raise HTTPException(
                status_code=503,
                detail="System busy, please retry"
            )

        finally:
            conn.close()

    raise HTTPException(status_code=503, detail="System busy, please retry")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
