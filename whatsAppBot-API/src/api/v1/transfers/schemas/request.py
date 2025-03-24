from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime, date

class TransferStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TransferFilter(BaseModel):
    customer_name: Optional[str] = None
    phone_number: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    status: Optional[TransferStatus] = None
    debit_account_id: Optional[str] = None
    credit_account_id: Optional[str] = None

class TimeRangeRequest(BaseModel):
    start_date: datetime = Field(..., description="Start date for the time range")
    end_date: datetime = Field(..., description="End date for the time range")
