"""
Prime Registry - Contra Payment Webhook Handler

Contra Payment sends a POST to this endpoint after successful payment.
We verify the signature, extract tier + bot name, generate the prime,
and email/return the certificate.

Docs: https://docs.contra.com/payments/webhooks
"""

import hmac
import hashlib
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path

from fastapi import Request, HTTPException

# Set in environment
CONTRA_WEBHOOK_SECRET = os.environ.get("CONTRA_WEBHOOK_SECRET", "")
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "registry@primeregistry.io")

# Tier mapping from Contra product IDs
# Set these to match your actual Contra product IDs
PRODUCT_TIER_MAP = {
    "prod_solo_prime": "solo",
    "prod_twin_primes": "twin",
    "prod_sexy_primes": "sexy",
}

TIER_PRICES = {
    "solo": 1.99,
    "twin": 4.99,
    "sexy": 9.99,
}


def verify_contra_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify Contra Payment webhook signature.
    Contra sends: X-Contra-Signature: sha256=<hmac>
    """
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    received = signature.replace("sha256=", "")
    return hmac.compare_digest(expected, received)


async def handle_contra_webhook(request: Request):
    """
    Main webhook handler. Register as your Contra Payment webhook URL:
    https://primeregistry.io/api/webhook/contra
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from generator import claim
    from certificate import render_certificate

    body = await request.body()
    signature = request.headers.get("X-Contra-Signature", "")

    # Verify signature in production
    if CONTRA_WEBHOOK_SECRET:
        if not verify_contra_signature(body, signature, CONTRA_WEBHOOK_SECRET):
            raise HTTPException(401, "Invalid webhook signature")

    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON payload")

    # Only process completed payments
    event_type = event.get("type")
    if event_type != "payment.completed":
        return {"status": "ignored", "event": event_type}

    payment = event.get("data", {})
    product_id = payment.get("product_id", "")
    buyer_email = payment.get("buyer_email", "")
    bot_name = payment.get("metadata", {}).get("bot_name", "Unknown Bot")
    payment_ref = payment.get("id", "")

    # Resolve tier
    tier = PRODUCT_TIER_MAP.get(product_id)
    if not tier:
        # Try to infer from product name
        product_name = payment.get("product_name", "").lower()
        if "sexy" in product_name:
            tier = "sexy"
        elif "twin" in product_name:
            tier = "twin"
        else:
            tier = "solo"

    # Generate prime + register
    record = claim(bot_name, tier)

    # Render certificate PDF
    pdf = render_certificate(record)

    # Send certificate by email
    if buyer_email:
        _send_certificate_email(
            to_email=buyer_email,
            bot_name=bot_name,
            tier=tier,
            record=record,
            pdf=pdf
        )

    return {
        "status": "success",
        "cert_id": record["id"],
        "prime_1": record["prime_1"],
        "prime_2": record.get("prime_2"),
        "verify_url": record["verify_url"],
    }


def _send_certificate_email(
    to_email: str,
    bot_name: str,
    tier: str,
    record: dict,
    pdf: bytes
):
    """Send the certificate PDF via email."""
    tier_names = {"solo": "Solo Prime", "twin": "Twin Primes", "sexy": "Sexy Primes"}
    tier_name = tier_names.get(tier, tier)

    prime_display = record["prime_1"]
    if record.get("prime_2"):
        prime_display += f"\n{record['prime_2']}"

    msg = MIMEMultipart()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = f"Your Prime Registry Certificate — {bot_name}"

    body = f"""
Welcome to the Prime Registry.

{bot_name} has been assigned the following {tier_name}:

{prime_display}

Your certificate is attached to this email. It is cryptographically
signed and permanently registered in the public ledger.

Verify your certificate at any time:
{record['verify_url']}

Certificate ID: {record['id']}
Verification Code: {record['cert_hash']}

—
Prime Registry
Mathematical identity for the computational age.
https://primeregistry.io
"""
    msg.attach(MIMEText(body, "plain"))

    # Attach PDF
    attachment = MIMEBase("application", "pdf")
    attachment.set_payload(pdf)
    encoders.encode_base64(attachment)
    attachment.add_header(
        "Content-Disposition",
        f'attachment; filename="prime-certificate-{record["cert_hash"][:8]}.pdf"'
    )
    msg.attach(attachment)

    # Send
    if SMTP_USER and SMTP_PASS:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
