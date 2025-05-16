"""
TractionAPI - A Python library for connecting to Traction services

This library provides methods to authenticate and interact with
the Traction API for various operations including customer management,
opportunity tracking, and reporting.
"""

import requests
import json
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urlencode


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
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

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

    # Customer methods

    def get_customers(self, page: int = 1, limit: int = 20, **kwargs) -> Dict:
        """
        Get all customers

        Args:
            page: Page number
            limit: Items per page
            **kwargs: Additional filter parameters

        Returns:
            List of customers
        """
        params = {"page": page, "limit": limit, **kwargs}
        return self._request("GET", "/customers", params=params)

    def get_customer(self, customer_id: str) -> Dict:
        """
        Get a customer by ID

        Args:
            customer_id: Customer ID

        Returns:
            Customer data
        """
        if not customer_id:
            raise ValueError("Customer ID is required")

        return self._request("GET", f"/customers/{customer_id}")

    def create_customer(self, customer_data: Dict) -> Dict:
        """
        Create a new customer

        Args:
            customer_data: Customer data

        Returns:
            Created customer data
        """
        if not customer_data:
            raise ValueError("Customer data is required")

        return self._request("POST", "/customers", data=customer_data)

    def update_customer(self, customer_id: str, customer_data: Dict) -> Dict:
        """
        Update a customer

        Args:
            customer_id: Customer ID
            customer_data: Customer data to update

        Returns:
            Updated customer data
        """
        if not customer_id:
            raise ValueError("Customer ID is required")

        if not customer_data:
            raise ValueError("Customer data is required")

        return self._request("PUT", f"/customers/{customer_id}", data=customer_data)

    def delete_customer(self, customer_id: str) -> Dict:
        """
        Delete a customer

        Args:
            customer_id: Customer ID

        Returns:
            Deletion status
        """
        if not customer_id:
            raise ValueError("Customer ID is required")

        return self._request("DELETE", f"/customers/{customer_id}")

    # Opportunity methods

    def get_opportunities(
        self, page: int = 1, limit: int = 20, status: Optional[str] = None, **kwargs
    ) -> Dict:
        """
        Get all opportunities

        Args:
            page: Page number
            limit: Items per page
            status: Filter by status
            **kwargs: Additional filter parameters

        Returns:
            List of opportunities
        """
        params = {"page": page, "limit": limit, **kwargs}
        if status:
            params["status"] = status

        return self._request("GET", "/opportunities", params=params)

    def get_opportunity(self, opportunity_id: str) -> Dict:
        """
        Get an opportunity by ID

        Args:
            opportunity_id: Opportunity ID

        Returns:
            Opportunity data
        """
        if not opportunity_id:
            raise ValueError("Opportunity ID is required")

        return self._request("GET", f"/opportunities/{opportunity_id}")

    def create_opportunity(self, opportunity_data: Dict) -> Dict:
        """
        Create a new opportunity

        Args:
            opportunity_data: Opportunity data

        Returns:
            Created opportunity data
        """
        if not opportunity_data:
            raise ValueError("Opportunity data is required")

        return self._request("POST", "/opportunities", data=opportunity_data)

    def update_opportunity(self, opportunity_id: str, opportunity_data: Dict) -> Dict:
        """
        Update an opportunity

        Args:
            opportunity_id: Opportunity ID
            opportunity_data: Opportunity data to update

        Returns:
            Updated opportunity data
        """
        if not opportunity_id:
            raise ValueError("Opportunity ID is required")

        if not opportunity_data:
            raise ValueError("Opportunity data is required")

        return self._request(
            "PUT", f"/opportunities/{opportunity_id}", data=opportunity_data
        )

    # Report methods

    def get_sales_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: Optional[str] = None,
    ) -> Dict:
        """
        Get sales report

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            group_by: Group by field

        Returns:
            Sales report data
        """
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if group_by:
            params["group_by"] = group_by

        return self._request("GET", "/reports/sales", params=params)

    def get_customer_activity_report(
        self,
        customer_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict:
        """
        Get customer activity report

        Args:
            customer_id: Customer ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Customer activity report data
        """
        if not customer_id:
            raise ValueError("Customer ID is required")

        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        return self._request(
            "GET", f"/reports/customer-activity/{customer_id}", params=params
        )
