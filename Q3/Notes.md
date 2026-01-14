Technical Assessment: The High-Concurrency Inventory System

Overview:

A strictly consistent inventory system designed to prevent overselling under high concurrency using database-level guarantees.

Concurrency & Consistency:

i)Inventory updates use a single atomic SQL statement with a conditional update.
ii)Ensures inventory never goes negative and overselling is impossible, even across multiple processes.

Contention Handling:

i)Database write contention is handled using an explicit timeout and bounded retries with backoff.
ii)Requests fail cleanly if retries are exhausted, avoiding deadlocks.

API Behavior:       

i)200 OK – purchase successful
ii)410 GONE – item sold out
iii)503 SERVICE UNAVAILABLE – temporary contention / timeout

proof_of_correctness.py:

i)A stress test sends more requests than available inventory.
ii)Verifies exactly 100 successful purchases with no overselling.