import json
import random
import secrets
import ssl
import string
import certifi
from itsdangerous import URLSafeTimedSerializer
from langchain_core.tools import StructuredTool, Tool
import logging
from utils import TEMP_ROUTES, AsyncEmailService, generate_reference_code, get_fernet_key, text_to_whatsapp_audio
from models.database import Appointment, AppointmentStatus, BankRequest, BankStatementRequest, CancellationReason, ComplainStatus, Complaint, Conversation, RejectionReason, RequestStatus, Transfer
from models.database import PinManagement, get_db
from services.profile_service import ProfileService
from services.memory_service import MemoryService
from typing import Coroutine, Optional, Dict, Any, List, Union, Tuple
import aiohttp
from pydantic import EmailStr, Field, BaseModel, validator
from datetime import datetime, timedelta
from langchain_core.tools import Tool
import asyncio
import os
from fastapi import Depends
from functools import wraps
from twilio.rest import Client
from services.sms_service import SMSService
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from models.database import engine 
from models.database import Complaint
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from models.database import OTPManagement
from langchain_deepseek import ChatDeepSeek
from langchain_google_genai import ChatGoogleGenerativeAI
import random
import string
from langchain_together  import ChatTogether
from datetime import datetime, timedelta
from loguru import logger
from textblob import TextBlob
from googletrans import Translator
profile_service = ProfileService()
memory_service = MemoryService
from dotenv import load_dotenv
load_dotenv()


TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_NUM')
BANK_BASE_URL = os.getenv('BASE_URL')
BACKEND_URL = os.getenv('BACKEND_URL')
VERIFY_URL = os.getenv('VERIFY_URL')
TWILIO_NUM = os.getenv('TWILIO_NUM')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')
os.environ['TOGETHER_API_KEY']=TOGETHER_API_KEY
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
os.environ['DEEPSEEK_API_KEY']= DEEPSEEK_API_KEY
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY

class GetStatementInputSchema(BaseModel):
    accountNo: str = Field(..., description="Account number")
    startDate: str = Field(..., description="Start date in the format YYYYMMDD")
    endDate: str = Field(..., description="End date in the format YYYYMMDD")
    customer_number: str = Field(..., description= "customer 3 digit number")

class GetStatementInputSchema(BaseModel):
    accountNo: str = Field(..., description="Account number")
    startDate: str = Field(..., description="Start date in the format YYYYMMDD")
    endDate: str = Field(..., description="End date in the format YYYYMMDD")
    customer_number: str = Field(..., description= "customer 3 digit number")

class TranslationInput(BaseModel):
    english_response: str = Field(..., description="The text to be translated")
    target_language: str = Field(..., description="The language code to translate to (e.g., 'am' for amharic, 'om' for afan oromo)")

class TransferInput(BaseModel):
    customer_number: str = Field(..., description="Customer 5-digit number from customer info")
    creditAccountId: str = Field(..., description="Recipient account number")
    debitAccountId: str = Field(..., description="Sender account number")
    debitAmount: str = Field(..., description="Amount to transfer in ETB")
    paymentDetails: str = Field(..., description="Purpose of transfer in English")
    customer_name: str = Field(..., description="Name of the customer from profile")
    Mobile_Number: str = Field(..., description="Customer mobile number with '+' and country code from customer profile")

class AccountBalanceInput(BaseModel):
    customer_number: str = Field(..., description="Correct customer number from profile info")

class ComplaintInput(BaseModel):
    name: str = Field(..., description="Name of the user creating the complaint")
    email: str = Field(..., description="Email address of the user creating the complaint")
    complaint_type: str = Field(..., description="Type of complaint")
    description: str = Field(..., description="Description of the complaint")
    Mobile_Number: str = Field(..., description="Customer mobile number with '+' and country code from customer profile")

class UpdateComplaintInput(BaseModel):
    email: str = Field(..., description="Email address of the user used to create the complaint")
    update_data: Dict[str, Any] = Field(..., description="Dictionary containing fields to update")

class GetComplaintsInput(BaseModel):
    email: str = Field(..., description="Email address of the user used to create the complaint")

