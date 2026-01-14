import aiosqlite
import json
import asyncio
import logging

DB_NAME = "firehose.db"
LOCK_RETRY_DELAY = 0.1

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp TEXT,
                metadata TEXT
            )
        """)
        await db.commit()

async def flush_batch(batch):
    """
    Inserts a batch of events into the database.
    batch: List of Event objects (Pydantic models)
    """
    if not batch:
        return

    # Prepare data for insertion
    # Ensure metadata is serialized to JSON string for safety
    values = [
        (e.user_id, e.timestamp.isoformat(), json.dumps(e.metadata))
        for e in batch
    ]

    while True:
        try:
            async with aiosqlite.connect(DB_NAME) as db:
                await db.executemany(
                    "INSERT INTO events (user_id, timestamp, metadata) VALUES (?, ?, ?)",
                    values
                )
                await db.commit()
                logging.info(f"Successfully flushed {len(values)} events to database.")
            return  # Success
        except aiosqlite.OperationalError as e:
            if "database is locked" in str(e):
                logging.warning("Database locked, retrying...")
                await asyncio.sleep(LOCK_RETRY_DELAY)
            else:
                logging.error(f"Database error: {e}")
                raise
        except Exception as e:
            logging.error(f"Unexpected error flushing batch: {e}")
            raise
