from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CustomerCount(BaseModel):
    total: int
    prospects: int
    existing: int

class CustomerEngagement(BaseModel):
    customer_name: str
    phone_number: str
    whatsapp_profile_name: Optional[str] = None
    customer_type: str
    conversation_count: int
    last_interaction: datetime
    average_sentiment_polarity: float

class CustomerSentiment(BaseModel):
    customer_name: str
    phone_number: str
    whatsapp_profile_name: Optional[str] = None
    customer_type: str
    average_sentiment_polarity: float
    conversation_count: int
    last_interaction: datetime

class ConversationSummary(BaseModel):
    id: int
    message: str
    response: str
    sentiment: str
    polarity: float
    created_at: datetime

class TransferSummary(BaseModel):
    id: int
    amount: float
    credit_account_id: str
    debit_account_id: str
    payment_details: str
    date: datetime

class BankStatementSummary(BaseModel):
    id: int
    request_start_date: datetime
    request_end_date: datetime
    date: datetime

class ComplaintSummary(BaseModel):
    id: int
    complaint_type: str
    description: str
    status: str
    created_at: datetime

class AppointmentSummary(BaseModel):
    id: int
    appointment_type: str
    preferred_date: datetime
    preferred_time: str
    status: str
    created_at: datetime

class BankRequestSummary(BaseModel):
    id: int
    service_type: str
    status: str
    created_at: datetime

class Customer360View(BaseModel):
    customer_name: str
    phone_number: str
    whatsapp_profile_name: Optional[str] = None
    customer_type: str
    total_conversations: int
    average_sentiment: float
    channel: str
    first_interaction: datetime
    last_interaction: datetime
    conversations: List[ConversationSummary]
    transfers: List[TransferSummary]
    bank_statements: List[BankStatementSummary]
    complaints: List[ComplaintSummary]
    appointments: List[AppointmentSummary]
    bank_requests: List[BankRequestSummary]

class PlatformChannel(BaseModel):
    phone_number: str
    customer_name: str
    channel: str
