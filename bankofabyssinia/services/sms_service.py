from twilio.rest import Client
import os
import logging

logger = logging.getLogger(__name__)

class SMSService:
    def __init__(self):
        self.client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        self.twilio_number = os.getenv('TWILIO_NUMBER')
    
    def send_transfer_notification(self, phone_number: str, amount: float, 
                                 currency: str, account: str, description: str):
        try:
            message = (
                f"Credit Alert\n"
                f"Amount: {amount} {currency}\n"
                f"Account: {account}\n"
                f"Description: {description}"
            )
            
            self.client.messages.create(
                body=message,
                from_=self.twilio_number,
                to=f"whatsapp:{phone_number}"
            )
            return True
        except Exception as e:
            logger.error(f"SMS notification failed: {str(e)}")
            return False
        

import aiohttp
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SMSService:
    def __init__(self):
        self.API_KEY = "eFZIUWNNQ2pEdUJ5ZnhVbnVyeGo"
        self.BASE_URL = "https://sms.arkesel.com/sms/api"
        self.SENDER_ID = "GTIBANK"

    async def send_transfer_alert(self, phone: str, amount: float, account: str) -> bool:
        try:
            message = f"Credit Alert\nAmount: {amount}STN \nAccount: {account}"
            params = {
                "action": "send-sms",
                "api_key": self.API_KEY,
                "to": phone.replace("+", ""),
                "from": self.SENDER_ID,
                "sms": message
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params) as response:
                    if response.status == 200:
                        logger.info(f"SMS sent to {phone}")
                        return True
                    logger.error(f"SMS failed: {await response.text()}")
                    return False
                    
        except Exception as e:
            logger.error(f"SMS error: {str(e)}")
            return False