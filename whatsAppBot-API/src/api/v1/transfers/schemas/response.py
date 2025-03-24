from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from .request import TransferStatus

class TransferResponse(BaseModel):
    id: int
    customer_name: str
    amount: float
    credit_account_id: str
    debit_account_id: str
    payment_details: Optional[str] = None
    date: datetime

    class Config:
        from_attributes = True

class TransferCount(BaseModel):
    total_transfers: int
    total_amount: float
    average_amount: float
    time_period: str

class CustomerTransferHistory(BaseModel):
    customer_name: str
    phone_number: str
    total_transfers: int
    total_amount: float
    average_amount: float
    last_transfer_date: datetime

class PaginatedTransferResponse(BaseModel):
    items: List[TransferResponse]
    total: int
    page: int
    size: int
    pages: int

class TransferPeriodAnalysis(BaseModel):
    period: str  # Could be hour, day of week, month, etc.
    count: int
    total_amount: float
    average_amount: float
