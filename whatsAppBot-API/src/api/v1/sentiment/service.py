from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_, or_, text
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re
from collections import Counter
from src.models.models import Conversation
from .schemas.request import SentimentType, CustomerType, SentimentFilter, WordAnalysisRequest

class SentimentService:
    @staticmethod
    async def get_sentiment_counts(
        db: Session,
        filter: Optional[SentimentFilter] = None
    ) -> Dict[str, int]:
        """Get counts of conversations by sentiment type"""
        query = db.query(Conversation.sentiment, func.count(Conversation.id))
        
        if filter:
            if filter.start_date:
                query = query.filter(Conversation.created_at >= filter.start_date)
            if filter.end_date:
                query = query.filter(Conversation.created_at <= filter.end_date)
            if filter.customer_type:
                query = query.filter(Conversation.customer_type == filter.customer_type)
        
        results = query.group_by(Conversation.sentiment).all()
        
        # Initialize counts
        counts = {
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "total": 0
        }
        
        # Fill in actual counts
        for sentiment, count in results:
            if sentiment and sentiment.upper() == SentimentType.POSITIVE:
                counts["positive"] = count
            elif sentiment and sentiment.upper() == SentimentType.NEGATIVE:
                counts["negative"] = count
            elif sentiment and sentiment.upper() == SentimentType.NEUTRAL:
                counts["neutral"] = count
            counts["total"] += count
            
        return counts
    
    @staticmethod
    def _extract_words(text: str) -> List[str]:
        """Extract individual words from text, removing punctuation and converting to lowercase"""
        if not text:
            return []
        # Remove special characters and split by whitespace
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        # Filter out common stop words (can be expanded)
        stop_words = {'the', 'and', 'is', 'in', 'to', 'a', 'for', 'of', 'that', 'this', 'with'}
        return [word for word in words if word not in stop_words]
    
    @staticmethod
    async def analyze_sentiment_words(
        db: Session,
        request: WordAnalysisRequest
    ) -> Dict[str, Any]:
        """Analyze most frequent words in conversations with specific sentiment"""
        # Build query based on request
        query = db.query(Conversation)
        
        # Apply filters
        filters = []
        if request.sentiment_type == SentimentType.POSITIVE:
            filters.append(Conversation.sentiment == SentimentType.POSITIVE)
        elif request.sentiment_type == SentimentType.NEGATIVE:
            filters.append(Conversation.sentiment == SentimentType.NEGATIVE)
        else:
            filters.append(Conversation.sentiment == SentimentType.NEUTRAL)
            
        if request.customer_name:
            filters.append(Conversation.customer_name == request.customer_name)
        if request.phone_number:
            filters.append(Conversation.phone_number == request.phone_number)
            
        query = query.filter(and_(*filters))
        
        # Get conversations
        conversations = query.all()
        
        # Extract and count words
        all_words = []
        word_polarities = {}
        
        for conv in conversations:
            words = SentimentService._extract_words(conv.message)
            all_words.extend(words)
            
            # Track polarity for each word
            for word in words:
                if word not in word_polarities:
                    word_polarities[word] = []
                word_polarities[word].append(conv.polarity)
        
        # Count word frequencies
        word_counts = Counter(all_words)
        
        # Calculate average polarity for each word
        word_analysis = []
        for word, count in word_counts.most_common(request.limit):
            avg_polarity = sum(word_polarities[word]) / len(word_polarities[word])
            word_analysis.append({
                "word": word,
                "frequency": count,
                "average_polarity": avg_polarity
            })
        
        return {
            "customer_name": request.customer_name,
            "phone_number": request.phone_number,
            "sentiment_type": request.sentiment_type,
            "words": word_analysis
        }
    
    @staticmethod
    async def get_users_by_sentiment_polarity(
        db: Session,
        positive: bool = True,
        customer_type: Optional[CustomerType] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get users with highest or lowest sentiment polarity"""
        query = db.query(
            Conversation.customer_name,
            Conversation.phone_number,
            Conversation.whatsapp_profile_name,
            Conversation.customer_type,
            func.avg(Conversation.polarity).label('average_polarity'),
            func.count(Conversation.id).label('conversation_count'),
            func.max(Conversation.created_at).label('last_interaction')
        ).group_by(
            Conversation.customer_name,
            Conversation.phone_number,
            Conversation.whatsapp_profile_name,
            Conversation.customer_type
        )
        
        # Apply customer type filter if provided
        if customer_type:
            query = query.filter(Conversation.customer_type == customer_type)
        
        # Require at least 3 conversations for meaningful analysis
        query = query.having(func.count(Conversation.id) >= 3)
        
        # Order by polarity (desc for positive, asc for negative)
        if positive:
            query = query.order_by(desc('average_polarity'))
        else:
            query = query.order_by(asc('average_polarity'))
        
        return query.limit(limit).all()
