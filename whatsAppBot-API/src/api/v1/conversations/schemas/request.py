from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

class CustomerType(str, Enum):
    PROSPECT = "PROSPECT"
    CUSTOMER = "EXISTING"

class SentimentType(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"

class UserSearchFilter(BaseModel):
    search_term: str = Field(..., min_length=1, description="Name or phone number to search for")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(10, ge=1, le=100)

class ChatHistoryFilter(BaseModel):
    identifier: str = Field(..., min_length=1, description="Name or phone number of the user")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$")
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)

class ConversationFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    customer_type: Optional[CustomerType] = None
    sentiment: Optional[SentimentType] = None
    language: Optional[str] = None
    phone_number: Optional[str] = None
    customer_name: Optional[str] = None
    has_transfer: Optional[bool] = None
    has_bank_statement: Optional[bool] = None
    day: Optional[date] = None

class DateRangeFilter(BaseModel):
    start_date: datetime = Field(..., description="Start date for the range")
    end_date: datetime = Field(..., description="End date for the range") 