from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class ConversationResponse(BaseModel):
    id: int
    customer_name: str
    phone_number: str
    whatsapp_profile_name: Optional[str]
    customer_type: str
    message: str
    response: str
    sentiment: str
    polarity: float
    detected_language: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TotalChatsResponse(BaseModel):
    total_chats: int

class ActiveChatsResponse(BaseModel):
    active_chats: int

class ChatHourDistribution(BaseModel):
    hour: int
    count: int

class ChatHoursResponse(BaseModel):
    distribution: List[ChatHourDistribution]
    most_active_hour: int
    least_active_hour: int

class LanguageDistributionItem(BaseModel):
    language: str
    count: int

class LanguageDistributionResponse(BaseModel):
    languages: List[LanguageDistributionItem]

class ProspectUserStats(BaseModel):
    phone_number: str
    chat_count: int
    last_interaction: datetime


class ExistingUserStats(BaseModel):
    customer_name: str
    phone_number: str
    chat_count: int
    last_interaction: datetime
    recent_messages: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedConversationResponse(BaseModel):
    items: List[ConversationResponse]
    total: int
    page: int
    size: int
    pages: int 