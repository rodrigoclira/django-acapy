from flask import Flask, request, jsonify
import requests
import json
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# ACAPY Configuration
ACAPY_ADMIN_URL = os.getenv("ACAPY_ADMIN_URL", "http://localhost:8021")
ACAPY_ADMIN_API_KEY = os.getenv("ACAPY_ADMIN_API_KEY", "")
FABER_ENDPOINT = os.getenv("FABER_ENDPOINT", "http://localhost:8020")


# Helper function for ACAPY API calls
def acapy_admin_request(method, path, data=None, params=None):
    """Make a request to the ACAPY Admin API"""
    url = f"{ACAPY_ADMIN_URL}{path}"
    headers = {"Content-Type": "application/json"}

    # Add API key if configured
    if ACAPY_ADMIN_API_KEY:
        headers["X-API-KEY"] = ACAPY_ADMIN_API_KEY

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"ACAPY request error: {e}")
        raise


# Routes
@app.route("/status", methods=["GET"])
def get_status():
    """Get agent status"""
    try:
        status = acapy_admin_request("GET", "/status")
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/connections", methods=["GET"])
def list_connections():
    """List all connections"""
    try:
        # Get both connection types
        connections = acapy_admin_request("GET", "/connections")

        # Optionally, try to get DID Exchange connections too
        try:
            didexchange = acapy_admin_request("GET", "/didexchange")
            # Merge the results if needed
            if "results" in connections and "results" in didexchange:
                connections["results"].extend(didexchange["results"])
        except Exception as de:
            logger.warning(f"Could not fetch didexchange connections: {de}")

        return jsonify(connections)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/out-of-band/create-invitation", methods=["POST"])
def create_invitation():
    """Create a new out-of-band connection invitation"""
    try:
        # Set up parameters
        params = {}

        # Required parameters for out-of-band protocol
        data = {
            "handshake_protocols": ["https://didcomm.org/didexchange/1.0"],
            "use_public_did": False,
        }

        # Optional parameters
        if request.json:
            if "alias" in request.json:
                params["alias"] = request.json["alias"]
            if "auto_accept" in request.json:
                params["auto_accept"] = request.json["auto_accept"]
            if "multi_use" in request.json:
                params["multi_use"] = request.json["multi_use"]

        invitation = acapy_admin_request(
            "POST", "/out-of-band/create-invitation", data=data, params=params
        )
        return jsonify(invitation)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/out-of-band/create-invitation/public", methods=["POST"])
def create_public_invitation():
    """Create a new out-of-band connection invitation using public DID"""
    try:
        # Set up parameters
        params = {}

        # Required parameters for out-of-band protocol with public DID
        data = {
            "handshake_protocols": ["https://didcomm.org/didexchange/1.0"],
            "use_public_did": True,
        }

        # Optional parameters
        if request.json:
            if "alias" in request.json:
                params["alias"] = request.json["alias"]
            if "auto_accept" in request.json:
                params["auto_accept"] = request.json["auto_accept"]
            if "multi_use" in request.json:
                params["multi_use"] = request.json["multi_use"]

        invitation = acapy_admin_request(
            "POST", "/out-of-band/create-invitation", data=data, params=params
        )
        return jsonify(invitation)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/out-of-band/receive-invitation", methods=["POST"])
def receive_invitation():
    """Receive an out-of-band connection invitation"""
    try:
        if not request.json:
            return jsonify({"error": "No invitation provided"}), 400

        invitation = request.json
        params = {"auto_accept": request.args.get("auto_accept", "true")}

        connection = acapy_admin_request(
            "POST", "/out-of-band/receive-invitation", data=invitation, params=params
        )
        return jsonify(connection)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/didexchange/<connection_id>/accept-invitation", methods=["POST"])
def accept_invitation(connection_id):
    """Accept a connection invitation using DID Exchange protocol"""
    try:
        params = {}
        if request.json:
            if "my_endpoint" in request.json:
                params["my_endpoint"] = request.json["my_endpoint"]
            if "my_label" in request.json:
                params["my_label"] = request.json["my_label"]

        response = acapy_admin_request(
            "POST", f"/didexchange/{connection_id}/accept-invitation", params=params
        )
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/didexchange/<connection_id>/accept-request", methods=["POST"])
def accept_request(connection_id):
    """Accept a connection request using DID Exchange protocol"""
    try:
        params = {}
        if request.json:
            if "my_endpoint" in request.json:
                params["my_endpoint"] = request.json["my_endpoint"]

        response = acapy_admin_request(
            "POST", f"/didexchange/{connection_id}/accept-request", params=params
        )
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/connections/<connection_id>", methods=["GET"])
def get_connection(connection_id):
    """Get a specific connection by ID"""
    try:
        connection = acapy_admin_request("GET", f"/connections/{connection_id}")
        return jsonify(connection)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/connections/<connection_id>/send-message", methods=["POST"])
