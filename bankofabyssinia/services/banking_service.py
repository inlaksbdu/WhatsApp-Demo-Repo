from typing import Any, Dict
from httpx import AsyncClient
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from loguru import logger

from services.profile_service import ProfileService

profile_service = ProfileService()


class BankingService:
    def __init__(self, client: AsyncClient | None = None):
        BASE_URL = "http://18.198.5.151:9095/gticontainer/api/v1.0.0/party"
        HEADERS = {"companyId": "GB0010001", "Content-Type": "application/json"}
        self.client = client or AsyncClient(base_url=BASE_URL, headers=HEADERS)

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def _make_request(self, method: str, endpoint: str, **kwargs):
        response = await self.client.request(method, endpoint, **kwargs)
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error making request: {str(e)}")
            raise Exception(f"Error making request: {str(e)}")

    def _generate_mnemonic(self, first_name: str, surname: str, dob: str) -> str:
        """Generate mnemonic from name and date of birth"""
        name_part = (first_name[:2] + surname[:2]).upper()
        return f"{name_part}{dob}"

    def _format_names(
        self, first_name: str, surname: str, other_name: str = ""
    ) -> dict:
        """Format various name fields"""
        if other_name:
            full_name = f"{first_name} {other_name} {surname}"
        else:
            full_name = f"{first_name} {surname}"

        short_name = f"{first_name} {surname}"

        return {
            "fullName": full_name.strip(),
            "fullName2": "",
            "shortName": short_name.strip(),
        }

    async def create_customer_and_account(
        self,
        first_name: str,
        surname: str,
        dob: str,
        email: str,
        mobile_number_1: str,
        mobile_number_2: str | None = None,
        other_name: str = "",
    ) -> Dict[str, Any]:
        try:
            mobile_number_2 = mobile_number_2 or mobile_number_1

            customer_response = await self.create_customer(
                first_name,
                surname,
                dob,
                email,
                mobile_number_1,
                mobile_number_2,
                other_name,
            )
            customer_id = customer_response["header"]["id"]
            account_response = await self.create_account(customer_id)

            logger.success(
                f"Customer and account created successfully. Account number: {account_response['header']['id']}"
            )
            return account_response
        except Exception as e:
            logger.error(f"Account creation failed: {str(e)}")
            raise e

    async def create_customer(
        self,
        first_name: str,
        surname: str,
        dob: str,
        email: str,
        mobile_number_1: str,
        mobile_number_2: str | None = None,
        other_name: str = "",
    ) -> Dict[str, Any]:
        customer_data = {
            "firstName": first_name,
            "surName": surname,
            "dateofBirth": dob.replace("-", ""),
            "customerEmail": email,
            "otherName": other_name,
        }
        try:
            names = self._format_names(
                first_name, surname=surname, other_name=other_name
            )

            mnemonic = self._generate_mnemonic(
                first_name=first_name, surname=surname, dob=dob.replace("-", "")
            )
            mobile_number_2 = mobile_number_2 or mobile_number_1

            data = {
                **customer_data,
                **names,
                "mnemonic": mnemonic,
                "accountOfficer": "2",
                "sector": "1000",
                "industry": "1001",
                "target": "10",
                "customerStatus": "12",
                "nationality": "ST",
                "residence": "ST",
                "dateofIncorp": "",
                "language": "1",
                "mobileNumber": mobile_number_1.replace("+", ""),
                "mobileNumber2": mobile_number_2.replace("+", ""),
                "resident": "Y",
                "street": "SAO TOME",
                "extensions": {},
            }

            customer_response = await self._make_request(
                method="POST", endpoint="createNewCustomer", json={"body": data}
            )
            return customer_response

        except Exception as e:
            logger.error(f"Account creation failed: {str(e)}")
            raise e

    async def create_account(self, customer_id: str) -> Dict[str, Any]:
        account_id = f"{customer_id}20"  # Category 6220
        try:
            account_response = await self._make_request(
                method="POST",
                endpoint=f"createGtiNewAccountCreation/{account_id}",
                json={
                    "body": {
                        "customerNo": customer_id,
                        "category": "6220",
                        "currency": "STN",
                        "accountName1": "John Doe",
                        "accountShortName": "John Doe",
                        "accountOfficer": "2",
                        "openingDate": "",
                        "channel": "",
                        "postingRestrict": "",
                        "extensions": {},
                    }
                },
            )
            return account_response
        except Exception as e:
            logger.error(f"Account creation failed: {str(e)}")
            raise e

    async def make_transfer(
        self,
        credit_account_id: str,
        debit_account_id: str,
        debit_amount: str,
        payment_details: str,
    ) -> str:
        data = {
            "creditAccountId": credit_account_id,
            "debitAccountId": debit_account_id,
            "debitAmount": debit_amount,
            "debitCurrency": "STN",
            "transactionType": "AC",
            "debitValueDate": "",
            "creditCurrencyId": "STN",
            "creditAmount": "",
            "paymentDetails": payment_details,
            "channel": "",
            "eternalRef": "",
            "override": "",
            "recordStatus": "",
            "inputterId": "",
            "dateAndTime": "",
            "authoriser": "",
            "companyCode": "",
            "extensions": {},
        }
        return await self._make_request(
            method="POST", endpoint="creategtiFundsTransfer", json={"body": data}
        )
