import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from student.traction_django import get_traction_client

from .models import ConnectionState
from .forms import UserRegistrationForm
from .util import generate_qrcode
from django.conf import settings
import requests
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
import logging
from .EnumState import StateModelEnum

logger = logging.getLogger(__name__)


@login_required
def home(request):
    context = {
        "teste": "Olá",
    }

    return render(request, "student/home.html", context)


@login_required
def issue_credential(request):
    context = {
        "teste": "Olá",
    }

    invitation = ""
    connection_id = ""
    invitation_url = ""

    try:
        _client = get_traction_client()
        invitation_data = _client.send_traction_request(
            endpoint="/connections/create-invitation"
        )
        logger.info(invitation_data)

        # Extract the invitation and connection_id
        invitation = invitation_data.get("invitation")
        connection_id = invitation_data.get("connection_id")
        invitation_url = invitation_data.get("invitation_url")
        logger.info(connection_id)

    except requests.exceptions.HTTPError as err:
        logger.error(err)
    except Exception as err:
        logger.error(err)

    if not invitation:
        return render(request, "student/credential.html", {"is_expired": True})

    # Store the connection_id in the session for later use
    request.session["connection_id"] = connection_id

    # Format based on what's available
    if invitation_url:
        # If we have a URL, use it directly
        qr_content = invitation_url
    else:
        # Otherwise, use the full invitation JSON
        qr_content = json.dumps(invitation)

    img_base64 = generate_qrcode(
        qr_content,
        version=1,
        box_size=10,
        border=4,
        fill_color="black",
        back_color="white",
    )

    ConnectionState.objects.create(
        connection_id=connection_id,
        revocation_registry_id="",
        revocation_id="",
        presentation_exchange_id="",
        state=StateModelEnum.CONNECTION_INVITATION.value,
        user=request.user,
    )

    # Response context
    context = {
        "connection_id": connection_id,
        "qr_code_img": f"data:image/png;base64,{img_base64}",
        "invitation_url": invitation_url,
        "invitation_json": json.dumps(invitation, indent=4),
    }

    return render(request, "student/credential.html", context)


def register(request):
    if request.method == "POST":
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data["password"])
            new_user.save()
            return render(request, "student/registered.html", {"new_user": new_user})
    else:
        user_form = UserRegistrationForm()

    return render(request, "student/register.html", {"user_form": user_form})


## Webhook endpoints ##
@csrf_exempt
@require_http_methods(["POST"])
def webhook_connections(request):
    """Handle connection webhook"""
    # Check authorization
    if request.headers.get("x-api-key") != "demo-issuance":
        return HttpResponse(status=401)

    body = json.loads(request.body)

    logger.info(body.get("connection_id"))
    logger.info(body.get("state"))
    state_model = ConnectionState.objects.filter(
        connection_id=body.get("connection_id")
    ).first()

    # Unless the connection is made (state = active) and we're in the correct state, we just wait
    if body.get("state") != "active" or state_model.state != "CONNECTION INVITATION":
        return HttpResponse(status=200)

    # # Now that the connection is made, offer the credential
    logger.info("Sending credential offer.")

    # Create a credential offer
    _client = get_traction_client()
    _client.send_traction_request(
        endpoint="/issue-credential/send-offer",
        body={
            "auto_issue": settings.CREDENTIAL_AUTO_ISSUE,
            "auto_remove": False,
            "connection_id": body.get("connection_id"),
            "cred_def_id": settings.TRACTION_CREDENTIAL_DEFINITION_ID,
            "trace": False,
            "credential_preview": {
                "@type": "issue-credential/1.0/credential-preview",
                "attributes": [
                    {
                        "name": "given_name",
                        "value": state_model.user.first_name,
                    },
                    {
                        "name": "family_name",
                        "value": state_model.user.last_name,
                    },
                    {
                        "name": "expires",
                        "value": settings.CREDENTIAL_DATA.get("expires"),
                    },
                ],
            },
        },
    )

    state_model.state = StateModelEnum.OFFER_SENT.value
    state_model.save()

    return HttpResponse(status=200)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_issue_credential(request):
    """Handle issue credential webhook"""
    # Check authorization
    if request.headers.get("x-api-key") != "demo-issuance":
        return HttpResponse(status=401)

    body = json.loads(request.body)

    state_model = ConnectionState.objects.filter(
        connection_id=body.get("connection_id")
    ).first()

    # If state = abandoned then user declined
    if body.get("state") == "abandoned" and state_model.state == "OFFER SENT":
        logger.info("User declined.")

    # If state = credential_acked or credential_issued then user received the credential in their wallet
    if body.get("state") in [
        "credential_acked",
        "credential_issued",
    ] and state_model.state in ["OFFER SENT", "CREDENTIAL ISSUED"]:
        logger.info("Issuance complete.")

    # If state = request_received then we received the credential request
    if body.get("state") == "request_received" and state_model.state == "OFFER SENT":
        # If we're not auto-issuing the credential then we must manually issue
        if not body.get("auto_issue"):
            logger.info("Issuing credential.")
            # Create a credential offer
            _client = get_traction_client()
            # send_traction_request(
            _client.send_traction_request(
                f"/issue-credential/records/{body.get('credential_exchange_id')}/issue"
            )

    return HttpResponse(status=200)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_present_proof(request):
    """Handle present proof webhook"""
    body = json.loads(request.body)

    # if (
    #     app_state.presentation_exchange_id is None
    #     or app_state.presentation_exchange_id != body.get("presentation_exchange_id")
    # ):
    #     return HttpResponse(status=200)

    if body.get("state") == "verified":
        logger.info("User presented successfully.")
    elif body.get("state") == "abandoned":
        logger.info("User declined presentation.")

    return HttpResponse(status=200)
