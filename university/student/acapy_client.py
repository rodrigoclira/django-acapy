# acapy_client.py

import json
import requests
import logging
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AcapyClient:
    """Client for interacting with the Flask ACAPY Controller API"""

    def __init__(
        self,
        base_url: str = "http://localhost:5000",
        api_key: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize the ACAPY client

        Args:
            base_url: Base URL of the Flask ACAPY controller
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        """
        Make a request to the ACAPY controller API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint without leading slash
            data: Optional request body for POST/PUT requests
            params: Optional query parameters

        Returns:
            Parsed JSON response as dictionary

        Raises:
            Exception: If the request fails
        """
        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        url = f"{self.base_url}/{endpoint}"

        try:
            logger.debug(f"Making {method} request to {url}")
            if method.upper() == "GET":
                response = requests.get(
                    url, headers=headers, params=params, timeout=self.timeout
                )
            elif method.upper() == "POST":
                response = requests.post(
                    url, headers=headers, json=data, params=params, timeout=self.timeout
                )
            elif method.upper() == "PUT":
                response = requests.put(
                    url, headers=headers, json=data, params=params, timeout=self.timeout
                )
            elif method.upper() == "DELETE":
                response = requests.delete(
                    url, headers=headers, params=params, timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Raise an exception for HTTP errors
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to ACAPY controller: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_message = e.response.json()
                    logger.error(f"ACAPY controller error: {error_message}")
                except json.JSONDecodeError:
                    error_message = e.response.text
                    logger.error(f"ACAPY controller non-JSON error: {error_message}")

            raise Exception(f"ACAPY controller request failed: {str(e)}")

    # ======================================
    # Agent Status Functions
    # ======================================

    def get_status(self) -> Dict:
        """Get agent status"""
        return self._make_request("GET", "status")

    # ======================================
    # Connection Management Functions
    # ======================================

    def list_connections(self) -> Dict:
        """List all connections"""
        return self._make_request("GET", "connections")

    def get_connection(self, connection_id: str) -> Dict:
        """Get a specific connection by ID"""
        if not connection_id:
            raise ValueError("Connection ID is required")

        return self._make_request("GET", f"connections/{connection_id}")

    def create_invitation(
        self,
        alias: Optional[str] = None,
        auto_accept: bool = True,
        multi_use: bool = False,
        use_public_did: bool = False,
    ) -> Dict:
        """
        Create a new out-of-band invitation

        Args:
            alias: Optional name for the connection
            auto_accept: Whether to auto-accept the connection request
            multi_use: Whether the invitation can be used multiple times
            use_public_did: Whether to use the public DID for the invitation

        Returns:
            Dictionary containing the invitation details
        """
        params = {}
        if alias is not None:
            params["alias"] = alias
        if auto_accept is not None:
            params["auto_accept"] = auto_accept
        if multi_use is not None:
            params["multi_use"] = multi_use

        endpoint = (
            "out-of-band/create-invitation/public"
            if use_public_did
            else "out-of-band/create-invitation"
        )

        # Required parameters for out-of-band protocol
        data = {
            "handshake_protocols": ["https://didcomm.org/didexchange/1.0"],
            "use_public_did": use_public_did,
        }

        return self._make_request("POST", endpoint, data=data, params=params)

    def receive_invitation(self, invitation: Dict, auto_accept: bool = True) -> Dict:
        """
        Receive an out-of-band invitation

        Args:
            invitation: The invitation object
            auto_accept: Whether to auto-accept the invitation

        Returns:
            Dictionary containing the connection details
        """
        if not invitation:
            raise ValueError("Invitation is required")

        params = {"auto_accept": str(auto_accept).lower()}

        return self._make_request(
            "POST", "out-of-band/receive-invitation", data=invitation, params=params
        )

    def accept_invitation(
        self,
        connection_id: str,
        my_label: Optional[str] = None,
        my_endpoint: Optional[str] = None,
    ) -> Dict:
        """
        Accept a connection invitation using DID Exchange protocol

        Args:
            connection_id: The connection ID
            my_label: Optional label for your side of the connection
            my_endpoint: Optional endpoint for your agent

        Returns:
            Dictionary containing the updated connection details
        """
        if not connection_id:
            raise ValueError("Connection ID is required")

        data = {}
        if my_label:
            data["my_label"] = my_label
        if my_endpoint:
            data["my_endpoint"] = my_endpoint

        return self._make_request(
            "POST", f"didexchange/{connection_id}/accept-invitation", data=data
        )

    def accept_request(
        self, connection_id: str, my_endpoint: Optional[str] = None
    ) -> Dict:
        """
        Accept a connection request using DID Exchange protocol

        Args:
            connection_id: The connection ID
            my_endpoint: Optional endpoint for your agent

        Returns:
            Dictionary containing the updated connection details
        """
        if not connection_id:
            raise ValueError("Connection ID is required")

        data = {}
        if my_endpoint:
            data["my_endpoint"] = my_endpoint

        return self._make_request(
            "POST", f"didexchange/{connection_id}/accept-request", data=data
        )

    def send_message(self, connection_id: str, content: str) -> Dict:
        """
        Send a basic message to a connection

        Args:
            connection_id: The connection ID
            content: The message content

        Returns:
            Dictionary containing the message details
        """
        if not connection_id:
            raise ValueError("Connection ID is required")

        if not content:
            raise ValueError("Message content is required")

        data = {"content": content}

        return self._make_request(
            "POST", f"connections/{connection_id}/send-message", data=data
        )

    # ======================================
    # Credential Management Functions
    # ======================================

    def issue_credential_v1(
        self, connection_id: str, credential_data: Dict[str, Any]
    ) -> Dict:
        """
        Issue a credential using v1 protocol

        Args:
            connection_id: The connection ID
            credential_data: The credential data

        Returns:
            Dictionary containing the credential exchange details
        """
        if not connection_id:
            raise ValueError("Connection ID is required")

        if not credential_data:
            raise ValueError("Credential data is required")

        # Make sure connection_id is included in the credential data
        if "connection_id" not in credential_data:
            credential_data["connection_id"] = connection_id

        return self._make_request(
            "POST", "issue-credential/create", data=credential_data
        )

    def issue_credential_v2(
        self, connection_id: str, credential_data: Dict[str, Any]
    ) -> Dict:
        """
        Issue a credential using v2 protocol

        Args:
            connection_id: The connection ID
            credential_data: The credential data

        Returns:
            Dictionary containing the credential exchange details
        """
        if not connection_id:
            raise ValueError("Connection ID is required")

        if not credential_data:
            raise ValueError("Credential data is required")

        # Make sure connection_id is included in the credential data
        if "connection_id" not in credential_data:
            credential_data["connection_id"] = connection_id

        return self._make_request(
            "POST", "issue-credential-2.0/create", data=credential_data
        )

    # ======================================
    # Proof Management Functions
    # ======================================

    def request_proof_v1(
        self,
        connection_id: str,
        proof_request: Dict[str, Any],
        comment: Optional[str] = None,
    ) -> Dict:
        """
        Request a proof using v1 protocol

        Args:
            connection_id: The connection ID
            proof_request: The proof request data
            comment: Optional comment

        Returns:
            Dictionary containing the proof exchange details
        """
        if not connection_id:
            raise ValueError("Connection ID is required")

        if not proof_request:
            raise ValueError("Proof request data is required")

        data = {"connection_id": connection_id, "proof_request": proof_request}

        if comment:
            data["comment"] = comment

        return self._make_request("POST", "present-proof/request", data=data)

    def request_proof_v2(
        self,
        connection_id: str,
        proof_request: Dict[str, Any],
        comment: Optional[str] = None,
    ) -> Dict:
        """
        Request a proof using v2 protocol

        Args:
            connection_id: The connection ID
            proof_request: The proof request data
            comment: Optional comment

        Returns:
            Dictionary containing the proof exchange details
        """
        if not connection_id:
            raise ValueError("Connection ID is required")

        if not proof_request:
            raise ValueError("Proof request data is required")

        data = {
            "connection_id": connection_id,
            "presentation_request": {"indy": proof_request},
        }

        if comment:
            data["comment"] = comment

        return self._make_request("POST", "present-proof-2.0/request", data=data)
