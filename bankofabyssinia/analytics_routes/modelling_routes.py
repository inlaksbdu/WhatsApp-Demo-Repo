from typing import List, Optional
from fastapi import APIRouter,  Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, and_
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np
import logging
import nltk
nltk.download('punkt_tab')
logger = logging.getLogger(__name__)

from models.database import Complaint, Conversation, get_db
from services.topic_modelling import (FAQ, ComplaintAnalytics, ConversationMetrics, FAQExtractor, TextPreprocessor, 
        TopicAnalysisResult, TopicFrequency, TopicFrequencyAnalyzer, analyze_conversations)

# FAQ = FAQ()
# ComplaintAnalytics = ComplaintAnalytics()
# ConversationMetrics = ConversationMetrics()
# FAQExtractor = FAQExtractor()
# TextPreprocessor = TextPreprocessor()
# TopicAnalysisResult = TopicAnalysisResult()
# TopicFrequency = TopicFrequency()
# TopicFrequencyAnalyzer = TopicFrequencyAnalyzer()
# analyze_conversations = analyze_conversations()




router = APIRouter(
    prefix="/message-analytics",
    tags=["Topic Modelling"]
)


@router.get("/analytics/conversations", response_model=ConversationMetrics)
async def get_conversation_analytics(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get comprehensive conversation analytics"""
    try:
        return await analyze_conversations(db, days)
    except Exception as e:
        logger.error(f"Error in conversation analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error analyzing conversations")


@router.get("/analytics/complaints", response_model=ComplaintAnalytics)
async def get_complaint_analytics(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Analyze complaint patterns and resolution metrics"""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Fetch complaints
        complaints = db.query(Complaint).filter(
            Complaint.created_at >= cutoff_date
        ).all()
        
        if not complaints:
            raise HTTPException(status_code=404, detail="No complaints found in specified period")
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'type': c.complaint_type,
            'status': c.status,
            'created_at': c.created_at,
            'updated_at': c.updated_at
        } for c in complaints])
        
        # Calculate resolution time for resolved complaints
        df['resolution_time'] = (df['updated_at'] - df['created_at']).dt.total_seconds() / 3600  # in hours
        
        # Analyze patterns
        type_distribution = df['type'].value_counts().to_dict()
        status_distribution = df['status'].value_counts().to_dict()
        avg_resolution_time = float(df[df['status'] == 'RESOLVED']['resolution_time'].mean())
        
        # Calculate daily complaint trends
        df['date'] = df['created_at'].dt.date
        daily_counts = df.groupby('date').size()
        
        return {
            'total_complaints': len(complaints),
            'type_distribution': type_distribution,
            'avg_resolution_time': avg_resolution_time,
            'status_distribution': status_distribution,
            'complaint_trends': {
                'daily_counts': daily_counts.tolist()
            }
        }
    
    except Exception as e:
        logger.error(f"Error in complaint analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error analyzing complaints")

@router.get("/analytics/topics/{topic_id}", response_model=TopicAnalysisResult)
async def get_topic_details(
    topic_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get detailed analysis of a specific topic"""
    try:
        analytics = await analyze_conversations(db, days)
        topic_info = next((topic for topic in analytics['common_topics'] 
                          if topic['topic_id'] == topic_id), None)
        
        if not topic_info:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        return TopicAnalysisResult(
            topic_id=topic_id,
            keywords=topic_info['keywords'],
            sample_messages=topic_info['sample_messages'],
            message_count=topic_info['message_count'],
            probability=topic_info['probability'],
            temporal_trend={},  # Would be populated with actual temporal data
            related_complaints=[]  # Would be populated with related complaints
        )
    
    except Exception as e:
        logger.error(f"Error in topic details: {str(e)}")
        raise HTTPException(status_code=500, detail="Error analyzing topic")
    


@router.get("/analytics/faqs", response_model=List[FAQ])
async def get_frequent_questions(
    days: Optional[int] = 30,
    min_frequency: Optional[int] = 2,
    db: Session = Depends(get_db)
):
    """Extract and analyze frequently asked questions"""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Fetch conversations
        conversations = db.query(Conversation).filter(
            Conversation.created_at >= cutoff_date
        ).all()
        
        if not conversations:
            raise HTTPException(status_code=404, detail="No conversations found")
        
        # Initialize FAQ extractor
        faq_extractor = FAQExtractor()
        
        # Extract questions from messages
        all_questions = []
        question_metadata = {}
        
        for conv in conversations:
            questions = faq_extractor.extract_questions(conv.message)
            for q in questions:
                all_questions.append(q)
                if q not in question_metadata:
                    question_metadata[q] = {
                        'frequency': 1,
                        'responses': [conv.response],
                        'last_asked': conv.created_at
                    }
                else:
                    question_metadata[q]['frequency'] += 1
                    question_metadata[q]['responses'].append(conv.response)
                    if conv.created_at > question_metadata[q]['last_asked']:
                        question_metadata[q]['last_asked'] = conv.created_at
        
        # Cluster similar questions
        question_clusters = faq_extractor.cluster_similar_questions(all_questions)
        
        # Prepare FAQ results
        faqs = []
        for cluster in question_clusters:
            if len(cluster) == 0:
                continue
                
            # Use the most frequent question as the main question
            main_question = max(cluster, key=lambda q: question_metadata[q]['frequency'])
            metadata = question_metadata[main_question]
            
            if metadata['frequency'] >= min_frequency:
                faqs.append(FAQ(
                    question=main_question,
                    similar_questions=[q for q in cluster if q != main_question],
                    frequency=metadata['frequency'],
                    typical_response=max(set(metadata['responses']), 
                                      key=metadata['responses'].count),
                    topic_category="",  # Would be populated based on topic modeling
                    last_asked=metadata['last_asked']
                ))
        
        # Sort by frequency
        faqs.sort(key=lambda x: x.frequency, reverse=True)
        
        return faqs
    
    except Exception as e:
        logger.error(f"Error in FAQ analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Error analyzing FAQs")

@router.get("/analytics/topics/frequency", response_model=List[TopicFrequency])
async def get_topic_frequency(
    days: Optional[int] = 30,
    min_frequency: Optional[int] = 5,
    db: Session = Depends(get_db)
):
    """Analyze frequently discussed topics"""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Fetch conversations
        conversations = db.query(Conversation).filter(
            Conversation.created_at >= cutoff_date
        ).all()
        
        if not conversations:
            raise HTTPException(status_code=404, detail="No conversations found")
        
        # Initialize analyzers
        preprocessor = TextPreprocessor()
        topic_analyzer = TopicFrequencyAnalyzer(preprocessor)
        
        # Prepare conversation data
        texts = [conv.message for conv in conversations]
        metadata = [{
            'created_at': conv.created_at,
            'customer_type': conv.customer_type
        } for conv in conversations]
        
        # Analyze topics
        topic_analysis = topic_analyzer.analyze_topic_distribution(texts, metadata)
        
        # Prepare results
        topics = []
        for phrase, freq in topic_analysis['key_phrases']:
            if freq >= min_frequency:
                # Find example messages containing this phrase
                examples = [text for text in texts 
                          if phrase.lower() in text.lower()][:3]
                
                topics.append(TopicFrequency(
                    topic=phrase,
                    frequency=int(freq),
                    example_messages=examples,
                    related_faqs=[],  # Would be populated based on FAQ analysis
                    customer_types=topic_analysis['customer_distribution'],
                    temporal_distribution=topic_analysis['time_distribution']
                ))
        
        return topics
    
    except Exception as e:
        logger.error(f"Error in topic frequency analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Error analyzing topic frequency")