from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import logging

from models.database import Conversation

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, db: Session):
        self.db = db

    async def save_conversation(
        self,
        phone_number: str,
        customer_type: str,
        customer_name: str,
        response: str,
        whatsapp_profile_name : str,
        message: str,
        polarity: float,
        subjectivity: str,
        sentiment: str,
        detected_language: str

    ) -> Optional[Conversation]:
        """Save a conversation to the database"""
        try:
            conversation = Conversation(
                phone_number=phone_number,
                customer_type=customer_type,
                message=message,
                polarity=polarity,
                subjectivity=subjectivity,
                sentiment=sentiment,
                detected_language = detected_language,
                customer_name=customer_name,    
                whatsapp_profile_name = whatsapp_profile_name ,
                response=response,
                created_at=datetime.utcnow()
            )
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)
            logger.info(f"Saved conversation for {phone_number}")
            return conversation
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving conversation: {str(e)}")
            return None

    async def get_conversation_history(
        self,
        phone_number: str,
        limit: int = 10
    ) -> list[Conversation]:
        """Get conversation history for a phone number"""
        try:
            conversations = self.db.query(Conversation)\
                .filter(Conversation.phone_number == phone_number)\
                .order_by(Conversation.created_at.desc())\
                .limit(limit)\
                .all()
            return conversations
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