class BankBookingInput(BaseModel):
    customer_name: str = Field(..., description="Name of the customer")
    email: str = Field(..., description="Email address of the customer")
    service_type: str = Field(..., description="Type of service (Account/Loan/Card/Transfer/Investment)")
    service_details: Dict[str, Any] = Field(..., description="JSON object containing service-specific details")
    Mobile_Number: str = Field(..., description="Customer mobile number with '+' and country code from customer profile")
    preferred_date: Optional[str] = Field(None, description="Optional preferred date for processing")
    @validator("service_details", pre=True)
    def parse_service_details(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v
    
class GetBankBookingInput(BaseModel):
    reference_code: str = Field(..., description="reference code generated for customer after bank booking")
   

class SecureLinkInput(BaseModel):
    customer_number: str = Field(..., description="5-digit string customer number from profile")
    mobile_number: str = Field(..., description="Customer 12 digit mobile number (e.g 233558158591)")

class AccountStatementInput(BaseModel):
    customer_number: str = Field(..., description="Customer 5 digit identification number")
    customer_name: str = Field(..., description="Customer name from profile info")
    accountNo: str = Field(..., description="Account number")
    startDate: str = Field(..., description="Start date (format: YYYYMMDD)")
    endDate: str = Field(..., description="End date (format: YYYYMMDD)")
    Mobile_Number: str = Field(..., description="Customer mobile number with '+' and country code from customer profile")

class AppointmentInput(BaseModel):
    customer_name: str = Field(..., description="Name of the customer")
    email: str = Field(..., description="Email address of the customer")
    phone_number: str = Field(..., description="Phone number with country code")
    appointment_type: str = Field(..., description="Type of appointment (faccount_opening, loan_consultation, investment_advisory, general_inquiry, complaint_resolution)")
    preferred_date: str = Field(..., description="Preferred date (YYYY-MM-DD)")
    preferred_time: str = Field(..., description="Preferred time (HH:MM)")
    location: str = Field(..., description="Location for the appointment")
    additional_notes: Optional[str] = Field(None, description="Optional additional notes")
    Mobile_Number: str = Field(..., description="Customer mobile number with '+' and country code from customer profile")

class GetAppointmentInput(BaseModel):
    reference_code: str = Field(..., description="Reference code of the booking")

class GenerateOtpInput(BaseModel):
    mobile_number: str = Field(..., description="Customer's mobile number with country code (e.g., +233559158793)")

class GenerateCreateAccountInput(BaseModel):
    otp_code: str = Field(..., description="otp code sent to user")
    identifier: str = Field(..., description="identifier generated when generating otp code")

class SendAudioInput(BaseModel):
    text_response: str = Field(..., description="Text to convert to speech")
    phone_number: str = Field(..., description="recepient's phone number from info")

class VerifyCreditAccount(BaseModel):
    credit_account_number: str = Field(..., description="credit account provided by the user")
   
class BankStatementInput(BaseModel):
    customer_email: EmailStr = Field(..., description="Valid email address of the customer")
    account_no: str = Field(..., description="Account number for reference")
    customer_name: str = Field(..., description="Customer's full name from customer info")
    credit_account_id: str = Field(..., description="Recipient account number")
    transactions: Dict[str, Dict[str, str]] = Field(..., description="Dictionary of transactions with date, type, debit, credit, and balance")

class EscalationEmailInput(BaseModel):
    escalating_to: EmailStr = Field(..., description="Email of the supervisor/department to escalate to")
    customer_email: EmailStr = Field(..., description="Customer's email")
    customer_name: str = Field(..., description="Customer's full name")
    mobile_number: str = Field(..., description="Customer mobile number with '+' and country code")
    conversation_summary: str = Field(..., description="Detailed issue description")
    customer_mood: str = Field(..., description="Customer's emotional state")


class BankingAPIClient:
    BASE_URL = os.getenv('BASE_URL') #"http://18.198.5.151:9095/gticontainer/api/v1.0.0/party"
    HEADERS = {"companyId": "GB0010001", "Content-Type": "application/json"}

    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def make_api_request(self, endpoint: str, method: str = "GET", params: Dict = None, json_data: Dict = None) -> Dict:
        """Make API request with error handling and logging"""
        try:
            async with self.session.request(
                method=method,
                url=f"{self.BASE_URL}/{endpoint}",
                headers=self.HEADERS,
                params=params,
                json=json_data
            ) as response:
                response_data = await response.json()
                if not response.ok:
                    logger.error(f"API error: {response.status} - {response_data}")
                    raise ValueError(f"API request failed: {response.status}")
                return response_data
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            raise

# def async_tool(func):
#     """Decorator to handle async tools properly"""
#     @wraps(func)
#     async def wrapper(*args, **kwargs):
#         return await func(*args, **kwargs)
#     return wrapper


# def async_tool(func):
#     """Decorator to handle async tools properly"""
#     @wraps(func)
#     async def wrapper(*args, **kwargs):
#         return await func(*args, **kwargs)
#     return wrapper


class BankingTools:
    def __init__(self):
        self.client = None
        self.db_session = get_db
        self.TEMP_ROUTES: Dict = {}
        self.email_service = AsyncEmailService()
        self.serializer = URLSafeTimedSerializer(os.environ["SECRET_KEY"])

    async def get_client(self):
        """Get or create API client"""
        if self.client is None:
            self.client = BankingAPIClient()
        return self.client

    def _generate_mnemonic(self, first_name: str, surname: str, dob: str) -> str:
        """Generate mnemonic from name and date of birth"""
        name_part = (first_name[:2] + surname[:2]).upper()
        return f"{name_part}{dob}"

    def _format_names(self, first_name: str, surname: str, other_name: str = "") -> dict:
        """Format various name fields"""
        if other_name:
            full_name = f"{first_name} {other_name} {surname}"
        else:
            full_name = f"{first_name} {surname}"
        
        short_name = f"{first_name} {surname}"
        
        return {
            "fullName": full_name.strip(),
            "fullName2": "",
            "shortName": short_name.strip()
        }

    # @async_tool

    def _run_async(self, coro: Coroutine):     
        """Helper to run coroutines in sync context"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

     

    # @async_tool
    async def make_transfer(self, customer_number: str, creditAccountId:str,debitAccountId:str, debitAmount:str, paymentDetails:str, customer_name:str, Mobile_Number:str) -> str:
        """
        Make fund transfers between accounts.
        Args:
                customer_number: customer 5-digit number from customer info
                creditAccountId: Recipient account number
                debitAccountId: Sender account number
                debitAmount: Amount to transfer in ETB
                paymentDetails: Purpose of transfer in English
                customer_name: Name of the customer from profile
                Mobile_Number: -> customer mobile number with "+" and country code from customer profile
        Returns:
            Transfer status message
        """
        try:
            # 1. Get encrypted PIN from database
            db = next(self.db_session())
            pin_record = db.query(PinManagement).filter(
                PinManagement.customer_number == customer_number
            ).first()
            
            if not pin_record:
                return "PIN not set for this customer. Please send verification link to the user first."
                
            # 2. Decrypt PIN using Fernet
            fernet = Fernet(get_fernet_key(os.environ["SECRET_KEY"]))  # Replace with your Fernet key
            decrypted_pin = fernet.decrypt(pin_record.encrypted_pin.encode()).decode()
            logger.info(f"Decrypted PIN: {decrypted_pin}")
            
            # 3. Verify PIN with banking system
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                verify_response = await session.post(
                    f"{VERIFY_URL}",
                    json={
                        "customer_number": customer_number,
                        "secure_pin": decrypted_pin
                    }
                )
                
                if verify_response.status != 200:
                    return "PIN verification failed. Ask the user to try again."
                
                pin = await verify_response.json()
                logger.info(f"PIN verification response: {pin}")
                status = pin["status"]
                logger.info(f"PIN status: {status} (Type: {type(status)})")
                
                if status is False:
                    return "User entered a wrong PIN. Remind the user to enter the correct PIN or else this account can be blocked!"
                
                # 4. Make the transfer
                try:
                    client = await self.get_client()
                    async with client as session:
                        try:
                            # Make the API request with explicit error catching
                            response = await session.make_api_request(
                                "creategtiFundsTransfer",
                                method="POST",
                                json_data={
                                    "body": {
                                        "creditAccountId": creditAccountId,
                                        "debitAccountId": debitAccountId,
                                        "debitAmount": debitAmount,
                                        "debitCurrency": "USD",
                                        "transactionType": "AC",
                                        "debitValueDate": "",
                                        "creditCurrencyId": "USD",
                                        "creditAmount": "",
                                        "paymentDetails": paymentDetails,
                                        "channel": "",
                                        "eternalRef": "",
                                        "override": "",
                                        "recordStatus": "",
                                        "inputterId": "",
                                        "dateAndTime": "",
                                        "authoriser": "",
                                        "companyCode": "",
                                        "extensions": {}
                                    }
                                }
                            )
                        except Exception as api_error:
                            logger.error(f"API Request Error: {api_error}")
                            logger.error(f"Error Type: {type(api_error)}")
                            
                            # Log the error details if available
                            if hasattr(api_error, 'response'):
                                try:
                                    error_response = await api_error.response.json()
                                    logger.error(f"Detailed Error Response: {error_response}")
                                    
                                    # Extract specific error message
                                    if 'error' in error_response and 'errorDetails' in error_response['error']:
                                        specific_error = error_response['error']['errorDetails'][0]['message']
                                        return f"Transfer failed: {specific_error}"
                                except Exception as parse_error:
                                    logger.error(f"Error parsing response: {parse_error}")
                            
                            # Fallback error return
                            return f"Transfer failed: {str(api_error)}"
                        
                        # Log the full API response
                        logger.info(f"API Response: {response}")
                        
                        # Check if the transfer was successful
                        if response.get("header", {}).get("status") == "failed":
                            error_details = response.get("error", {}).get("errorDetails", [])
                            error_message = "Transfer failed due to the following errors:\n"
                            for error in error_details:
                                error_message += f"- {error.get('message', 'Unknown error')}\n"
                            return error_message
                        
                        # # Clear profile cache and delete PIN record
                        # mobileNumber = transfer_data["Mobile Number"]
                        # async with profile_service._cache_lock:
                        #     if mobileNumber in profile_service._profile_cache:
                        #         del profile_service._profile_cache[mobileNumber]
                        
                        # number = transfer_data["Mobile Number"].replace('+', '')
                        # profile = await profile_service.fetch_customer_profile(number)
                        # await memory_service.initialize_memory(profile)
                        db.delete(pin_record)
                        db.commit()
                        logger.info(f"Deleted PIN record for customer_number {customer_number}")
                        currency = 'ETB'
                        # Save transfer details to the Transfer table
                        try:
                            phone_number = Mobile_Number
                            if "+" in phone_number:
                                clean_number = phone_number
                                logger.info("Plus sign is present")
                            else:
                                clean_number = f"+{phone_number}"
                                logger.info("Plus sign is not present, plus added")

                            # Get the latest conversation for this customer
                            latest_conversation = db.query(Conversation)\
                                .filter(Conversation.phone_number == clean_number)\
                                .order_by(Conversation.created_at.desc())\
                                .first()

                            transfer_record = Transfer(
                                customer_name=customer_name,
                                amount=float(debitAmount),
                                credit_account_id=creditAccountId,
                                debit_account_id= debitAccountId,
                                payment_details=paymentDetails,
                                date=datetime.utcnow(),
                                conversation_id=latest_conversation.id if latest_conversation else None
                            )
                            db.add(transfer_record)
                            db.commit()
                            logger.info(f"Transfer record saved to database with ID: {transfer_record.id}")
                            
                            return f"Transfer completed successfully. Debit Account: {response['body']['debitAccountId']}, Amount: {response['body']['debitAmount']}. Reference: {response['header'].get('id', 'N/A')}, Currency: {currency}"
                            
                        except Exception as db_error:
                            logger.error(f"Failed to save transfer record: {str(db_error)}")
                            # Still return success message even if DB save fails
                            return f"Transfer completed successfully. Debit Account: {response['body']['debitAccountId']}, Amount: {response['body']['debitAmount']}. Reference: {response['header'].get('id', 'N/A')}"
                        
                except Exception as e:
                    logger.error(f"Unexpected transfer error: {str(e)}")
                    return f"Transfer failed: {str(e)}"
        
        except Exception as e:
            logger.error(f"Unexpected error in make_transfer: {str(e)}")
            return f"An unexpected error occurred: {str(e)}"

        return loop.run_until_complete(coro)
    

    def make_transfer_sync(self, customer_number: str, creditAccountId:str,debitAccountId:str, debitAmount:str, paymentDetails:str, customer_name:str, Mobile_Number:str) -> str:
        """Synchronous wrapper for create_customer_account"""
        return self._run_async(self.make_transfer(customer_number, creditAccountId,debitAccountId, debitAmount, paymentDetails, customer_name, Mobile_Number))
    

    # @async_tool
    async def get_exchange_rates(self, *args, **kwargs) -> str:
        """
        Get current exchange rates for all currencies.
        Note: This endpoint does not require any parameters.
        Returns:
            String containing formatted exchange rate information
        """
        # Explicitly ignore any passed arguments since this endpoint doesn't use them
        client = await self.get_client()
        async with client as session:
            # Call endpoint with no parameters
            response = await session.make_api_request("getExchangeRates")
            rates = response.get("body", [])
            
            formatted_rates = "Current Exchange Rates:\n"
            for rate in rates:
                if "ccy" in rate:
                    formatted_rates += (
                        f"Currency: {rate['ccy']}\n"
                        f"Buy: {rate.get('buyRate', 'N/A')}\n"
                        f"Sell: {rate.get('sellRate', 'N/A')}\n"
                        f"Mid: {rate.get('midRate', 'N/A')}\n"
                        f"Market: {rate.get('ccyMarket', 'N/A')}\n\n"
                    )
            
            return formatted_rates


    def get_exchange_rates_sync(self, *args, **kwargs) -> str:
        """
        Synchronous wrapper for get_exchange_rates.
        Accepts but ignores any arguments since the endpoint doesn't use them.
        """
        # Pass through args/kwargs but they won't affect the endpoint call
        return self._run_async(self.get_exchange_rates(*args, **kwargs))
        
        # @async_tool
    async def get_account_balance(self, customer_number: str) -> str:
        """Get customer account balance and details using their customer number

            customer_number: correct Customer number from profile info
        """
        
        try:
            # 1. Get encrypted PIN from database
            logger.info(f"customer number {customer_number}")
            db = next(self.db_session())
            pin_record = db.query(PinManagement).filter(
                PinManagement.customer_number == customer_number
            ).first()
            logger.info(f"pin record details {pin_record}")
            if not pin_record:
                return "PIN not set for this customer. Please send verification link to the user first."
                
            # 2. Decrypt PIN using Fernet
            fernet = Fernet(get_fernet_key(os.environ["SECRET_KEY"]))
            decrypted_pin = fernet.decrypt(pin_record.encrypted_pin.encode()).decode()
            logger.info(f"the decrypted pin--------------- {decrypted_pin}")
            
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                # Your existing code here
                verify_response = await session.post(
                    f"{VERIFY_URL}",
                    json={
                        "customer_number": customer_number,
                        "secure_pin": decrypted_pin
                    }
                )
                
                if verify_response.status != 200:
                    return "Ask the user to try again."
                
                pin = await verify_response.json()
                logger.info(f"PIN verification response: {pin}")
                status = pin["status"]
                
                if status is False:
                    return "User entered a wrong pin, remind user to enter correct pin or else this account can be blocked!"
                
                try:
                    number = customer_number
                    client = await self.get_client()
                    # Apply the same SSL context to this client if needed
                    async with client as session:
                        response = await session.make_api_request(
                        "getGtiAccountDetails",
                        params={"customerNumber": number},
                        method="GET"
                        ) 
                        account_data = response
                        accounts = account_data["body"]
                        formatted_response = f"Found {len(accounts)} account(s) for customer {customer_number}:\n\n"
                        currency = 'ETB'
                        for account in accounts:
                            formatted_response += (
                                f"Account Number: {account.get('accountNo', 'N/A')}\n"
                                f"Account Name: {account.get('accountName', 'N/A')}\n"
                                f"Account Type: {account.get('accountCategory', 'N/A')}\n"
                                f"Balance: {account.get('workingBalance', 'N/A')} {currency}\n"
                                f"Opening Date: {account.get('openingDate', 'N/A')}\n"
                                f"Account Officer: {account.get('accountOfficer', 'N/A')}\n"
                                f"Status: Active\n"
                                "------------------------\n"
                            )
                        db.delete(pin_record)
                        db.commit()
                        return formatted_response
                        
                except Exception as e:
                    logger.error(f"Error fetching account details: {str(e)}")
                    return f"Failed to get account details: {str(e)}"
        except Exception as e:
            return f"An error occurred: {str(e)}"


    def get_account_balance_sync(self, customer_number: str) -> str:
        """Synchronous wrapper for get_account_details"""
        return self._run_async(self.get_account_balance(customer_number))

    # @async_tool
    async def create_complaint(
        self,
        name:str, email:str, complaint_type:str, description:str, Mobile_Number:str
    ) -> Optional[Dict]:
        """Create a new complaint for user
        Args:
                name: Name of the user creating the complaint
                email: Email address of the user creating the complaint
                complaint_type: Type of complaint
                description: Description of the complaint
                Mobile_Number: -> customer mobile number with "+" and country code from customer profile
        """
        try:
            if "+" in Mobile_Number:
                clean_number = Mobile_Number
                logger.info("Plus sign is present")
            else:
                clean_number = f"+{Mobile_Number}"
                logger.info("Plus sign is not present, plus added")
            logger.info(f"clean number {clean_number}")
            db = next(self.db_session())
            
            # Get the latest conversation for tracking
            latest_conversation = db.query(Conversation)\
                .filter(Conversation.phone_number == clean_number)\
                .order_by(Conversation.created_at.desc())\
                .first()
            
            complaint = Complaint(
                name=name,
                email= email,
                phone_number= Mobile_Number,
                complaint_type=complaint_type,
                description= description,
                status=ComplainStatus.PENDING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                conversation_id=latest_conversation.id if latest_conversation else None
            )
            
            db.add(complaint)
            db.commit()
            db.refresh(complaint)
            
            return {
                "id": complaint.id,
                "reference_number": f"COMP-{complaint.id:06d}",
                "name": complaint.name,
                "email": complaint.email,
                "phone_number": complaint.phone_number,
                "complaint_type": complaint.complaint_type,
                "status": complaint.status.value,
                "created_at": complaint.created_at.isoformat(),
                "message": "Complaint registered successfully. Our team will contact you soon."
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating complaint: {str(e)}")
            raise
        finally:
            db.close()

    def create_complaint_sync(self, name:str, email:str, complaint_type:str,description:str, Mobile_Number:str) -> Dict:
        """Synchronous wrapper for create_complaint"""
        return self._run_async(self.create_complaint(name, email, complaint_type,description, Mobile_Number))

    async def update_complaint(
        self,
        email:str,
        update_data:dict  # Accept a single dictionary argument
    ) -> Optional[Dict]:
        """Update complaint by user email
        Args:
                email: Email address of the user used to create the complaint
                update_data: Dictionary containing fields to update
        """
        try:
            db = next(self.db_session())
            complaint = db.query(Complaint).filter(Complaint.email == email).first()
            
            if not complaint:
                return None
            
            for field, value in update_data.items():
                if hasattr(complaint, field):
                    setattr(complaint, field, value)
            
            complaint.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(complaint)
            
            return {
                "id": complaint.id,
                "name": complaint.name,
                "email": complaint.email,
                "phone_number": complaint.phone_number,
                "complaint_type": complaint.complaint_type,
                "description": complaint.description,
                "status": complaint.status,
                "created_at": complaint.created_at,
                "updated_at": complaint.updated_at
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating complaint: {str(e)}")
            raise
        finally:
            db.close()

    def update_complaint_sync(self, email:str, update_data:dict ) -> Optional[Dict]:
        """Synchronous wrapper for update_complaint"""
        return self._run_async(self.update_complaint(email, update_data))

    async def get_complaints_by_email(
        self,
        email:str  # Accept a single dictionary argument
    ) -> Optional[Dict]:
        """Get complaints by user email 
        Args:
                email: Email address of the user used to create the complaint
        """
        try:
            db = next(self.db_session())
            email = email
            complaints = db.query(Complaint).filter(Complaint.email == email).order_by(Complaint.created_at.desc()).all()
            
            return [{
                "id": complaint.id,
                "name": complaint.name,
                "email": complaint.email,
                "phone_number": complaint.phone_number,
                "complaint_type": complaint.complaint_type,
                "description": complaint.description,
                "status": complaint.status,
                "created_at": str(complaint.created_at),
                "updated_at": str(complaint.updated_at)
            } for complaint in complaints]
        except Exception as e:
            logger.error(f"Error getting complaints: {str(e)}")
            raise
        finally:
            db.close()

    def get_complaints_by_email_sync(self, email:str) ->Optional[Dict]:
        """Synchronous wrapper for get_complaints_by_email"""
        return self._run_async(self.get_complaints_by_email(email))
    


    async def generate_secure_link(self, customer_number:str, mobile_number:str) -> Optional[Dict]:
        """
        Generate a secure link with customer number and mobile number
        Args:
                customer_number: customer number from profile
                mobile_number: customer 12 digit mobile number (e.g 233558158591)
        Returns:
            Either a verification link string or a dictionary with error information
        """
        try:

            
            # Create and encrypt token
            token = self.serializer.dumps({
                'customer_number': customer_number,
                'mobile_number': mobile_number
            })
                        
            # Log the generated token and data
            logger.info(f"Generated token: {token}")
            logger.info(f"Token data: {customer_number} and {mobile_number}")
            
            # Create the verification link
            verification_link = f"{BACKEND_URL}/verify-pin?token={token}"
            
            logger.info(f"Secure link generated for customer {customer_number} and mobile {mobile_number}")
            return verification_link
            
        except Exception as e:
            # Create a detailed error response instead of raising the exception
            error_message = str(e)
            error_type = type(e).__name__
            
            logger.error(f"Error generating secure link: {error_type} - {error_message}")
            
        # Return a structured error response the agent can understand and handle
        return {
            "error": True,
            "message": f"Failed to generate secure link: {error_message}",
            "error_type": error_type,
            "data": f"data: {customer_number} and {mobile_number}"
        }
    
    def generate_secure_link_sync(self, customer_number:str, mobile_number:str) -> List[Dict]:
        """Synchronous wrapper for get_account_statement"""
        return self._run_async(self.generate_secure_link(customer_number, mobile_number))    


    async def send_bank_statement_email(self,customer_email:str, account_no:str, customer_name:str, credit_account_id:str, transactions:dict):
        """
       Send bank statement via email to customer.
             Args:
                 __arg1: Dictionary containing:
                        "customer_email": Request Valid email address from customer, not from profile
                        "account_no": Account number for reference
                        "customer_name": Customer's full name from customer info
                        "credit_account_id": Recipient account number
                        "transactions": {
                            "transaction1": {
                                "date": "2024-11-21",
                                "type": "Transfer In",
                                "debit": "0.00",
                                "credit": "2.00",
                                "balance": "2.00"
                            },
                            "transaction2": {
                            ...
                            }
                        }
                    }
        """
        return await self.email_service.send_bank_statement_email(customer_email, account_no, customer_name, credit_account_id, transactions)


    def send_bank_statement_email_sync(self, customer_email:str, account_no:str, customer_name:str, credit_account_id:str, transactions:dict) -> Dict:
        """Synchronous wrapper for send_bank_statement_email"""
        try:
            return self._run_async(self.send_bank_statement_email(customer_email, account_no, customer_name, credit_account_id, transactions))
        except Exception as e:
            logger.error(f"Synchronous wrapper error: {str(e)}")
            return {"error": f"Synchronous processing failed: {str(e)}"}      

    async def send_escalation_email(
        self,
        escalating_to: str,
        customer_email: str,
        customer_name: str,
        mobile_number: str,
        conversation_summary: str,
        customer_mood: str
    ) -> Dict[str, Any]:
        """
        Send a professional escalation email to bank supervisors.
        Args:
                - escalating_to (str): Email of supervisor/department
                - customer_email (str): Customer's email
                - customer_name (str): Customer's full name
                - mobile_number (str): customer mobile number with "+" and country code from customer profile
                - conversation_summary (str): Detailed issue description
                - customer_mood (str): Customer's emotional state
        
        Returns:
            Dict[str, Any]: Email sending status and details
        """
        return await self.email_service.send_escalation_email(escalating_to,
                customer_email,
                customer_name,
                mobile_number,
                conversation_summary,
                customer_mood)

    def send_escalation_email_sync(self,escalating_to: str,
        customer_email: str,
        customer_name: str,
        mobile_number: str,
        conversation_summary: str,
        customer_mood: str
    ) -> Dict[str, Any]:
        
        """Synchronous wrapper for send_bank_statement_email"""
        try:
            return self._run_async(self.send_escalation_email(escalating_to,
                customer_email,
                customer_name,
                mobile_number,
                conversation_summary,
                customer_mood))
        except Exception as e:
            logger.error(f"Synchronous wrapper error: {str(e)}")
            return {"error": f"Synchronous processing failed: {str(e)}"}   

    async def get_secure_account_statement(self, customer_number:str, customer_name:str, accountNo:str,startDate:str,endDate:str, Mobile_Number:str) -> Dict:
        """
        Args:
            customer_number: Customer identification number
            customer_name : Customer name from profile info
            accountNo: Account number
            startDate: Start date (format: YYYYMMDD)
            endDate: End date (format: YYYYMMDD)
            Mobile_Number: customer mobile number with "+" and country code from customer profile
        Returns:
            str: Account statement details if PIN verification successful
        """
        try:
            # 1. Get encrypted PIN from database
            db = next(self.db_session())
            pin_record = db.query(PinManagement).filter(
                PinManagement.customer_number == customer_number
            ).first()
            logger.info(f'pin record in db {pin_record}')
            if not pin_record:
                return "PIN not set for this customer. Please send verification link to the user first."
                
            # 2. Decrypt PIN using Fernet
            fernet = fernet = Fernet(get_fernet_key(os.environ["SECRET_KEY"]))  # Replace with your Fernet key
            decrypted_pin = fernet.decrypt(pin_record.encrypted_pin.encode()).decode()
            logger.info(f"the decrypted pin--------------- {decrypted_pin}")
            logger.info(f"the decrypted pin--------------- {type(decrypted_pin)}")
            # 3. Verify PIN with banking system
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                verify_response = await session.post(
                    f"{VERIFY_URL}",
                    json={
                        "customer_number": customer_number,
                        "secure_pin": decrypted_pin
                    }
                )
                
                if verify_response.status != 200:
                    return "Ask the user to try again."
                
                pin = await verify_response.json()
                logger.info(f"PIN verification response: {pin}")
                status = pin["status"]
                logger.info(f"pin status {status}" )   
                logger.info(f"pin status type {type(status)}" ) 
                if status is False:
                    db.delete(pin_record)
                    db.commit()
                    return "User entered a wrong pin, remind user to enter correct pin or else this account can be blocked!" 
                # 4. If PIN is verified, proceed to get account statement
                try:
                    # Validate dates
                    start_date = datetime.strptime(startDate, '%Y%m%d')
                    end_date = datetime.strptime(endDate, '%Y%m%d')
                    if end_date < start_date:
                        return "End date cannot be earlier than start date"
                        
                    # Get account statement
                    client = await self.get_client()
                    async with client as session:
                        response = await session.make_api_request(
                            "getAccountStatement",
                            params={
                                "accountNo": accountNo,
                                "startDate": startDate,
                                "endDate": endDate
                            }
                        )
                                            # Delete the PIN record
                        db.delete(pin_record)
                        db.commit()
                        logger.info(f"Deleted PIN record for customer_number {customer_number}")
                        
                        # After successful statement retrieval, before returning response:
                        try:
                            phone_number = Mobile_Number
                            if "+" in phone_number:
                                clean_number = phone_number
                                logger.info("Plus sign is present")
                            else:
                                clean_number = f"+{phone_number}"
                                logger.info("Plus sign is not present, plus added")
                            # Get the latest conversation for this customer
                            latest_conversation = db.query(Conversation)\
                                .filter(Conversation.phone_number == clean_number)\
                                .order_by(Conversation.created_at.desc())\
                                .first()

                            statement_request = BankStatementRequest(
                                customer_name= customer_name,
                                request_start_date=datetime.strptime(startDate, '%Y%m%d'),
                                request_end_date=datetime.strptime(endDate, '%Y%m%d'),
                                date=datetime.utcnow(),
                                conversation_id=latest_conversation.id if latest_conversation else None
                            )
                            db.add(statement_request)
                            db.commit()
                            logger.info(f"Statement request logged to database with ID: {statement_request.id}")
                            
                            return f"Statement: {response}"
                            
                        except Exception as db_error:
                            logger.error(f"Failed to log statement request: {str(db_error)}")
                            # Still return statement even if logging fails
                            return f"Statement: {response}"
                        
                except ValueError as e:
                    return f"Invalid date format. Use YYYYMMDD format. Error: {str(e)}"
                    
        except Exception as e:
            return f"An error occurred: {str(e)}"
        

    def get_secure_account_statement_sync(self, customer_number:str, customer_name:str, accountNo:str,startDate:str,endDate:str, Mobile_Number:str) -> Optional[Dict]:
        """Synchronous wrapper for get_account_statement"""
        return self._run_async(self.get_secure_account_statement(customer_number, customer_name, accountNo,startDate,endDate, Mobile_Number))   
    
    async def create_bank_booking(
        self,
        customer_name:str,
        email:str,
        service_type:str,
        service_details:dict,
        Mobile_Number:str,
        preferred_date:Optional[str]  # Accept a single dictionary argument
    ) -> str:
        """Create a new bank service request booking
        Args:
                customer_name: Name of the customer
                email: Email address of the customer
                service_type: Type of service (Account/Loan/Card/Transfer/Investment)
                service_details: JSON object containing service-specific details
                Mobile_Number: customer mobile number with "+" and country code from customer profile
                preferred_date: Optional preferred date for processing
        """
        try:
            phone_number = Mobile_Number
            if "+" in phone_number:
                clean_number = phone_number
                logger.info("Plus sign is present")
            else:
                clean_number = f"+{phone_number}"
                logger.info("Plus sign is not present, plus added")
            db = next(self.db_session())
            
            # Get latest conversation
            latest_conversation = db.query(Conversation)\
                .filter(Conversation.phone_number == clean_number)\
                .order_by(Conversation.created_at.desc())\
                .first()

            # Generate reference code
            reference_code = await generate_reference_code()
            
            # Set expiry date (e.g., 7 days from now)
            expiry_date = datetime.utcnow() + timedelta(days=7)
            
            bank_request = BankRequest(
                customer_name= customer_name,
                email= email,
                reference_code=reference_code,
                service_type= service_type,
                service_details= service_details,
                status=RequestStatus.PENDING,
                created_at=datetime.utcnow(),
                expiry_date=expiry_date,
                conversation_id=latest_conversation.id if latest_conversation else None
            )
            
            db.add(bank_request)
            db.commit()
            db.refresh(bank_request)
            
            return {
                "id": bank_request.id,
                "reference_code": bank_request.reference_code,
                "service_type": bank_request.service_type,
                "status": bank_request.status,
                "expiry_date": bank_request.expiry_date.isoformat(),
                "message": "Service request booked successfully. Please keep your reference code for tracking."
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating bank booking: {str(e)}")
            raise
        finally:
            db.close()
    
    def create_bank_booking_sync(self,customer_name:str,
        email:str,
        service_type:str,
        service_details:dict,
        Mobile_Number:str,
        preferred_date:Optional[str] ) -> Dict:
        """Synchronous wrapper for create_complaint"""
        return self._run_async(self.create_bank_booking(customer_name,email, service_type, service_details, Mobile_Number,preferred_date))
    
    
    async def get_bank_booking(
        self,
        reference_code:str  # Accept a single dictionary argument
    ) -> List[Dict]:
        """Get complaints by user email 
        Args:
                reference_code: reference code of that booking
        """
        try:
            db = next(self.db_session())
            booking = db.query(BankRequest).filter(BankRequest.reference_code == reference_code).first()
            
            if not booking:
                return {"error": "Booking not found"}
                
            return {
                "id": booking.id,
                "customer_name": booking.customer_name,
                "email": booking.email,
                "reference_code": booking.reference_code,
                "service_type": booking.service_type,
                "service_details": booking.service_details,
                "status": booking.status,
                "created_at": booking.created_at
            }
            
        except Exception as e:
            logger.error(f"Error retrieving bank booking: {str(e)}")
            raise
        finally:
            db.close()

    def get_bank_booking_sync(self, reference_code:str) -> Dict:
        """Synchronous wrapper for create_complaint"""
        return self._run_async(self.get_bank_booking(reference_code))
    

    async def verify_account_details(self, customer_number: str) -> str:
        """verify customer account creation details using their customer number and return their account number to them
        args:
            customer_number: Customer number given to you
        returns:
            str: Formatted string containing account details
        """
        try:
            number = customer_number['customer_number']
            client = await self.get_client()
            
            async with client as session:
                response = await session.make_api_request(
                    "getGtiAccountDetails",
                    params={"customerNumber": number},
                    method="GET"
                ) 
                account_data = response
                accounts = account_data["body"]
                formatted_response = f"Found {len(accounts)} account(s) for customer {customer_number}:\n\n"
                
                for account in accounts:
                    formatted_response += (
                        f"Account Number: {account.get('accountNo', 'N/A')}\n"
                        f"Account Name: {account.get('accountName', 'N/A')}\n"
                        f"Account Type: {account.get('accountCategory', 'N/A')}\n"
                        f"Opening Date: {account.get('openingDate', 'N/A')}\n"
                        f"Account Officer: {account.get('accountOfficer', 'N/A')}\n"
                        f"Status: Active\n"
                        "------------------------\n"
                    )
                return formatted_response          
        except Exception as e:
            logger.error(f"Error fetching account details: {str(e)}")
            return f"Failed to get account details: {str(e)}"
        
    def verify_account_details_sync(self, customer_number: str) -> str:
        """Synchronous wrapper for get_account_details"""
        return self._run_async(self.verify_account_details(customer_number))


    async def generate_create_account_link(self, *args, **kwargs):
        """
        Generate a secure link for customer to create an account, this function does not accept any parameter
        """
        try:


            verification_link = f"{BACKEND_URL}/create-account"
            logger.info(f" verification link {verification_link}")
            logger.info(f"Secure link generated for customer {verification_link}")
            return verification_link
            
        except Exception as e:
            logger.error(f"Error generating secure link for customer {verification_link}: {str(e)}")
            raise e
        
    def generate_create_account_link_sync(self, *args, **kwargs):
        """Synchronous wrapper for get_account_statement"""
        return self._run_async(self.generate_create_account_link(*args, **kwargs))     
    

    async def create_appointment(
        self, customer_name: str, email: str, phone_number: str,
                               appointment_type: str, preferred_date: str, preferred_time: str,
                               location: str, Mobile_Number: str, additional_notes: Optional[str] = None)  -> Dict:
        """Create a new appointment booking
        Args:
                customer_name: Name of the customer
                email: Email address of the customer
                phone_number: Phone number with country code
                appointment_type: Type of appointment (faccount_opening,loan_consultation,investment_advisory,general_inquiry,complaint_resolution)
                preferred_date: Preferred date (YYYY-MM-DD)
                preferred_time: Preferred time (HH:MM)
                location: Location for the appointment
                additional_notes: Optional additional notes
                Mobile_Number: customer mobile number with "+" and country code from customer profile
        """
        try:
            phone_number = Mobile_Number
            if "+" in phone_number:
                clean_number = phone_number
                logger.info("Plus sign is present")
            else:
                clean_number = f"+{phone_number}"
                logger.info("Plus sign is not present, plus added")


            db = next(self.db_session())
            
            # Get latest conversation
            latest_conversation = db.query(Conversation)\
                .filter(Conversation.phone_number == clean_number)\
                .order_by(Conversation.created_at.desc())\
                .first()
            
            # Generate reference code
            reference_code = await generate_reference_code()
            
            # Parse the datetime
            preferred_date = datetime.strptime(preferred_date, "%Y-%m-%d")
            
            appointment = Appointment(
                customer_name=customer_name,
                email= email,
                phone_number= clean_number,
                appointment_type= appointment_type,
                preferred_date=preferred_date,
                preferred_time= preferred_time,
                location= location,
                additional_notes= additional_notes,
                status=AppointmentStatus.PENDING,
                reference_code=reference_code,
                created_at=datetime.utcnow(),
                conversation_id=latest_conversation.id if latest_conversation else None,
                confirmation_sent=False
            )
            
            db.add(appointment)
            db.commit()
            db.refresh(appointment)
            
            # Send confirmation message via WhatsApp
            try:
                confirmation_message = (
                    f"Your appointment has been scheduled!\n"
                    f"Reference Code: {appointment.reference_code}\n"
                    f"Date: {appointment.preferred_date.strftime('%Y-%m-%d')}\n"
                    f"Time: {appointment.preferred_time}\n"
                    f"Location: {appointment.location}\n\n"
                    f"Please keep this reference code for future updates."
                )
                
                
                
                appointment.confirmation_sent = True
                db.commit()
                
            except Exception as e:
                logger.error(f"Failed to send confirmation message: {str(e)}")
            
            return {
                "id": appointment.id,
                "reference_code": appointment.reference_code,
                "appointment_type": appointment.appointment_type,
                "preferred_date": appointment.preferred_date.strftime("%Y-%m-%d"),
                "preferred_time": appointment.preferred_time,
                "status": appointment.status,
                "message": confirmation_message
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating appointment: {str(e)}")
            raise
        finally:
            db.close()

    def create_appointment_sync(self, customer_name: str, email: str, phone_number: str,
                              appointment_type: str, preferred_date: str, preferred_time: str,
                              location: str, Mobile_Number: str, additional_notes: Optional[str] = None) -> Dict:
        """Synchronous wrapper for create_complaint"""
        return self._run_async(self.create_appointment(customer_name, email, phone_number, appointment_type, 
            preferred_date, preferred_time, location, Mobile_Number, additional_notes, ))


    async def get_appointment(
        self,
        reference_code: str) -> List[Dict]:
        """Get complaints by user email 
                reference_code: reference code of that booking
        Returns:
            Dictionary containing the appointment details or None if not found
        """
        try:

            db = next(self.db_session())
            
            appointment = db.query(Appointment).filter(
                Appointment.reference_code == reference_code
            ).first()
            
            if not appointment:
                return None
            
            return {
                "id": appointment.id,
                "reference_code": appointment.reference_code,
                "customer_name": appointment.customer_name,
                "email": appointment.email,
                "phone_number": appointment.phone_number,
                "appointment_type": appointment.appointment_type,
                "preferred_date": appointment.preferred_date.strftime("%Y-%m-%d"),
                "preferred_time": appointment.preferred_time,
                "location": appointment.location,
                "status": appointment.status,
                "created_at": appointment.created_at,
                "additional_notes": appointment.additional_notes,
                "assigned_agent": appointment.assigned_agent,
                "cancellation_reason": appointment.cancellation_reason,
                "rejection_reason": appointment.rejection_reason,
                "reason_details": appointment.reason_details,
                "suggested_alternative_date": appointment.suggested_alternative_date.strftime("%Y-%m-%d") if appointment.suggested_alternative_date else None,
                "suggested_alternative_time": appointment.suggested_alternative_time
            }
            
        except Exception as e:
            logger.error(f"Error retrieving appointment: {str(e)}")
            raise

        finally:
            db.close()

    def get_appointment_sync(self, reference_code:str) -> List[Dict]:
        """Synchronous wrapper for create_complaint"""
        return self._run_async(self.get_appointment(reference_code))
    



    async def generate_otp(self,mobile_number:str) -> Dict[str, str]:
        """
        Generate a 6-digit OTP code for user via sms and store it in database before creating an account for new customers
        Args:
                mobile_number: Customer's mobile number with country code (e.g., +233559158793)
        Returns:
            Dictionary with unique identifier for the OTP or error message
        """
        try:
            # Validate phone number format
            if not mobile_number.startswith('+'):
                return {
                    "error": "Invalid phone number format. Please include country code starting with '+' (e.g., +233559158793)"
                }

            db = next(self.db_session())
            
            # Clear any existing unexpired OTPs for this number
            existing_otps = db.query(OTPManagement).filter(
                OTPManagement.identifier.like(f"{mobile_number}%"),
                OTPManagement.expires_at > datetime.utcnow(),
                OTPManagement.is_used == False
            ).all()
            
            for otp in existing_otps:
                db.delete(otp)
            
            # Generate 6-digit OTP
            otp = ''.join(random.choices(string.digits, k=6))
            
            # Generate unique identifier (include phone number for tracking)
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            identifier = f"{mobile_number}_{timestamp}"
            
            # Create OTP record with 5-minute expiration
            otp_record = OTPManagement(
                identifier=identifier,
                otp_code=otp,
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            )
            
            db.add(otp_record)
            db.commit()

            # Send OTP via WhatsApp
            try:
                client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                client.messages.create(
                    body=f'Your OTP code is: {otp}. Valid for 5 minutes.',
                    from_=f'{TWILIO_NUM}',
                    to=f'{mobile_number}'
                )
                logger.info(f"OTP sent to {mobile_number}")
            except Exception as e:
                logger.error(f"Failed to send OTP: {str(e)}")
                # Cleanup the OTP record if message fails
                db.delete(otp_record)
                db.commit()
                return {"error": "Failed to send OTP message. Please try again."}
                        
            return {
                "identifier": identifier,
                "message": "OTP sent successfully. Please check your messages."
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error generating OTP: {str(e)}")
            return {"error": f"Failed to generate OTP: {str(e)}"}
        finally:
            db.close()

    def generate_otp_sync(self, mobile_number:str) -> Dict:
        """Synchronous wrapper for get_account_statement"""
        return self._run_async(self.generate_otp(mobile_number)) 
    

    async def verify_otp_and_generate_create_account_link(self, identifier:str, otp_code:str) -> str:
        """
        Verify OTP and generate account creation link if valid
        Args:
                identifier: OTP identifier
                otp_code: OTP code provided by user
        Returns:
            Account creation link if OTP is valid, otherwise error message
        """
        try:
            db = next(self.db_session())
            
            # Get OTP record
            otp_record = db.query(OTPManagement).filter(
                OTPManagement.identifier == identifier
            ).first()
            
            if not otp_record:
                return "Invalid OTP identifier. Please request a new OTP."
            
            # Check if OTP is expired
            if datetime.utcnow() > otp_record.expires_at:
                db.delete(otp_record)  # Clean up expired OTP
                db.commit()
                return "OTP has expired. Please request a new OTP."

            if otp_record.is_used:
                return "This OTP has already been used. Please request a new OTP."
            
            if otp_record.otp_code != otp_code:
                return "Incorrect OTP code. Please try again."
            
            # Mark OTP as used
            otp_record.is_used = True
            db.commit()
            verification_link = f"{BACKEND_URL}/create-account"
            
            db.delete(otp_record)
            db.commit()
            
            return verification_link
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error verifying OTP: {str(e)}")
            return f"Error verifying OTP: {str(e)}"
        finally:
            db.close()


    def verify_otp_and_generate_create_account_link_sync(self, identifier:str, otp_code:str) -> Dict:
        """Synchronous wrapper for get_account_statement"""
        return self._run_async(self.verify_otp_and_generate_create_account_link(identifier, otp_code)) 


    async def verify_credit_account(self, credit_account_number:str) -> Dict[str, str]:
        """verify credit account provided by the user if it really exist before making transfer
        Args:
                credit_account_number: Credit account number provided by the user
        """             
        try:

            # number = credit_account_number['credit_account_number']
            # logger.info(f"credit account number{number}")
            logger.info(f"credit_account_number{credit_account_number}")
            logger.info(f"credit_account_number type {type(credit_account_number)}")
            client = await self.get_client()
            # Apply the same SSL context to this client if needed
            async with client as session:
                response = await session.make_api_request(
                "getGtiAccountDetails",
                params={"accountNumber": credit_account_number},
                method="GET"
                ) 
                account_data = response

                accounts = account_data["body"]
                formatted_response = f"Found {len(accounts)} account(s) for customer {credit_account_number}:\n\n"
                
                for account in accounts:
                    formatted_response += (
                        f"Account Number: {account.get('accountNo', 'N/A')}\n"
                        f"Account Name: {account.get('accountName', 'N/A')}\n"
                        f"Account Type: {account.get('accountCategory', 'N/A')}\n"
                        f"Opening Date: {account.get('openingDate', 'N/A')}\n"
                        f"Account Officer: {account.get('accountOfficer', 'N/A')}\n"
                        f"Status: Active\n"
                        "------------------------\n"
                    )

                return formatted_response
                
        except Exception as e:
            logger.error(f"Error fetching account details: {str(e)}")
            return f"Failed to get account details: {str(e)}"
        
    def verify_credit_account_sync(self,credit_account_number:str) -> Dict:
        """Synchronous wrapper for get_account_details"""
        return self._run_async(self.verify_credit_account(credit_account_number))
    

    async def send_whatsapp_audio_message(self,phone_number:str, text_response:str) -> Dict[str, str]:
        """
        respond to user with audio
        Args:
                phone_number: Recipient's from info
                text_response: Text to convert to speech
        Returns: 
             audio only, don't add any extra text to the tool mesage, the only text should "play audio"...Avoid adding text like 'Please check your WhatsApp'
        """
        try:
            if "+" in phone_number:
                clean_number = phone_number
                logger.info("Plus sign is present")
            else:
                clean_number = f"+{phone_number}"
                logger.info("Plus sign is not present, plus added")

            # Generate S3 URL for the audio
            s3_audio_url = await text_to_whatsapp_audio(text_response)
            
            # Initialize Twilio client
            client = Client(
                os.getenv("TWILIO_ACCOUNT_SID"), 
                os.getenv("TWILIO_AUTH_TOKEN")
            )
            logger.info(f"Sending audio to {clean_number}")
            logger.info(f"The twilio number {TWILIO_NUMBER}")
            # Send WhatsApp message with audio
            message = client.messages.create(
                media_url=[s3_audio_url],
                from_=f"whatsapp:{TWILIO_NUMBER}",  # Your Twilio WhatsApp number
                to=f"whatsapp:{clean_number}"
            )
            
            return f"audio sent to user"
        
        except Exception as e:
            logging.error(f"Error sending WhatsApp audio message: {str(e)}")
            raise

    def send_whatsapp_audio_message_sync(self, text_response:str , phone_number:str) -> Dict:
        """Synchronous wrapper for get_account_details"""
        return self._run_async(self.send_whatsapp_audio_message(phone_number, text_response))

    
    
    # async def translate_to_amharic(self, __arg1: Dict[str, str]) -> str:
    #     """
    #     Translate English text to Amharic and return the translation
    #     Args:
    #         __arg1: Dictionary containing:
    #             text: Text to translate to Amharic
    #     Returns:
    #         str: Translated Amharic text
    #     """
    #     try:
    #         text = __arg1['text']
    #         translator = Translator()
    #         translation = translator.translate(text, dest='am')
    #         return translation
    #     except Exception as e:
    #         logger.error(f"Translation failed: {str(e)}")
    #         return f"Translation error: {str(e)}"

    # async def translate_respone_to_am_om(self, __arg1: Dict[str, str]) -> Dict[str, str]:
    #     """
    #     Am tool to help you translate your english response to amharic and afan Oromo.

    #     Args:
    #         __arg1: Dictionary containing:
    #             english_response: The text to be translated
    #             target_language: The language code to translate to (e.g., 'am' for amharic, 'om' for afan oromo)

    #     Returns:
    #         Optional[str]: Translated text, or None if translation fails
    #     """
    #     try:
    #         target_language = __arg1['target_language']
    #         text = __arg1['english_response']
    #         # Create translator instance
    #         translator = Translator()
    #         logger.info(f"Translating text to {target_language}")
    #         # Translate the text
    #         translation = await translator.translate(text, dest=target_language)

    #         return translation.text
    #     except Exception as e:
    #         logging.error(f"Translation error: {str(e)}")
    #         return None
        

    async def translate_respone_to_am_om(self, english_response:str ,target_language:str ) -> str:
        """
        Am tool to help you translate your english response to amharic and afan Oromo.

        Args:
                english_response: The text to be translated
                target_language: The language to translate to (e.g., 'amharic' or 'afan oromo')

        Returns:
            Optional[str]: Translated text, or None if translation fails
        """
        try:
            
            # target_language = __arg1['target_language']
            # text = __arg1['english_response']
            logger.info(f"translatin to {target_language}")
            # Create translator instance
            messages = [
                {
                    "role": "system",
                    "content": f"""You are an expert translator specializing translating from the given text to {target_language} .

            Your task is to translate text from English to the target language in a way that:
            1. Preserves the original meaning and context
            2. Sounds natural and conversational to native speakers

            JUST TRANSLATE!"""
                },
                {
                    "role": "user",
                    "content": english_response
                }
            ]
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.2,
                max_retries=2,
                # other params...
            )
            ai_msg = llm.invoke(messages)
            translation = ai_msg.content
            return translation

        except Exception as e:
            logging.error(f"Translation error: {str(e)}")
            return e

    def translate_respone_to_am_om_sync(self,english_response, target_language) -> str:
        """Synchronous wrapper for translate_to_amharic"""
        return self._run_async(self.translate_respone_to_am_om(english_response,target_language))
    
    # async def translate_respone_to_am_om(self, args: Dict[str, str]) -> str:
    #     """
    #     Am tool to help you translate your english response to amharic and afan Oromo.
    #     """
    #     try:
    #         target_language = args['target_language']
    #         text = args['english_response']
    #         # Create translator instance
    #         translator = Translator()
    #         logger.info(f"Translating text to {target_language}")
    #         # Translate the text
    #         translation = await translator.translate(text, dest=target_language)
            
    #         return translation.text
    #     except Exception as e:
    #         logger.error(f"Translation error: {e}")
    #         raise e

    # def translate_respone_to_am_om_sync(self, **kwargs) -> str:
    #     """Synchronous wrapper for translate_to_amharic"""
    #     # Convert keyword arguments to dictionary format expected by the async function
    #     args = {
    #         'english_response': kwargs['english_response'],
    #         'target_language': kwargs['target_language']
    #     }
    #     return self._run_async(self.translate_respone_to_am_om(args))
    
    def create_tools(self) -> List[Tool]:
        """Create and return a list of banking tools"""
        return [
            StructuredTool(
                name="generate_secure_link",
                description=self.generate_secure_link.__doc__,
                func=self.generate_secure_link_sync,  # Or async version with appropriate wrapper
                args_schema=SecureLinkInput,
                return_direct=False
            ),
            StructuredTool(
                name="translate_respone_to_am_om",
                description="Translate English text to Amharic (am) or Afan Oromo (om)",
                func=self.translate_respone_to_am_om_sync,  # Or async version with appropriate wrapper
                args_schema=TranslationInput,
                return_direct=False
            ),
           StructuredTool(
                name="send_whatsapp_audio_message",
                description=self.send_whatsapp_audio_message.__doc__,
                func=self.send_whatsapp_audio_message_sync,  # Or async version with appropriate wrapper
                args_schema= SendAudioInput,
                return_direct=False
            ),

           StructuredTool(
                name="verify_credit_account",
                description=self.verify_credit_account.__doc__,
                func=self.verify_credit_account_sync,  # Or async version with appropriate wrapper
                args_schema= VerifyCreditAccount,
                return_direct=False
            ),


            StructuredTool(
                name="create_appointment",
                description=self.create_appointment.__doc__,
                func=self.create_appointment_sync,  # Or async version with appropriate wrapper
                args_schema=AppointmentInput,
                return_direct=False
            ),
            StructuredTool(
                name="create_complaint",
                description=self.create_complaint.__doc__,
                func=self.create_complaint_sync,  # Or async version with appropriate wrapper
                args_schema=ComplaintInput,
                return_direct=False
            ),
            StructuredTool(
                name="get_appointment",
                description=self.get_appointment.__doc__,
                func=self.get_appointment_sync,  # Or async version with appropriate wrapper
                args_schema=GetAppointmentInput,
                return_direct=False
            ),

            # Tool(
            #     name="send_bank_statement_email", 
            #     func=self.send_bank_statement_email_sync, 
            #     description=self.send_bank_statement_email.__doc__),
            StructuredTool(
                name="send_bank_statement_email",
                description=self.send_bank_statement_email.__doc__,
                func=self.send_bank_statement_email_sync,  # Or async version with appropriate wrapper
                args_schema=BankStatementInput,
                return_direct=False
            ),
            StructuredTool(
                name="send_escalation_email",
                description=self.send_escalation_email.__doc__,
                func=self.send_escalation_email_sync,  # Or async version with appropriate wrapper
                args_schema=EscalationEmailInput,
                return_direct=False
            ),
            StructuredTool(
                name="get_secure_account_statement",
                description=self.get_secure_account_statement.__doc__,
                func=self.get_secure_account_statement_sync,  # Or async version with appropriate wrapper
                args_schema=AccountStatementInput,
                return_direct=False
            ),
            # Tool(
            #     name="generate_create_account_link",
            #     func=self.generate_create_account_link_sync,
            #     description=self.generate_create_account_link.__doc__
            # ),
            StructuredTool(
                name="generate_otp",
                description=self.generate_otp.__doc__,
                func=self.generate_otp_sync,  # Or async version with appropriate wrapper
                args_schema=GenerateOtpInput,
                return_direct=False
            ),
            StructuredTool(
                name="verify_otp_and_generate_create_account_link",
                description=self.verify_otp_and_generate_create_account_link.__doc__,
                func=self.verify_otp_and_generate_create_account_link_sync,  # Or async version with appropriate wrapper
                args_schema=GenerateCreateAccountInput,
                return_direct=False
            ),
            # StructuredTool(
            #     name="get_secure_account_statement",
            #     description=self.get_secure_account_statement.__doc__,
            #     func=self.get_secure_account_statement_sync,
            #     args_schema = GetStatementInputSchema

            # ),
            StructuredTool(
                name="get_complaints_by_email",
                description=self.get_complaints_by_email.__doc__,
                func=self.get_complaints_by_email_sync,  # Or async version with appropriate wrapper
                args_schema=GetComplaintsInput,
                return_direct=False
            ),
            StructuredTool(
                name="update_complaint",
                description=self.update_complaint.__doc__,
                func=self.update_complaint_sync,  # Or async version with appropriate wrapper
                args_schema=UpdateComplaintInput,
                return_direct=False
            ),
    
            StructuredTool(
                name="get_account_balance",
                description=self.get_account_balance.__doc__,
                func=self.get_account_balance_sync,  # Or async version with appropriate wrapper
                args_schema=AccountBalanceInput,
                return_direct=False
            ),
            StructuredTool(
                name="create_bank_booking",
                description=self.create_bank_booking.__doc__,
                func=self.create_bank_booking_sync,  # Or async version with appropriate wrapper
                args_schema= BankBookingInput,
                return_direct=False
            ),
            StructuredTool(
                name="get_bank_booking",
                description=self.get_bank_booking.__doc__,
                func=self.get_bank_booking_sync,  # Or async version with appropriate wrapper
                args_schema= GetBankBookingInput,
                return_direct=False
            ),

            StructuredTool(
                name="make_transfer",
                description=self.make_transfer.__doc__,
                func=self.make_transfer_sync,  # Or async version with appropriate wrapper
                args_schema=TransferInput,
                return_direct=False
            ),
            Tool(
                name="get_exchange_rates",
                func=self.get_exchange_rates_sync,
                description="Get current exchange rates for all currencies. No parameters required."
            ),
        ]

    def create_small_tools(self) -> List[Tool]:
        """Create and return a list of banking tools"""
        return [
            Tool(
                name="make_transfer",
                func=self.make_transfer_sync,
                description=self.make_transfer.__doc__
            ),
            Tool(
                name="get_account_statement",
                func=self.get_account_statement,
                description=self.get_account_statement.__doc__),
            Tool(
                name="get_account_balance",
                func=self.get_account_balance,
                description=self.get_account_balance.__doc__
            )
        ]
