import io
import base64
import json
import qrcode
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm
from django.conf import settings
import requests

# Import the ACAPY client
from .acapy_client import AcapyClient
import logging

logger = logging.getLogger(__name__)

ACAPY_CONTROLLER_URL = getattr(
    settings, "ACAPY_CONTROLLER_URL", "http://localhost:5000"
)
acapy_client = AcapyClient(base_url=ACAPY_CONTROLLER_URL)


@login_required
def home(request):
    context = {
        "teste": "Olá",
    }

    return render(request, "student/home.html", context)


@login_required
def issue_badge(request):
    context = {
        "teste": "Olá",
    }

    invitation = ""
    connection_id = ""
    invitation_url = ""

    try:
        invitation_data = acapy_client.create_invitation(
            alias="badge connection",
            auto_accept=False,
            multi_use=False,
            use_public_did=False,
        )

        # Extract the invitation and connection_id
        invitation = invitation_data.get("invitation")
        connection_id = invitation_data.get("connection_id")
        invitation_url = invitation_data.get("invitation_url")

    except requests.exceptions.HTTPError as err:
        logger.error(err)
    except Exception as err:
        logger.error(err)

    if not invitation:
        return render(request, "student/badge.html", {"is_expired": True})

    # Store the connection_id in the session for later use
    request.session["connection_id"] = connection_id

    # Format based on what's available
    if invitation_url:
        # If we have a URL, use it directly
        qr_content = invitation_url
    else:
        # Otherwise, use the full invitation JSON
        qr_content = json.dumps(invitation)

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)

    # Create an image from the QR code
    img = qr.make_image(fill_color="black", back_color="white")

    # Save the image to a bytes buffer
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Convert the image to a base64 string to display in HTML
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Response context
    context = {
        "connection_id": connection_id,
        "qr_code_img": f"data:image/png;base64,{img_base64}",
        "invitation_url": invitation_url,
        "invitation_json": json.dumps(invitation, indent=4),
    }

    return render(request, "student/badge.html", context)


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
