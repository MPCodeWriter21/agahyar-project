"""SMS.ir API client for sending OTP messages.

Synchronous adapter around the sms.ir REST API v1, intended for use
in Django views.  Docs: https://sms.ir/rest-api/
"""

import logging
from http import HTTPStatus

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.sms.ir/v1/"


class SMSAPIError(Exception):
    """Raised when an SMS.ir API request fails."""

    def __init__(self, message: str, status_code: int = -1) -> None:
        super().__init__(message)
        self.status_code = status_code


class SMSClient:
    """Synchronous client for the sms.ir REST API."""

    def __init__(self) -> None:
        self._api_key: str = getattr(settings, "SMS_IR_API_KEY", "")
        self._otp_template_id: int = getattr(settings, "SMS_IR_OTP_TEMPLATE_ID", 0)
        self._disabled: bool = getattr(settings, "DISABLE_SMS", False)

    def _post(self, endpoint: str, data: dict) -> dict:
        """Send a POST request to the sms.ir API.

        :param endpoint: API path segment (e.g. ``send/verify``).
        :param data: JSON payload.
        :returns: Parsed JSON response.
        :raises SMSAPIError: On non-200 responses or network errors.
        """
        url = f"{BASE_URL}{endpoint}"
        headers = {
            "X-Api-Key": self._api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        try:
            response = httpx.post(url, json=data, headers=headers, timeout=15)
        except httpx.HTTPError as exc:
            logger.error("SMS API network error: %s", exc)
            raise SMSAPIError(f"Network error: {exc}") from exc

        if response.status_code != HTTPStatus.OK:
            logger.error("SMS API error %s: %s", response.status_code, response.text)
            raise SMSAPIError(
                message=f"API returned {response.status_code}",
                status_code=response.status_code,
            )

        return response.json()

    def send_otp(self, mobile_number: str, otp_code: str) -> dict:
        """Send an OTP code via a pre-configured template.

        :param mobile_number: 11-digit Iranian mobile number.
        :param otp_code: The plain-text OTP to embed in the message.
        :returns: The parsed API response data.
        :raises SMSAPIError: If the API call fails.
        """
        if self._disabled:
            logger.info(
                "SMS disabled -- OTP %s not sent to %s", otp_code, mobile_number
            )
            return {
                "status": 1,
                "message": "SMS disabled",
                "data": {"messageId": 0, "cost": 0},
            }

        data = {
            "mobile": mobile_number,
            "templateId": self._otp_template_id,
            "parameters": [{"Name": "code", "Value": otp_code}],
        }
        return self._post("send/verify", data)


def get_sms_client() -> SMSClient:
    """Return a configured SMSClient instance."""
    return SMSClient()
