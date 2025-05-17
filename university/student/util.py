import base64
import io
import qrcode


def generate_qrcode(
    qr_content, version=1, box_size=10, border=4, fill_color="black", back_color="white"
):
    """
    Generate a QR code image from the given content.
    Args:
        qr_content (str): The content to encode in the QR code.
        version (int): Version of the QR code (1-40).
        box_size (int): Size of each box in the QR code.
        border (int): Thickness of the border (minimum is 4).
        fill_color (str): Color of the QR code.
        back_color (str): Background color of the QR code.
    Returns:
        str: Base64 encoded string of the QR code image.
    """

    qr = qrcode.QRCode(
        version=version,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=border,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)

    # Create an image from the QR code
    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    # Save the image to a bytes buffer
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Convert the image to a base64 string to display in HTML
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return img_base64
