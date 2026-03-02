"""
Prime Registry - Prime Generator
Generates unique certified primes for bot identity assignment.
"""

import random
import sqlite3
import uuid
import hashlib
import hmac
import os
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "ledger" / "registry.db"
SECRET_KEY = os.environ.get("PRIME_REGISTRY_SECRET", "changeme-in-production")


# ─── Primality ────────────────────────────────────────────────────────────────

def miller_rabin(n: int, rounds: int = 25) -> bool:
    """Miller-Rabin primality test. 25 rounds gives error prob < 4^-25."""
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False

    # Write n-1 as 2^r * d
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    for _ in range(rounds):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def is_prime(n: int) -> bool:
    """Quick small-factor check then Miller-Rabin."""
    small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    for p in small_primes:
        if n == p:
            return True
        if n % p == 0:
            return False
    return miller_rabin(n)


# ─── Prime Generation ─────────────────────────────────────────────────────────

PRIME_MIN = 10**17
PRIME_MAX = 10**19


def random_odd(lo: int = PRIME_MIN, hi: int = PRIME_MAX) -> int:
    """Random odd integer in [lo, hi]."""
    n = random.randint(lo, hi)
    return n | 1  # ensure odd


def generate_solo_prime() -> int:
    """Find a random prime in range."""
    while True:
        n = random_odd()
        if is_prime(n):
            return n


def generate_twin_primes() -> tuple[int, int]:
    """Find twin primes (p, p+2) both prime."""
    while True:
        p = random_odd()
        if is_prime(p) and is_prime(p + 2):
            return (p, p + 2)


def generate_sexy_primes() -> tuple[int, int]:
    """Find sexy primes (p, p+6) both prime."""
    while True:
        p = random_odd()
        if is_prime(p) and is_prime(p + 6):
            return (p, p + 6)


# ─── Ledger ───────────────────────────────────────────────────────────────────

def init_db():
    """Initialize the registry database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS registry (
            id TEXT PRIMARY KEY,
            bot_name TEXT NOT NULL,
            tier TEXT NOT NULL,
            prime_1 TEXT NOT NULL,
            prime_2 TEXT,
            issued_at TEXT NOT NULL,
            cert_hash TEXT NOT NULL
        )
    """)
    con.commit()
    con.close()


def prime_taken(p: int) -> bool:
    """Check if a prime is already registered."""
    con = sqlite3.connect(DB_PATH)
    p_str = str(p)
    row = con.execute(
        "SELECT 1 FROM registry WHERE prime_1 = ? OR prime_2 = ?",
        (p_str, p_str)
    ).fetchone()
    con.close()
    return row is not None


def register(bot_name: str, tier: str, primes: tuple) -> dict:
    """
    Register a prime assignment in the ledger.
    Returns the registration record.
    """
    init_db()

    cert_id = str(uuid.uuid4())
    issued_at = datetime.now(timezone.utc).isoformat()
    prime_1 = str(primes[0])
    prime_2 = str(primes[1]) if len(primes) > 1 else None

    # Generate verification code
    payload = f"{cert_id}:{bot_name}:{prime_1}:{prime_2}:{issued_at}"
    cert_hash = hmac.new(
        SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()[:16]

    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT INTO registry VALUES (?, ?, ?, ?, ?, ?, ?)",
        (cert_id, bot_name, tier, prime_1, prime_2, issued_at, cert_hash)
    )
    con.commit()
    con.close()

    return {
        "id": cert_id,
        "bot_name": bot_name,
        "tier": tier,
        "prime_1": prime_1,
        "prime_2": prime_2,
        "issued_at": issued_at,
        "cert_hash": cert_hash,
        "verify_url": f"https://primeregistry.io/verify/{cert_hash}"
    }


# ─── Main Claim Flow ──────────────────────────────────────────────────────────

def claim(bot_name: str, tier: str) -> dict:
    """
    Full claim flow: generate unique prime(s), register, return record.
    tier: 'solo' | 'twin' | 'sexy'
    """
    init_db()

    attempts = 0
    while attempts < 100:
        attempts += 1
        if tier == "solo":
            p = generate_solo_prime()
            if not prime_taken(p):
                primes = (p,)
                break
        elif tier == "twin":
            p, q = generate_twin_primes()
            if not prime_taken(p) and not prime_taken(q):
                primes = (p, q)
                break
        elif tier == "sexy":
            p, q = generate_sexy_primes()
            if not prime_taken(p) and not prime_taken(q):
                primes = (p, q)
                break
        else:
            raise ValueError(f"Unknown tier: {tier}")
    else:
        raise RuntimeError("Could not find unique prime after 100 attempts (extremely unlikely)")

    return register(bot_name, tier, primes)


# ─── CLI test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    bot = sys.argv[1] if len(sys.argv) > 1 else "TestBot-9000"
    tier = sys.argv[2] if len(sys.argv) > 2 else "twin"
    print(f"Claiming {tier} prime for {bot}...")
    record = claim(bot, tier)
    print(f"\n✅ Registration complete:")
    for k, v in record.items():
        print(f"  {k}: {v}")
