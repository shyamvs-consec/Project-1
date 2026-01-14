import sqlite3
import time
import os

DB_NAME = "firehose.db"

def simulate_outage(duration=10):
    print(f"Attempting to lock {DB_NAME} for {duration} seconds...")
    try:
        # Connect and acquire exclusive lock
        conn = sqlite3.connect(DB_NAME, timeout=1.0)
        conn.execute("BEGIN EXCLUSIVE")
        print(">> DATABASE LOCKED. API calls should still be accepted (202).")
        print(f">> Waiting {duration} seconds...")
        time.sleep(duration)
        conn.rollback() # Release lock
        print(">> DATABASE UNLOCKED. Worker should resume writing.")
    except sqlite3.OperationalError as e:
        print(f"Could not acquire lock (is the app writing?): {e}")

if __name__ == "__main__":
    if not os.path.exists(DB_NAME):
        print("Database file not found. Run the app first.")
    else:
        simulate_outage()
