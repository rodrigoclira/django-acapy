from django.http import HttpResponse
from django.conf import settings
import json
import logging
from .models import ConnectionState
from .traction_django import get_traction_client
from .EnumState import StateModelEnum

logger = logging.getLogger(__name__)


def handle_webhook_connections(request):
    """
    Handle webhook events for connection topics.
    """
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

    data = body = {
        "connection_id": state_model.connection_id,
        "comment": f"Offer on cred def id {settings.TRACTION_CREDENTIAL_DEFINITION_ID}",
        "auto_remove": False,
        "credential_preview": {
            "@type": "https://didcomm.org/issue-credential/2.0/credential-preview",
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
        "filter": {"indy": {"cred_def_id": settings.TRACTION_CREDENTIAL_DEFINITION_ID}},
        "trace": False,
    }

    # old_data = {
    #     "auto_issue": settings.CREDENTIAL_AUTO_ISSUE,
    #     "auto_remove": False,
    #     "connection_id": body.get("connection_id"),
    #     "cred_def_id": settings.TRACTION_CREDENTIAL_DEFINITION_ID,
    #     "comment": f"Offer on cred def id {settings.TRACTION_CREDENTIAL_DEFINITION_ID}",
    #     "trace": True,
    #     "filter": {"indy": {"cred_def_id": settings.TRACTION_CREDENTIAL_DEFINITION_ID}},
    #     "credential_preview": {
    #         "@type": "https://didcomm.org/issue-credential/2.0/credential-preview",
    #         "attributes": [
    #             {
    #                 "name": "given_name",
    #                 "value": state_model.user.first_name,
    #             },
    #             {
    #                 "name": "family_name",
    #                 "value": state_model.user.last_name,
    #             },
    #             {
    #                 "name": "expires",
    #                 "value": settings.CREDENTIAL_DATA.get("expires"),
    #             },
    #         ],
    #     },
    # }

    # Create a credential offer
    _client = get_traction_client()

    _client.send_traction_request(
        f"/connections/{state_model.connection_id}/send-message",
        {
            "content": "Agora que a conexão foi estabelecida, você receberá uma credencial do JEMS na sua carteira"
        },
    )

    _client.send_traction_request(
        endpoint="/issue-credential-2.0/send-offer", data=data
    )

    state_model.state = StateModelEnum.OFFER_SENT.value
    state_model.save()

    return HttpResponse(status=200)


def webhook_issue_credential(request):
    body = json.loads(request.body)
    state = body.get("state")
    credential_exchange_id = body["credential_exchange_id"]
    print(state, credential_exchange_id)

    # state_model = ConnectionState.objects.filter(
    #     connection_id=body.get("connection_id")
    # ).first()

    # prev_state = state_model.cred_state.get(credential_exchange_id)
    # if prev_state == state:
    #     return  # ignore
    # self.cred_state[credential_exchange_id] = state


def webhook_issue_credential_v2_0(request):
    """
    Handle webhook events for issue credential v2.0 topics.
    """
    # Check authorization
    if request.headers.get("x-api-key") != "demo-issuance":
        return HttpResponse(status=401)

    body = json.loads(request.body)

    state_model = ConnectionState.objects.filter(
        connection_id=body.get("connection_id")
    ).first()

    # # If state = abandoned then user declined
    # if (
    #     body.get("state") == "abandoned"
    #     and state_model.state == StateModelEnum.OFFER_SENT.value
    # ):
    #     logger.info("User declined offer.")

    # # If state = credential_acked or credential_issued then user received the credential in their wallet
    # if body.get("state") in [
    #     "credential_acked",
    #     "credential_issued",
    # ] and state_model.state in [
    #     StateModelEnum.OFFER_SENT.value,
    #     StateModelEnum.CREDENTIAL_ISSUED.value,
    # ]:
    #     state_model.revocation_registry_id = body.get("revocation_registry_id") or ""
    #     state_model.revocation_id = body.get("revocation_id") or ""
    #     state_model.save()
    #     logger.info("Issuance complete.")

    # # If state = request_received then we received the credential request
    # if (
    #     body.get("state") == "request_received"
    #     and state_model.state == StateModelEnum.OFFER_SENT.value
    # ):
    #     # If we're not auto-issuing the credential then we must manually issue
    #     if not body.get("auto_issue"):
    #         logger.info("Issuing credential.")
    #         # Create a credential offer
    #         _client = get_traction_client()
    #         # send_traction_request(
    #         _client.send_traction_request(
    #             f"/issue-credential/records/{body.get('credential_exchange_id')}/issue"
    #         )
    #     state_model.state = StateModelEnum.CREDENTIAL_ISSUED.value
    #     state_model.save()
    cred_ex_id = body["cred_ex_id"]
    if body.get("state") == "request_received":
        print("#17 Issue credential to X")
        # issue credential based on offer preview in cred ex record
        _client = get_traction_client()

        _client.send_traction_request(
            f"/issue-credential-2.0/records/{cred_ex_id}/issue",
            {"comment": f"Issuing credential, exchange {cred_ex_id}"},
        )
    elif body.get("state") == "done":
        pass
        # Logic moved to detail record specific handler

    elif body.get("state") == "abandoned":
        logger.info("Credential exchange abandoned")
        logger.info("Problem report message:", body.get("error_msg"))
    return HttpResponse(status=200)


def handle_webhook_present_proof(request):
    body = json.loads(request.body)

    state_model = ConnectionState.objects.filter(
        connection_id=body.get("connection_id")
    ).first()

    if (
        state_model is None
        or state_model.presentation_exchange_id is None
        or state_model.presentation_exchange_id != body.get("pres_ex_id")
    ):
        return HttpResponse(status=200)

    if body.get("state") == "verified":
        logger.info("User presented successfully.")
        state_model.presentation_exchange_id = ""
        state_model.save()
    elif body.get("state") == "abandoned":
        logger.info("User declined presentation.")
        state_model.presentation_exchange_id = ""
        state_model.save()

    return HttpResponse(status=200)


def handle_webhook_endorse_transaction(request):
    body = json.loads(request.body)

    logger.info(body)

    # Process the body as needed
    # For example, you might want to log it or save it to the database

    return HttpResponse(status=200)


def handle_webhook_ping(request):
    """
    Handle ping webhook events.
    """
    # Check authorization
    if request.headers.get("x-api-key") != "demo-issuance":
        return HttpResponse(status=401)

    body = json.loads(request.body)

    logger.info("Ping received: %s", body)

    # Respond with a 200 OK status
    return HttpResponse(status=200)
