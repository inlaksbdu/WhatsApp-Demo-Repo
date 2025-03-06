import asyncio
from typing import Coroutine, Dict, List, Optional
from loguru import logger
from tools.tools import BankingTools

class AccountLinkGenerator:
    def __init__(self):
        self.banking = BankingTools()

    def _run_async(self, coro: Coroutine):
        """Helper to run coroutines in sync context"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

    async def generate_create_account_link(self) -> Optional[Dict]:
        """
        Generate a secure link for customer to create an account
        """
        try:
            # Create the verification link
            verification_link = f"https://5c47-2c0f-2a80-7ac-1210-7186-84f1-685a-fba1.ngrok-free.app/create-account"
            logger.info(f"verification link {verification_link}")
            logger.info(f"Secure link generated for customer {verification_link}")
            return verification_link

        except Exception as e:
            logger.error(f"Error generating secure link: {str(e)}")
            raise e

    def generate_create_account_link_sync(self):
        """Synchronous wrapper for generate_create_account_link"""
        return self._run_async(self.generate_create_account_link())

if __name__ == "__main__":
    generator = AccountLinkGenerator()
    result = generator.generate_create_account_link_sync()
    print(f"Generated link: {result}")