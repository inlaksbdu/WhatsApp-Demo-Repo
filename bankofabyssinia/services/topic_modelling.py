from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, and_
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from models.database import Conversation, get_db
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk
from textblob import TextBlob
import spacy
import re
from pydantic import BaseModel
from collections import Counter
import logging
import json
from datetime import timezone
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from sentence_transformers import SentenceTransformer
import itertools
from collections import defaultdict

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')

# Initialize spaCy
nlp = spacy.load('en_core_web_sm')
from pydantic import BaseModel, ConfigDict
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




# Add new Pydantic models for FAQ and Topic Frequency
class FAQ(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    question: str
    similar_questions: List[str]
    frequency: int
    typical_response: str
    topic_category: str
    last_asked: datetime

class TopicFrequency(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    topic: str
    frequency: int
    example_messages: List[str]
    related_faqs: List[str]
    customer_types: Dict[str, int]
    temporal_distribution: Dict[str, int]
# Pydantic models
class TopicAnalysisResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    topic_id: int
    keywords: List[str]
    sample_messages: List[str]
    message_count: int
    probability: float
    temporal_trend: Dict[str, float]
    related_complaints: List[str]

class ConversationMetrics(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    total_conversations: int
    unique_customers: int
    avg_response_length: float
    topic_distribution: Dict[str, float]
    customer_type_distribution: Dict[str, float]
    temporal_patterns: Dict[str, int]
    common_topics: List[Dict[str, any]]

class ComplaintAnalytics(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    total_complaints: int
    type_distribution: Dict[str, int]
    avg_resolution_time: float
    status_distribution: Dict[str, int]
    complaint_trends: Dict[str, List[float]]

# Helper classes for text processing
class TextPreprocessor:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        # Add domain-specific stop words
        self.stop_words.update(['hi', 'hello', 'thanks', 'thank', 'please', 'would', 'like'])
        
    def clean_text(self, text: str) -> str:
        # Convert to lowercase
        text = text.lower()
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def preprocess(self, text: str) -> List[str]:
        # Clean text
        text = self.clean_text(text)
        # Tokenize
        tokens = word_tokenize(text)
        # Lemmatize and remove stop words
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens 
                 if token not in self.stop_words and len(token) > 2]
        return tokens

class TopicModeler:
    def __init__(self, n_topics=10):
        self.n_topics = n_topics
        self.vectorizer = TfidfVectorizer(max_features=1000,
                                        stop_words='english',
                                        max_df=0.95,
                                        min_df=2)
        self.lda = LatentDirichletAllocation(n_components=n_topics,
                                           random_state=42,
                                           max_iter=20)
        self.preprocessor = TextPreprocessor()

    def fit_transform(self, texts: List[str]):
        processed_texts = [' '.join(self.preprocessor.preprocess(text)) for text in texts]
        self.dtm = self.vectorizer.fit_transform(processed_texts)
        self.topic_distributions = self.lda.fit_transform(self.dtm)
        return self.topic_distributions

    def get_topic_words(self, n_words=10):
        feature_names = self.vectorizer.get_feature_names_out()
        topic_words = []
        for topic_idx, topic in enumerate(self.lda.components_):
            top_words_idx = topic.argsort()[:-n_words-1:-1]
            top_words = [feature_names[i] for i in top_words_idx]
            topic_words.append(top_words)
        return topic_words

async def analyze_conversations(db: Session = Depends(get_db), days: int = 30):
    """Comprehensive conversation analysis"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Fetch conversations
    conversations = db.query(Conversation).filter(
        Conversation.created_at >= cutoff_date
    ).all()
    
    if not conversations:
        raise HTTPException(status_code=404, detail="No conversations found in specified period")
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame([{
        'message': conv.message,
        'response': conv.response,
        'customer_type': conv.customer_type,
        'created_at': conv.created_at,
        'whatsapp_profile_name': conv.whatsapp_profile_name
    } for conv in conversations])
    
    # Initialize topic modeler
    topic_modeler = TopicModeler(n_topics=8)  # Adjust number of topics based on your needs
    topic_distributions = topic_modeler.fit_transform(df['message'].fillna(''))
    topic_words = topic_modeler.get_topic_words()
    
    # Get dominant topic for each message
    df['dominant_topic'] = topic_distributions.argmax(axis=1)
    
    # Temporal analysis
    df['hour'] = df['created_at'].dt.hour
    hourly_distribution = df.groupby('hour').size().to_dict()
    
    # Calculate topic trends over time
    df['date'] = df['created_at'].dt.date
    topic_trends = {}
    for topic_idx in range(len(topic_words)):
        topic_trend = df[df['dominant_topic'] == topic_idx].groupby('date').size()
        topic_trends[f"topic_{topic_idx}"] = topic_trend.tolist()
    
    # Analyze customer types
    customer_distribution = df['customer_type'].value_counts().to_dict()
    
    # Calculate response statistics
    df['response_length'] = df['response'].str.len()
    avg_response_length = df['response_length'].mean()
    
    # Get sample messages for each topic
    sample_messages = []
    for topic_idx in range(len(topic_words)):
        topic_msgs = df[df['dominant_topic'] == topic_idx]['message'].head(3).tolist()
        sample_messages.append(topic_msgs)
    
    # Prepare topic insights
    topic_insights = []
    for topic_idx, words in enumerate(topic_words):
        topic_insights.append({
            'topic_id': topic_idx,
            'keywords': words,
            'sample_messages': sample_messages[topic_idx],
            'message_count': int(df['dominant_topic'].value_counts().get(topic_idx, 0)),
            'probability': float(topic_distributions[:, topic_idx].mean())
        })
    
    return {
        'total_conversations': len(conversations),
        'unique_customers': df['whatsapp_profile_name'].nunique(),
        'avg_response_length': float(avg_response_length),
        'topic_distribution': {f"Topic {i}": float(v) 
                             for i, v in enumerate(topic_distributions.mean(axis=0))},
        'customer_type_distribution': customer_distribution,
        'temporal_patterns': hourly_distribution,
        'common_topics': topic_insights
    }




class FAQExtractor:
    def __init__(self):
        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.similarity_threshold = 0.85
        self.vectorizer = CountVectorizer(ngram_range=(1, 3))
        
    def extract_questions(self, text: str) -> List[str]:
        """Extract potential questions from text"""
        doc = nlp(text)
        questions = []
        
        # Pattern matching for question-like structures
        question_patterns = [
            r"(?i)^(what|how|why|when|where|who|can|could|would|will|should|do|does|did|is|are|was|were).*\?",
            r"(?i)^(please|kindly|help|need).*\?",
            r"(?i).*\b(help|assist|guide|explain|tell)\b.*\?"
        ]
        
        if any(re.match(pattern, text.strip()) for pattern in question_patterns):
            questions.append(text.strip())
            
        return questions
    
    def cluster_similar_questions(self, questions: List[str]) -> List[List[str]]:
        """Group similar questions together"""
        if not questions:
            return []
            
        # Encode questions using SBERT
        embeddings = self.model.encode(questions)
        
        # Calculate similarity matrix
        similarities = cosine_similarity(embeddings)
        
        # Cluster similar questions
        clusters = []
        used_indices = set()
        
        for i in range(len(questions)):
            if i in used_indices:
                continue
                
            cluster = [i]
            used_indices.add(i)
            
            for j in range(i + 1, len(questions)):
                if j not in used_indices and similarities[i][j] >= self.similarity_threshold:
                    cluster.append(j)
                    used_indices.add(j)
                    
            clusters.append([questions[idx] for idx in cluster])
            
        return clusters

class TopicFrequencyAnalyzer:
    def __init__(self, preprocessor: TextPreprocessor):
        self.preprocessor = preprocessor
        self.vectorizer = CountVectorizer(ngram_range=(1, 3))
        
    def extract_key_phrases(self, texts: List[str], top_n: int = 10) -> List[tuple]:
        """Extract most frequent key phrases from texts"""
        processed_texts = [' '.join(self.preprocessor.preprocess(text)) for text in texts]
        vectors = self.vectorizer.fit_transform(processed_texts)
        
        # Get feature names and their frequencies
        feature_names = self.vectorizer.get_feature_names_out()
        frequencies = vectors.sum(axis=0).A1
        
        # Sort by frequency
        key_phrases = [(feature_names[i], frequencies[i]) 
                      for i in frequencies.argsort()[::-1][:top_n]]
        
        return key_phrases
    
    def analyze_topic_distribution(self, texts: List[str], metadata: List[dict]) -> Dict:
        """Analyze topic distribution with metadata"""
        key_phrases = self.extract_key_phrases(texts)
        
        # Group by time periods
        time_distribution = defaultdict(int)
        customer_distribution = defaultdict(int)
        
        for text, meta in zip(texts, metadata):
            hour = meta['created_at'].hour
            time_distribution[hour] += 1
            customer_distribution[meta['customer_type']] += 1
            
        return {
            'key_phrases': key_phrases,
            'time_distribution': dict(time_distribution),
            'customer_distribution': dict(customer_distribution)
        }