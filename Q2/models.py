from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime

class Event(BaseModel):
    user_id: int
    timestamp: datetime
    metadata: Dict[str, Any]
