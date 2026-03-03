"""
Prime Registry - FastAPI Backend
Handles claims, verification, and public ledger.

Install: pip install fastapi uvicorn jinja2 weasyprint
Run:     uvicorn api:app --host 0.0.0.0 --port 8000
"""

import sqlite3
from pathlib import Path
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
sys.path.insert(0, str(Path(__file__).parent))
from generator import claim, init_db, DB_PATH
from certificate import render_certificate
from contra_webhook import handle_contra_webhook
from stripe_checkout import router as stripe_router

app = FastAPI(
    title="Prime Registry API",
    description="Unique prime number identity for bots.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(stripe_router, prefix="")

PRICES = {
    "solo": 1.99,
    "twin": 4.99,
    "sexy": 9.99,
}

TIER_NAMES = {
    "solo": "Solo Prime",
    "twin": "Twin Primes",
    "sexy": "Sexy Primes",
}


# ─── Models ───────────────────────────────────────────────────────────────────

class ClaimRequest(BaseModel):
    bot_name: str
    tier: str  # solo | twin | sexy
    payment_ref: str  # Contra Payment reference ID


class ClaimResponse(BaseModel):
    success: bool
    cert_id: str
    bot_name: str
    tier: str
    prime_1: str
    prime_2: str | None
    issued_at: str
    cert_hash: str
    verify_url: str
    pdf_url: str


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "Prime Registry",
        "tagline": "Mathematical identity for the computational age.",
        "tiers": PRICES,
        "endpoints": ["/claim", "/verify/{code}", "/ledger", "/stats"]
    }


@app.post("/claim")
def claim_prime(req: ClaimRequest):
    """
    Claim a unique prime for a bot.
    In production: verify payment_ref against Contra Payment API first.
    """
    tier = req.tier.lower()
    if tier not in PRICES:
        raise HTTPException(400, f"Invalid tier '{tier}'. Choose: solo, twin, sexy")

    bot_name = req.bot_name.strip()
    if not bot_name or len(bot_name) > 100:
        raise HTTPException(400, "bot_name must be 1-100 characters")

    try:
        record = claim(bot_name, tier)
    except Exception as e:
        raise HTTPException(500, f"Prime generation failed: {e}")

    return {
        "success": True,
        **record,
        "pdf_url": f"/certificate/{record['cert_hash']}.pdf"
    }


@app.get("/certificate/{cert_hash}.pdf")
def get_certificate(cert_hash: str):
    """Download certificate PDF by verification code."""
    init_db()
    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT * FROM registry WHERE cert_hash = ?", (cert_hash,)
    ).fetchone()
    con.close()

    if not row:
        raise HTTPException(404, "Certificate not found")

    record = {
        "id": row[0],
        "bot_name": row[1],
        "tier": row[2],
        "prime_1": row[3],
        "prime_2": row[4],
        "issued_at": row[5],
        "cert_hash": row[6],
        "verify_url": f"https://numinals.io/verify/{row[6]}"
    }

    pdf = render_certificate(record)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="prime-{cert_hash[:8]}.pdf"'
        }
    )


@app.get("/verify/{cert_hash}")
def verify_certificate(cert_hash: str):
    """Verify a certificate is authentic and retrieve its details."""
    init_db()
    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT * FROM registry WHERE cert_hash = ?", (cert_hash,)
    ).fetchone()
    con.close()

    if not row:
        return {"valid": False, "message": "Certificate not found in registry"}

    return {
        "valid": True,
        "cert_id": row[0],
        "bot_name": row[1],
        "tier": row[2],
        "tier_name": TIER_NAMES.get(row[2], row[2]),
        "prime_1": row[3],
        "prime_2": row[4],
        "issued_at": row[5],
    }


@app.get("/ledger")
def public_ledger(page: int = 1, per_page: int = 50):
    """Browse the public registry of all issued primes."""
    init_db()
    offset = (page - 1) * per_page
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT id, bot_name, tier, prime_1, prime_2, issued_at FROM registry "
        "ORDER BY issued_at DESC LIMIT ? OFFSET ?",
        (per_page, offset)
    ).fetchall()
    total = con.execute("SELECT COUNT(*) FROM registry").fetchone()[0]
    con.close()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "entries": [
            {
                "cert_id": r[0],
                "bot_name": r[1],
                "tier": r[2],
                "prime_1": r[3],
                "prime_2": r[4],
                "issued_at": r[5],
            }
            for r in rows
        ]
    }


@app.post("/webhook/contra")
async def contra_webhook(request: Request):
    """Contra Payment webhook — called after successful purchase."""
    return await handle_contra_webhook(request)


@app.get("/stats")
def stats():
    """Fun stats about the registry."""
    init_db()
    con = sqlite3.connect(DB_PATH)
    total = con.execute("SELECT COUNT(*) FROM registry").fetchone()[0]
    by_tier = con.execute(
        "SELECT tier, COUNT(*) FROM registry GROUP BY tier"
    ).fetchall()
    con.close()

    return {
        "total_issued": total,
        "by_tier": {row[0]: row[1] for row in by_tier},
        "primes_available": "Effectively infinite (10^17 range contains ~10^15 primes)",
        "twin_prime_conjecture": "Unproven. We believe there are infinitely many.",
    }
