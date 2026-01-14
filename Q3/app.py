from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import engine, get_db, Base
from models import Inventory, PurchaseRecord

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

def initialize_inventory(db: Session):
    """Seed the database with Item A if it doesn't exist."""
    item = db.query(Inventory).filter(Inventory.id == 1).first()
    if not item:
        item = Inventory(id=1, name="Item A", quantity=100)
        db.add(item)
        #db.commit()
        print("Initialized Item A with 100 stock.")
    else:
        # Reset for testing purposes if needed, or just leave it
        # Un-comment the next lines if you want to force reset on restart for testing
        item.quantity = 100
    db.commit()
        

@app.on_event("startup")
def on_startup():
    with Session(engine) as db:
        initialize_inventory(db)

import time
from sqlalchemy.exc import OperationalError

MAX_RETRIES = 3
RETRY_DELAY = 0.05  # 50 ms

@app.post("/buy_ticket")
def buy_ticket(db: Session = Depends(get_db)):
    statement = text("""
        UPDATE inventory
        SET quantity = quantity - 1
        WHERE id = :id AND quantity > 0
    """)

    for attempt in range(MAX_RETRIES):
        try:
            result = db.execute(statement, {"id": 1})

            if result.rowcount == 1:
                db.add(PurchaseRecord(item_id=1))
                db.commit()
                return {"message": "Purchase successful"}

            db.rollback()
            raise HTTPException(status_code=410, detail="Item sold out")

        except OperationalError as e:
            db.rollback()

            # Retry only on lock contention
            if "database is locked" in str(e).lower():
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (2 ** attempt))  # exponential backoff
                    continue
                raise HTTPException(
                    status_code=503,
                    detail="System busy, please retry"
                )
            raise


@app.get("/inventory")
def get_inventory(db: Session = Depends(get_db)):
    item = db.query(Inventory).filter(Inventory.id == 1).first()
    return item
