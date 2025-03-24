from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime

class CustomerType(str, Enum):
    PROSPECT = "PROSPECT"
    CUSTOMER = "EXISTING"

class CustomerFilter(BaseModel):
    customer_type: Optional[CustomerType] = None
    name: Optional[str] = None
    phone_number: Optional[str] = None
    min_engagement: Optional[int] = None
    min_sentiment_polarity: Optional[float] = None
    max_sentiment_polarity: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class CustomerDetailRequest(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    customer_type: Optional[CustomerType] = None
