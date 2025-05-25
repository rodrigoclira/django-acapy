import datetime
import json
import logging

import requests
from student import webhook
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from student.traction_django import get_traction_client

from .EnumState import StateModelEnum
from .forms import UserRegistrationForm
from .models import ConnectionState
from .util import generate_qrcode

logger = logging.getLogger(__name__)


@login_required
def home(request):
    context = {}

    return render(request, "student/home.html", context)


@login_required
def issue_credential(request):
    context = {}

    invitation = ""
    connection_id = ""
    invitation_url = ""

    try:
        payload = {"handshake_protocols": ["didexchange/1.1"], "use_public_did": False}
        invi_params = {
            "auto_accept": "true",
            "multi_use": "false",
            "create_unique_did": "false",
        }

        _client = get_traction_client()
        invitation_data = _client.send_traction_request(
            endpoint="/connections/create-invitation", data=payload, params=invi_params
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


@login_required
def presentation_request(request):
    logger.info("Sending presentation request")
    context = {}

    # Check if the user has an existing connection state
    if request.method == "POST":
        state_model = ConnectionState.objects.filter(user=request.user).last()

        # {
        #     "presentation_request": {
        #         "indy": {
        #             "name": "Proof of Education",
        #             "version": "1.0",
        #             "requested_attributes": {
        #                 "0_name_uuid": {
        #                     "name": "name",
        #                     "restrictions": [{"schema_name": "degree schema"}],
        #                 },
        #                 "0_date_uuid": {
        #                     "name": "date",
        #                     "restrictions": [{"schema_name": "degree schema"}],
        #                 },
        #                 "0_degree_uuid": {
        #                     "name": "degree",
        #                     "restrictions": [{"schema_name": "degree schema"}],
        #                 },
        #             },
        #             "requested_predicates": {
        #                 "0_birthdate_dateint_GE_uuid": {
        #                     "name": "birthdate_dateint",
        #                     "p_type": "<=",
        #                     "p_value": 20070525,
        #                     "restrictions": [{"schema_name": "degree schema"}],
        #                 }
        #             },
        #         }
        #     },
        #     "trace": False,
        #     "connection_id": "3c8ff292-1481-47ac-9fba-1c3456ab1438",
        # }

        if state_model:
            logger.info(f"Using existing state model: {state_model}")
            data = {
                "presentation_request": {
                    "indy": {
                        "name": "Proof of Individuality",
                        "version": "1.0",
                        "requested_attributes": {
                            "0_given_name_uuid": {
                                "name": "given_name",
                                "restrictions": [
                                    {
                                        "cred_def_id": settings.TRACTION_CREDENTIAL_DEFINITION_ID
                                    }
                                ],
                            },
                            "0_family_name_uuid": {
                                "name": "family_name",
                                "restrictions": [
                                    {
                                        "cred_def_id": settings.TRACTION_CREDENTIAL_DEFINITION_ID
                                    }
                                ],
                            },
                        },
                        "requested_predicates": {
                            "not_expired": {
                                "name": "expires",
                                "p_type": ">=",
                                "p_value": datetime.date.today()
                                .isoformat()
                                .replace("-", ""),
                                "restrictions": [
                                    {
                                        "cred_def_id": settings.TRACTION_CREDENTIAL_DEFINITION_ID
                                    }
                                ],
                            }
                        },
                    }
                },
                "trace": False,
                "connection_id": state_model.connection_id,
            }

            old_data = {
                "connection_id": state_model.connection_id,
                "auto_verify": False,
                "auto_remove": False,
                "trace": True,
                "comment": "Please present your credential",
                "goal_code": "present-credential",
                "presentation_request": {
                    "anoncreds": {
                        "name": "proof-request",
                        "nonce": "1234567890",
                        "version": "1.0",
                        "requested_attributes": {
                            "demo_attributes": {
                                "names": ["given_name", "family_name"],
                                "restrictions": [
                                    {
                                        "cred_def_id": settings.TRACTION_CREDENTIAL_DEFINITION_ID
                                    }
                                ],
                            }
                        },
                        "requested_predicates": {
                            "not_expired": {
                                "name": "expires",
                                "p_type": ">=",
                                "p_value": datetime.date.today()
                                .isoformat()
                                .replace(
                                    "-", ""
                                ),  # Number.parseInt(new Date().toISOString().substring(0, 10).replace(/-/g, '')),
                                "restrictions": [
                                    {
                                        "cred_def_id": settings.TRACTION_CREDENTIAL_DEFINITION_ID
                                    }
                                ],
                            }
                        },
                    },
                },
            }

            _client = get_traction_client()
            send_request_data = _client.send_traction_request(
                endpoint="/present-proof-2.0/send-request", data=data
            )
            logger.info(send_request_data)

            state_model.presentation_exchange_id = send_request_data.get("pres_ex_id")
            state_model.save()
            context = {"show_request": False}
    else:
        context = {"show_request": True}

    return render(request, "student/request-credential.html", context)


@csrf_exempt
@require_http_methods(["POST"])
def handle_topic(request, topic):
    """Handle incoming messages for a specific topic"""
    logger.info(f"Handling topic: {topic}")

    # Process the request based on the topic
    match topic:
        case "connections":
            return webhook.handle_webhook_connections(request)
        case "issue_credential_v2_0":
            return webhook.handle_webhook_issue_credential_v2_0(request)
        case "issue_credential_v2_0_indy":
            return webhook.handle_webhook_issue_credential_v2_0_indy(request)
        case "issue_cred_rev":
            return webhook.handle_webhook_issue_cred_rev(request)
        # case "present_proof_v2_0":
        #     return webhook.handle_webhook_present_proof(request)
        # case "endorse_transaction":
        #     return webhook.handle_webhook_endorse_transaction(request)
        case "ping":
            return webhook.handle_webhook_ping(request)
        case _:
            return HttpResponse("Topic not found", status=404)
    # Add more cases as needed for other topics
    # Uncomment the following lines if you want to handle specific topics
    # elif topic == "connections":
    # if topic == "connections":
    #     return webhook.handle_webhook_connections(request)
    # elif topic == "issue_credential_v2_0":
    #     return webhook.handle_webhook_issue_credential_v2_0(request)
    # elif topic == "present_proof_v2_0":
    #     return webhook.handle_webhook_present_proof(request)
    # elif topic == "endorse_transaction":
    #     return webhook.handle_webhook_endorse_transaction(request)
    # elif topic == "ping":
    #     return webhook.handle_webhook_ping(request)
    # else:
    #     return HttpResponse("Topic not found", status=404)


## Webhook endpoints ##
@csrf_exempt
@require_http_methods(["POST"])
def webhook_connections(request):
    """Handle connection webhook"""
    return webhook.handle_webhook_connections(request)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_issue_credential_v2_0(request):
    """Handle issue credential webhook"""
    return webhook.handle_webhook_issue_credential_v2_0(request)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_present_proof(request):
    """Handle present proof webhook"""
    return webhook.handle_webhook_present_proof(request)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_endorse_transaction(request):
    """Handle endorse transaction webhook"""
    return webhook.handle_webhook_endorse_transaction(request)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_ping(request):
    """Handle ping webhook"""
    return webhook.handle_webhook_ping(request)
