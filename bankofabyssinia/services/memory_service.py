import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from langgraph.store.memory import InMemoryStore
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from config import UserProfile, MEMORY_EXPIRY

logger = logging.getLogger(__name__)

class MemoryService:
    def __init__(self):
        self.store = InMemoryStore()
        self._active_threads: Dict[str, str] = {}  # phone_number -> thread_id
        self._conversation_cache: Dict[str, Tuple[List[BaseMessage], datetime]] = {}
        self._cache_lock = asyncio.Lock()
        self._last_activity: Dict[str, datetime] = {}
        logger.info("Memory service initialized")
    
    def _get_namespace(self, phone_number: str) -> tuple:
        """Get namespace tuple for a user"""
        return (phone_number, "conversation")
    
    async def _cleanup_inactive_threads(self):
        """Remove inactive threads and their cached data"""
        current_time = datetime.now()
        to_remove = []
        
        for phone_number, last_active in self._last_activity.items():
            if (current_time - last_active) > timedelta(seconds=MEMORY_EXPIRY):
                to_remove.append(phone_number)
        
        for phone_number in to_remove:
            async with self._cache_lock:
                if phone_number in self._active_threads:
                    del self._active_threads[phone_number]
                if phone_number in self._conversation_cache:
                    del self._conversation_cache[phone_number]
                del self._last_activity[phone_number]
                logger.info(f"Cleaned up inactive thread for {phone_number}")
    
    def get_or_create_thread(self, phone_number: str) -> str:
        """Get existing thread ID or create new one"""
        self._last_activity[phone_number] = datetime.now()
        
        if phone_number in self._active_threads:
            logger.debug(f"Retrieved existing thread for {phone_number}")
            return self._active_threads[phone_number]
        
        # Use phone number as thread ID for simplicity and uniqueness
        thread_id = phone_number
        self._active_threads[phone_number] = thread_id
        logger.info(f"Created new thread {thread_id} for {phone_number}")
        return thread_id
    
    async def initialize_memory(self, profile: UserProfile) -> None:
        """Initialize or update user memory with profile"""
        try:
            namespace = self._get_namespace(profile.phone_number)
            self._last_activity[profile.phone_number] = datetime.now()
            
            # Store profile information
            self.store.put(
                namespace,
                "profile",
                profile.dict()
            )
            
            # Initialize empty conversation history if not exists
            if not self.store.get(namespace, "messages"):
                self.store.put(namespace, "messages", [])
                logger.info(f"Initialized new conversation history for {profile.phone_number}")
            else:
                logger.debug(f"Using existing conversation history for {profile.phone_number}")
                
            # Trigger cleanup of inactive threads
            await self._cleanup_inactive_threads()
                
        except Exception as e:
            logger.error(f"Error initializing memory for {profile.phone_number}: {str(e)}")
            raise
    
    def _get_messages_from_store(self, messages) -> List[BaseMessage]:
        """Helper method to extract messages from store item"""
        if messages is None:
            return []
        elif hasattr(messages, 'value'):  # Handle langgraph.store.base.Item
            return messages.value if isinstance(messages.value, list) else []
        elif isinstance(messages, list):
            return messages
        else:
            logger.error(f"Invalid message format: {type(messages)}")
            return []

    async def add_message(
        self,
        phone_number: str,
        message: BaseMessage
    ) -> None:
        """Add a message to the conversation history"""
        try:
            self._last_activity[phone_number] = datetime.now()
            namespace = self._get_namespace(phone_number)
            
            # Update cache and store
            async with self._cache_lock:
                # Get messages from cache or store
                if phone_number in self._conversation_cache:
                    messages, _ = self._conversation_cache[phone_number]
                else:
                    messages = self._get_messages_from_store(
                        self.store.get(namespace, "messages")
                    )
                
                messages.append(message)
                
                # Update both cache and store
                self._conversation_cache[phone_number] = (messages, datetime.now())
                self.store.put(namespace, "messages", messages)
                
            logger.debug(f"Added message for {phone_number}: {message.__class__.__name__}")
            
        except Exception as e:
            logger.error(f"Error adding message for {phone_number}: {str(e)}")
            raise
    
    async def get_conversation_history(
        self,
        phone_number: str,
        limit: int = 10
    ) -> List[BaseMessage]:
        """Get recent conversation history"""
        try:
            self._last_activity[phone_number] = datetime.now()
            
            # Check cache first
            async with self._cache_lock:
                if phone_number in self._conversation_cache:
                    messages, cached_time = self._conversation_cache[phone_number]
                    if datetime.now() - cached_time < timedelta(seconds=MEMORY_EXPIRY):
                        history = messages[-limit:]
                        logger.debug(f"Retrieved {len(history)} messages from cache for {phone_number}")
                        return history
            
            # If not in cache or expired, get from store
            namespace = self._get_namespace(phone_number)
            messages = self._get_messages_from_store(
                self.store.get(namespace, "messages")
            )
            
            # Update cache
            async with self._cache_lock:
                self._conversation_cache[phone_number] = (messages, datetime.now())
            
            history = messages[-limit:]
            logger.debug(f"Retrieved {len(history)} messages from store for {phone_number}")
            return history
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history for {phone_number}: {str(e)}")
            raise
    
    async def get_profile(self, phone_number: str) -> Optional[UserProfile]:
        """Retrieve stored profile for a user"""
        try:
            namespace = self._get_namespace(phone_number)
            profile_data = self.store.get(namespace, "profile")
            
            if profile_data:
                logger.debug(f"Retrieved profile for {phone_number}")
                return UserProfile(**profile_data.dict())
                
            logger.warning(f"No profile found for {phone_number}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving profile for {phone_number}: {str(e)}")
            raise

    async def close(self):
        """Cleanup resources"""
        self._conversation_cache.clear()
        self._active_threads.clear()
        self._last_activity.clear()
        logger.info("Memory service cleaned up")
