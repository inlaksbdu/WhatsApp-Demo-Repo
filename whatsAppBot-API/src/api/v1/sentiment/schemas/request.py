from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime

class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class CustomerType(str, Enum):
    PROSPECT = "PROSPECT"
    CUSTOMER = "EXISTING"

class SentimentFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    customer_type: Optional[CustomerType] = None
    sentiment_type: Optional[SentimentType] = None
    min_polarity: Optional[float] = None
    max_polarity: Optional[float] = None
    
class WordAnalysisRequest(BaseModel):
    customer_name: Optional[str] = None
    phone_number: Optional[str] = None
    sentiment_type: SentimentType
    limit: int = Field(10, ge=1, le=100)