def send_message(connection_id):
    """Send a basic message to a connection"""
    try:
        if not request.json or "content" not in request.json:
            return jsonify({"error": "No message content provided"}), 400

        message_content = request.json["content"]
        message_data = {"content": message_content}

        response = acapy_admin_request(
            "POST", f"/connections/{connection_id}/send-message", data=message_data
        )
        return jsonify({"status": "Message sent", "message": message_content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/issue-credential/create", methods=["POST"])
def create_credential():
    """Create and issue a credential"""
    try:
        if not request.json:
            return jsonify({"error": "No credential data provided"}), 400

        # For simplicity, assuming the request contains all necessary credential data
        credential_data = request.json

        # Create and issue the credential
        credential = acapy_admin_request(
            "POST", "/issue-credential/send", data=credential_data
        )
        return jsonify(credential)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/issue-credential-2.0/create", methods=["POST"])
def create_credential_v2():
    """Create and issue a credential using v2 protocol"""
    try:
        if not request.json:
            return jsonify({"error": "No credential data provided"}), 400

        # For simplicity, assuming the request contains all necessary credential data
        credential_data = request.json

        # Create and issue the credential using v2 protocol
        credential = acapy_admin_request(
            "POST", "/issue-credential-2.0/send", data=credential_data
        )
        return jsonify(credential)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/present-proof/request", methods=["POST"])
def request_proof():
    """Request a proof from a connection"""
    try:
        if not request.json:
            return jsonify({"error": "No proof request data provided"}), 400

        # For simplicity, assuming the request contains all necessary proof request data
        proof_request_data = request.json

        # Send the proof request
        proof_request = acapy_admin_request(
            "POST", "/present-proof/send-request", data=proof_request_data
        )
        return jsonify(proof_request)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/present-proof-2.0/request", methods=["POST"])
def request_proof_v2():
    """Request a proof from a connection using v2 protocol"""
    try:
        if not request.json:
            return jsonify({"error": "No proof request data provided"}), 400

        # For simplicity, assuming the request contains all necessary proof request data
        proof_request_data = request.json

        # Send the proof request using v2 protocol
        proof_request = acapy_admin_request(
            "POST", "/present-proof-2.0/send-request", data=proof_request_data
        )
        return jsonify(proof_request)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/webhooks/topic/<topic>", methods=["POST"])
def handle_webhook(topic):
    """Handle incoming webhooks from ACAPY"""
    try:
        logger.info(f"Received webhook for topic: {topic}")
        payload = request.json
        logger.info(f"Webhook payload: {payload}")

        # You can implement specific handling for different webhook topics here
        if topic == "connections" or topic == "didexchange":
            # Handle connection/didexchange state changes
            connection_id = payload.get("connection_id")
            state = payload.get("state")
            logger.info(f"Connection {connection_id} changed state to {state}")

            # If connection is active/completed, notify Faber
            if state == "active" or state == "completed":
                try:
                    notify_faber(connection_id, "connection_active")
                except Exception as notify_error:
                    logger.error(f"Failed to notify Faber: {notify_error}")

        elif topic == "issue_credential" or topic == "issue_credential_v2_0":
            # Handle credential issuance state changes
            credential_exchange_id = payload.get("credential_exchange_id")
            state = payload.get("state")
            logger.info(
                f"Credential exchange {credential_exchange_id} changed state to {state}"
            )

        elif topic == "present_proof" or topic == "present_proof_v2_0":
            # Handle proof presentation state changes
            presentation_exchange_id = payload.get("presentation_exchange_id")
            state = payload.get("state")
            logger.info(
                f"Presentation exchange {presentation_exchange_id} changed state to {state}"
            )

        elif topic == "out_of_band":
            # Handle out-of-band events
            invitation_id = payload.get("invitation_id")
            state = payload.get("state")
            logger.info(
                f"Out-of-band invitation {invitation_id} changed state to {state}"
            )

        # Return success response
        return jsonify({"status": "Success", "topic": topic})
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return jsonify({"error": str(e)}), 500


def notify_faber(connection_id, event_type):
    """Notify the Faber agent of an event"""
    notification = {
        "connection_id": connection_id,
        "event_type": event_type,
        "timestamp": datetime.now().isoformat(),
    }

    try:
        response = requests.post(
            f"{FABER_ENDPOINT}/notifications",
            headers={"Content-Type": "application/json"},
            json=notification,
        )
        response.raise_for_status()
        logger.info(f"Successfully notified Faber of {event_type} event")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to notify Faber: {e}")
        raise


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
