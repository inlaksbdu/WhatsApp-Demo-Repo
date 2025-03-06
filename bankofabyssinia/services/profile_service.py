import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List
import json
import logging
from config import (
    CUSTOMER_INFO_ENDPOINT,
    CustomerDetails,
    UserProfile,
    CustomerType,
    AccountDetails,
    MEMORY_EXPIRY,
    ACCOUNT_DETAILS_ENDPOINT
)
# customer_endpoint = 
logger = logging.getLogger(__name__)
print(f'customer endpoint {CUSTOMER_INFO_ENDPOINT}')

class ProfileService:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._profile_cache: Dict[str, Tuple[UserProfile, datetime]] = {}
        self._cache_lock = asyncio.Lock()
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with connection pooling"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=aiohttp.TCPConnector(limit=100)
            )
        return self._session
    
    async def close(self):
        """Close the session and clear cache"""
        if self._session and not self._session.closed:
            await self._session.close()
        self._profile_cache.clear()
    
    def _clean_phone_number(self, phone: str) -> str:
        """Remove any non-numeric characters from phone number"""
        return ''.join(filter(str.isdigit, phone))
    
    async def _get_cached_profile(self, phone_number: str) -> Optional[UserProfile]:
        """Get profile from cache if it exists and is not expired"""
        async with self._cache_lock:
            if phone_number in self._profile_cache:
                profile, cached_time = self._profile_cache[phone_number]
                if datetime.now() - cached_time < timedelta(seconds=MEMORY_EXPIRY):
                    logger.debug(f"Cache hit for {phone_number}")
                    return profile
                else:
                    logger.debug(f"Cache expired for {phone_number}")
                    del self._profile_cache[phone_number]
            return None
    
    async def _cache_profile(self, phone_number: str, profile: UserProfile):
        """Cache profile with timestamp"""
        async with self._cache_lock:
            self._profile_cache[phone_number] = (profile, datetime.now())
    
    # async def fetch_customer_profile(self, phone_number: str) -> UserProfile:
    #     """Fetch customer profile from API or cache with improved error handling"""
    #     try:
    #         # Check cache first
    #         cached_profile = await self._get_cached_profile(phone_number)
    #         if cached_profile:
    #             return cached_profile
            
    #         clean_number = self._clean_phone_number(phone_number)
    #         logger.info(f"Fetching profile for {clean_number}")
            
    #         session = await self.get_session()
    #         async with session.get(
    #             CUSTOMER_INFO_ENDPOINT,
    #             params={"mobileNumber": clean_number},
    #             timeout=10
    #         ) as response:
    #             if response.status != 200:
    #                 logger.warning(f"API returned status {response.status} for {clean_number}")
    #                 return await self._handle_non_customer(phone_number)
                
    #             data = await response.json()
                
    #             # Check response structure
    #             if not data.get("body") or not data["body"]:
    #                 logger.info(f"No customer data found for {clean_number}")
    #                 return await self._handle_non_customer(phone_number)
                
    #             try:
    #                 customer_data = data["body"][0]
    #                 customer_details = CustomerDetails(**customer_data)
                    
    #                 profile = UserProfile(
    #                     phone_number=phone_number,
    #                     customer_type=CustomerType.EXISTING,
    #                     customer_details=customer_details,
    #                     last_updated=datetime.now()
    #                 )
                    
    #                 # Cache the successful profile
    #                 await self._cache_profile(phone_number, profile)
    #                 logger.info(f"Successfully created profile for existing customer {clean_number}")
    #                 return profile
                    
    #             except Exception as e:
    #                 logger.error(f"Error parsing customer data: {str(e)}")
    #                 return await self._handle_non_customer(phone_number)
                
    #     except asyncio.TimeoutError:
    #         logger.error(f"Timeout fetching profile for {phone_number}")
    #         return await self._handle_non_customer(phone_number)
    #     except Exception as e:
    #         logger.error(f"Error fetching customer profile: {str(e)}")
    #         return await self._handle_non_customer(phone_number)
    async def _fetch_account_details(self, customer_number: str) -> List[Dict]:
        """Fetch account details for a customer"""
        try:
            session = await self.get_session()
            logger.info(f"Fetching account details for customer: {customer_number}")
            
            async with session.get(
                ACCOUNT_DETAILS_ENDPOINT,
                params={"customerNumber": customer_number}
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch account details. Status: {response.status}")
                    return []
                    
                data = await response.json()
                logger.info(f"Account details response: {data}")
                
                if not data.get("body"):
                    logger.warning(f"No account details found for customer: {customer_number}")
                    return []
                
                accounts = data["body"]
                logger.info(f"Found {len(accounts)} accounts for customer: {customer_number}")
                return accounts
                
        except Exception as e:
            logger.error(f"Error fetching account details: {str(e)}")
            return []

    async def fetch_customer_profile(self, phone_number: str) -> UserProfile:
        try:
            cached_profile = await self._get_cached_profile(phone_number)
            if cached_profile:
                return cached_profile
            
            clean_number = self._clean_phone_number(phone_number)
            session = await self.get_session()
            
            async with session.get(
                CUSTOMER_INFO_ENDPOINT,
                params={"mobileNumber": clean_number}
            ) as response:
                if response.status != 200:
                    return await self._handle_non_customer(phone_number)
                logger.info(f'customer endpoint {CUSTOMER_INFO_ENDPOINT}')
                data = await response.json()
                if not data.get("body") or not data["body"]:
                    return await self._handle_non_customer(phone_number)
                
                try:
                    customer_data = data["body"][0]
                    customer_details = CustomerDetails(**customer_data)
                    
                    if customer_details.customerNumber:
                        accounts = await self._fetch_account_details(customer_details.customerNumber)
                        customer_details.accounts = accounts
                        logger.info(f"Successfully fetched account details {accounts}")
                    
                    profile = UserProfile(
                        phone_number=phone_number,
                        customer_type=CustomerType.EXISTING,
                        customer_details=customer_details,
                        last_updated=datetime.now()
                    )
                    
                    await self._cache_profile(phone_number, profile)
                    return profile
                    
                except Exception as e:
                    logger.error(f"Error parsing customer data: {str(e)}")
                    return await self._handle_non_customer(phone_number)
                
        except Exception as e:
            logger.error(f"Error fetching customer profile: {str(e)}")
            return await self._handle_non_customer(phone_number)
    
    async def _handle_non_customer(self, phone_number: str) -> UserProfile:
        """Create and cache profile for non-customers"""
        profile = UserProfile(
            phone_number=phone_number,
            customer_type=CustomerType.PROSPECT,
            customer_details=None,
            last_updated=datetime.now()
        )
        await self._cache_profile(phone_number, profile)
        return profile
    
    # def get_greeting(self, profile: UserProfile) -> str:
    #     """Get personalized greeting based on customer type"""
    #     if profile.customer_type == CustomerType.EXISTING:
    #         name = profile.customer_details.fullName.split()[0]  # Use first name for friendliness
    #         return f"Hello {name}, welcome back to GBC! 🏦 How may I assist you today?"
    #     return (
    #         "Welcome to GBC! 🏦 While I notice you don't have an account with us yet, "
    #         "I'm happy to provide information about our services and guide you through "
    #         "opening an account. How may I assist you?"
    #     )

    #     """Get personalized greeting based on customer type"""
    #     try:
    #         if profile.customer_type == CustomerType.EXISTING:
    #             name = profile.customer_details.fullName.split()[0] if profile.customer_details else "there"
    #             return f"Hello {name}, welcome back to CBG! 🏦 How may I assist you today?"
    #         return "Welcome to CBG! 🏦 I notice you don't have an account with us yet. I'm happy to provide information about our services and guide you on how to open an account. How may I assist you?"
    #     except Exception as e:
    #         logger.error(f"Error generating greeting: {str(e)}")
    #         return "Welcome to CBG! 🏦 How may I assist you today?"
