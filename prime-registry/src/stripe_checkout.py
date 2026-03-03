"""
Stripe Checkout + Webhook handler for Numinals prime registry.
"""

import os
import stripe
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from generator import claim
from certificate import save_certificate
from certificate_png import save_png
from pathlib import Path
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

router = APIRouter()

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

PRICE_IDS = {
    "solo":  os.environ.get("STRIPE_PRICE_SOLO",  "price_1T6sVm42uBw4qg1lCmZUlwox"),
    "twin":  os.environ.get("STRIPE_PRICE_TWIN",  "price_1T6sVm42uBw4qg1lHxKYEdvA"),
    "sexy":  os.environ.get("STRIPE_PRICE_SEXY",  "price_1T6sVn42uBw4qg1li35BahEq"),
}

BASE_URL = os.environ.get("REGISTRY_BASE_URL", "https://numinals.io")


class CheckoutRequest(BaseModel):
    tier: str
    bot_name: str


@router.post("/checkout")
async def create_checkout(req: CheckoutRequest):
    tier = req.tier.lower()
    if tier not in PRICE_IDS:
        raise HTTPException(status_code=400, detail="Invalid tier")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": PRICE_IDS[tier], "quantity": 1}],
        mode="payment",
        success_url=f"{BASE_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{BASE_URL}/#claim",
        metadata={"tier": tier, "bot_name": req.bot_name},
        custom_fields=[],
    )
    return {"url": session.url}


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        tier = session["metadata"].get("tier", "solo")
        bot_name = session["metadata"].get("bot_name", "Anonymous")
        email = session.get("customer_details", {}).get("email", "")

        # Generate prime and certificates
        record = claim(bot_name, tier)

        certs_dir = Path("certificates")
        certs_dir.mkdir(exist_ok=True)

        pdf_path = save_certificate(record, certs_dir / f"{record['cert_hash']}.pdf")
        png_path = save_png(record, certs_dir / f"{record['cert_hash']}.png")

        # Send email if we have SMTP configured
        if email:
            _send_certificate_email(email, bot_name, tier, record, pdf_path, png_path)

    return Response(status_code=200)


def _send_certificate_email(email, bot_name, tier, record, pdf_path, png_path):
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    from_email = os.environ.get("FROM_EMAIL", "registry@numinals.io")

    if not smtp_user or not smtp_pass:
        return  # SMTP not configured yet

    tier_names = {"solo": "Solo Prime", "twin": "Twin Primes", "sexy": "Sexy Primes"}
    tier_name = tier_names.get(tier, tier)

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = email
    msg["Subject"] = f"Your Numinals Certificate — {bot_name} · {tier_name}"

    prime_display = record["prime_1"]
    if record.get("prime_2"):
        prime_display += f" / {record['prime_2']}"

    body = f"""Your certified prime is ready.

Bot: {bot_name}
Tier: {tier_name}
Prime(s): {prime_display}
Certificate ID: {record['cert_hash']}

Verify at: {record['verify_url']}

PDF and PNG certificates are attached.

— The Numinals Registry
"""
    msg.attach(MIMEText(body, "plain"))

    for path in [pdf_path, png_path]:
        with open(path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={path.name}")
            msg.attach(part)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, email, msg.as_string())
    except Exception as e:
        print(f"Email send failed: {e}")
