import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from starlette import status

from models import Event
from database import init_db, flush_batch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Configuration
BATCH_SIZE = 1000
FLUSH_INTERVAL = 1.0  # seconds

# Global State
event_queue = asyncio.Queue()

async def consumer_worker():
    """
    Background task that pulls events from the queue and flushes them to the DB.
    """
    logging.info("Consumer worker started.")
    batch: List[Event] = []
    
    while True:
        try:
            # Wait for next event or timeout to flush partial batch
            try:
                # Calculate time remaining for flush interval if we have items
                # For simplicity in this demo, we just wait a short time for each item
                # A robust implementation would track the oldest item in the batch.
                # Here we use a simpler approach: get items as fast as possible, 
                # but if queue empty, flush what we have.
                
                # Fetch item with timeout to allow periodic flush
                item = await asyncio.wait_for(event_queue.get(), timeout=FLUSH_INTERVAL)
                batch.append(item)
                event_queue.task_done()
                
                if len(batch) >= BATCH_SIZE:
                    await flush_batch(batch)
                    batch = []
            
            except asyncio.TimeoutError:
                # No new items for FLUSH_INTERVAL, flush what we have
                if batch:
                    await flush_batch(batch)
                    batch = []
            
        except asyncio.CancelledError:
            logging.info("Consumer worker cancelled. Flushing remaining items...")
            break
        except Exception as e:
            logging.error(f"Error in consumer worker: {e}")
            # Don't crash the worker, just log and continue (maybe drop batch or retry?)
            # In this simple demo, we might lose the batch if flush fails repeatedly.

    # Final flush on shutdown
    if batch:
        await flush_batch(batch)
    
    # Drain the queue
    while not event_queue.empty():
        try:
            item = event_queue.get_nowait()
            batch.append(item)
            event_queue.task_done()
        except asyncio.QueueEmpty:
            break
    
    if batch:
        await flush_batch(batch)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    worker_task = asyncio.create_task(consumer_worker())
    yield
    # Shutdown
    worker_task.cancel()
    await worker_task

app = FastAPI(lifespan=lifespan)

@app.post("/event", status_code=status.HTTP_202_ACCEPTED)
async def ingest_event(event: Event):
    await event_queue.put(event)
    return {"status": "accepted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
