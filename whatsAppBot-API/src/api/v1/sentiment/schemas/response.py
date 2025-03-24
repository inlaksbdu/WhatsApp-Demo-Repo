from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from .request import SentimentType, CustomerType

class SentimentCount(BaseModel):
    positive: int
    negative: int
    neutral: int
    total: int

class WordFrequency(BaseModel):
    word: str
    frequency: int
    average_polarity: float

class SentimentWordAnalysis(BaseModel):
    customer_name: Optional[str] = None
    phone_number: Optional[str] = None
    sentiment_type: SentimentType
    words: List[WordFrequency]

class CustomerSentimentPolarity(BaseModel):
    customer_name: str
    phone_number: str
    whatsapp_profile_name: Optional[str] = None
    customer_type: CustomerType
    average_polarity: float
    conversation_count: int
    last_interaction: datetime
