from pydantic import BaseModel
from typing import Optional

class TransactionCreate(BaseModel):
    type: str
    amount: float
    category: str
    date: Optional[str] = None
    note: Optional[str] = None