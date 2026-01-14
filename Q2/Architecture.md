Architecture Notes – Firehose Collector

Overview:

The Firehose Collector is a high-throughput ingestion service designed to accept large volumes of events without blocking client requests or losing data.

Architecture:

Client → FastAPI → Async Queue → Background Worker → SQL Database

Key Design Decisions:

A)Non-Blocking Ingestion:

i)POST /event validates input and immediately returns 202 Accepted.
ii)Events are placed into an in-memory asyncio.Queue.
iii)No database work is performed on the request path.

B)Buffering & Batching:

i)Events are flushed to the database by a background worker.
ii)Flush triggers:
    a)Batch size threshold (e.g., 1000 events)
    b)Time-based interval (e.g., 1 second)

iii)Prevents per-request database writes.

C)Persistence & Security

i)Events are stored in a SQL database (SQLite for demo).
ii)Arbitrary metadata is serialized using json.dumps.
iii)Parameterized SQL queries prevent injection.

D)Resilience

i)Database lock/outage is handled by retrying writes in the worker.
ii)API continues accepting requests during DB downtime.
iii)Buffered events are written once the database recovers.

Tradeoffs:

i)Single consumer worker due to SQLite write limitations.
ii)Batch size and interval are hardcoded for simplicity.

