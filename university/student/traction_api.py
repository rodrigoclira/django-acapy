"""
TractionAPI - A Python library for connecting to Traction services

This library provides methods to authenticate and interact with
the Traction API for various operations including customer management,
opportunity tracking, and reporting.
"""

import requests
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TractionAPIError(Exception):
    """Custom exception for Traction API errors"""

    def __init__(self, message: str, status_code: int = 0, data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.data = data or {}


class TractionAPI:
    """Client for interacting with the Traction API"""

    def __init__(
        self,
        api_key: str,
        tenant_id: str = None,
        base_url: str = "https://api.traction.io/v1",
        timeout: int = 30,
    ):
        """
        Initialize a new TractionAPI client

        Args:
            api_key: API key for authentication
            base_url: Base URL for the Traction API (optional)
            timeout: Request timeout in seconds (optional)
        """
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.tenant_id = tenant_id
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def authenticate(self) -> str:
        """
        Authenticate with the Traction API and return the token

        Returns:
            str: Authentication token
        """
        url = f"{self.base_url}/multitenancy/tenant/{self.tenant_id}/token"
        response = requests.post(url, json={"api_key": self.api_key})
        if response.status_code != 200:
            logger.error(f"Authentication failed: {response.text}")
            raise TractionAPIError(
                message="Authentication failed",
                status_code=response.status_code,
                data=response.json(),
            )
        data = response.json()
        token = data.get("token")
        if not token:
            logger.error("Token not found in response")
            raise TractionAPIError(
                message="Token not found in response",
                status_code=response.status_code,
                data=data,
            )
        logger.info("Authentication successful")
        return token

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        """
        Make an HTTP request to the Traction API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request data (optional)
            params: Query parameters (optional)

        Returns:
            Response data as dictionary

        Raises:
            TractionAPIError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data if data else None,
                params=params,
                timeout=self.timeout,
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            error_data = None
            try:
                error_data = response.json()
            except:
                pass

            raise TractionAPIError(
                message=f"Request failed with status {response.status_code}",
                status_code=response.status_code,
                data=error_data,
            )

        except requests.exceptions.RequestException as e:
            raise TractionAPIError(message=str(e))

    # Connection methods

    def test_connection(self) -> Dict:
        """
        Test the API connection

        Returns:
            Connection status
        """
        return self._request("GET", "/status")

    # Custom methods
    def send_traction_request(
        self,
        endpoint: str,
        data: Dict = {},
        params: Dict = None,
    ) -> Dict:
        """
        Send a request to the Traction API

        Args:
            endpoint: API endpoint
            body: Request body
            params: Query parameters

        Returns:
            Response data
        """
        logger.info("Sending request to Traction API.")
        if not endpoint:
            raise ValueError("Endpoint is required")

        if not data:
            logger.warning("Request body is empty")

        if not params:
            logger.warning("Request parameters are empty")

        url = f"{self.base_url}{endpoint}"

        logger.debug(f"Request URL: {url}")
        token = (
            self.authenticate()
        )  # Token pode ser utilizado em mais de uma requisição?? #TODO Testar

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        response = requests.post(url, json=data, params=params, headers=headers)

        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response body: {response.text}")
        return response.json()
