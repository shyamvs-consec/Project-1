import asyncio
import aiosqlite
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import uvicorn
import os

app = FastAPI()

DB_NAME = "ledger.db"

# --- Database Setup ---

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users 
                     (id INTEGER PRIMARY KEY, username TEXT, balance REAL, role TEXT)''')
        
        # Check if users exist to avoid duplicate seeding on restart
        cursor = await db.execute("SELECT count(*) FROM users")
        count = await cursor.fetchone()
        
        if count[0] == 0:
            users = [
                (1, 'alice', 100.0, 'user'),
                (2, 'bob', 50.0, 'user'),
                (3, 'admin', 9999.0, 'admin'),
                (4, 'charlie', 10.0, 'user')
            ]
            await db.executemany("INSERT OR IGNORE INTO users (id, username, balance, role) VALUES (?, ?, ?, ?)", users)
            await db.commit()
            print("Database seeded.")

@app.on_event("startup")
async def startup_event():
    await init_db()

# --- Schemas ---

class TransactionRequest(BaseModel):
    user_id: int
    amount: float

# --- Routes ---

@app.get("/search")
async def search_users(q: str = Query(..., description="Username to search for")):
    """
    Search for a user by username.
    Resistant to SQL Injection using parameterized queries.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        # SECURITY FIX: Use parameterized queries to prevent SQL Injection
        # We perform a partial match for better usability, or exact match based on requirement.
        # The original code did EXACT match: "WHERE username = '{query}'"
        # We will keep exact match to preserve behavior, but securely.
        query = "SELECT id, username, role FROM users WHERE username = ?"
        
        async with db.execute(query, (q,)) as cursor:
            results = await cursor.fetchall()
            
        data = [{"id": r[0], "username": r[1], "role": r[2]} for r in results]
        return data

@app.post("/transaction")
async def process_transaction(data: TransactionRequest):
    """
    Deducts money from a user's balance.
    Non-blocking simulation of external API call.
    Atomic database updates.
    """
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # PERFORMANCE FIX: Use asyncio.sleep instead of time.sleep
    # This yields control back to the event loop, allowing other requests to be processed.
    await asyncio.sleep(3) 
    
    async with aiosqlite.connect(DB_NAME) as db:
        # DATA INTEGRITY FIX: Check balance before update and ensure atomicity
        async with db.execute("BEGIN"):
            try:
                # Check current balance
                cursor = await db.execute("SELECT balance FROM users WHERE id = ?", (data.user_id,))
                row = await cursor.fetchone()
                
                if not row:
                    await db.rollback()
                    raise HTTPException(status_code=404, detail="User not found")
                
                current_balance = row[0]
                
                if current_balance < data.amount:
                    await db.rollback()
                    raise HTTPException(status_code=400, detail="Insufficient funds")
                
                # Perform update
                await db.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (data.amount, data.user_id))
                await db.commit()
                
                return {"status": "processed", "deducted": data.amount, "remaining_balance": current_balance - data.amount}
                
            except Exception as e:
                await db.rollback()
                # Re-raise HTTP exceptions, wrap others
                if isinstance(e, HTTPException):
                    raise e
                raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    # Running using uvicorn directly for easy testing similar to app.run()
    uvicorn.run(app, host="127.0.0.1", port=8000)
