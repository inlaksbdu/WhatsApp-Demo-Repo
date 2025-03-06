# Pydantic models for response schemas
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel

class DailyVolume(BaseModel):
    date: datetime
    total_messages: int
    unique_users: int
    class Config:
       from_attributes=True


class UserStats(BaseModel):
    phone_number: str
    whatsapp_profile_name: str
    customer_type: str
    total_messages: int
    last_activity: datetime
    first_interaction: datetime
    class Config:
       from_attributes=True


class ConversationHistory(BaseModel):
    message: str
    response: str
    created_at: datetime
    phone_number: str 
    class Config:
       from_attributes=True

class ProfileSummary(BaseModel):
    total_conversations: int
    # total_messages: int
    average_daily_messages: float
    most_active_hour: int
    customer_type: str
    whatsapp_profile_name: str
    phone_number: str
    first_interaction: datetime
    last_interaction: datetime
    class Config:
       from_attributes=True

class VolumeStats(BaseModel):
    whatsapp_profile_name: str
    phone_number: str
    date: datetime
    message_count: int

    class Config:
        from_attributes=True

class UserInteraction(BaseModel):
    message: str
    response: str
    created_at: datetime
    complaint_type: Optional[str] = None
    complaint_status: Optional[str] = None
    
    class Config:
        from_attributes = True

class CustomerTypeMetrics(BaseModel):
    customer_type: str
    total_users: int
    total_conversations: int
    total_complaints: int
    avg_messages_per_user: float
    avg_response_time: float
    most_common_complaint: str
    satisfaction_rate: float
    class Config:
       from_attributes=True

class UserComplaintSummary(BaseModel):
    whatsapp_profile_name: str
    phone_number: str
    customer_type: str
    total_complaints: int
    open_complaints: int
    urgent_complaints: int
    avg_resolution_time: float
    most_frequent_issue: str
    class Config:
       from_attributes=True

class UserProfile(BaseModel):
    whatsapp_profile_name: str
    phone_number: str
    customer_type: str
    last_seen: datetime
    total_conversations: int

    class Config:
        from_attributes = True


class InteractionPattern(BaseModel):
    whatsapp_profile_name: str
    phone_number: str
    total_interactions: int
    avg_daily_interactions: float
    peak_interaction_hour: int
    last_interaction: datetime
    interaction_frequency: str  # Daily, Weekly, Monthly
    common_topics: List[str]
    class Config:
       from_attributes=True


class RepeatUserMetrics(BaseModel):
    whatsapp_profile_name: str
    phone_number: str
    first_interaction: datetime
    last_interaction: datetime
    total_conversations: int
    conversation_frequency: float
    loyalty_score: float  # Based on interaction patterns
    status: str  
    class Config:
       from_attributes=True

 #Conversation Analytics Models
class ChatMetrics(BaseModel):
    total_messages: int
    unique_users: int
    avg_messages_per_user: float
    customer_type_distribution: Dict[str, int]
    most_active_hours: List[Dict[str, int]]
    class Config:
       from_attributes=True

class UserChatPattern(BaseModel):
    whatsapp_profile_name: str
    phone_number: str
    customer_type: str
    total_messages: int
    first_message: datetime
    last_message: datetime
    average_messages_per_day: float
    active_days: int
    class Config:
       from_attributes=True



# Complaint Analytics Models
class ComplaintMetrics(BaseModel):
    total_complaints: int
    unique_users: int
    complaint_type_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    avg_resolution_time: Optional[float]
    class Config:
       from_attributes=True

class UserComplaintPattern(BaseModel):
    name: str
    phone_number: str
    total_complaints: int
    complaint_types: List[str]
    current_status: List[str]
    first_complaint: datetime
    last_complaint: datetime
    class Config:
       from_attributes=True

# Combined Analytics Model (with clear separation)
class PhoneNumberOverview(BaseModel):
    phone_number: str
    chat_data: Optional[UserChatPattern]
    complaint_data: Optional[UserComplaintPattern]
    is_linked: bool  # Indicates if number exists in both systems
    class Config:
       from_attributes=True