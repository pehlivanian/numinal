# Prime Registry — Product Specification

## Overview

A digital identity product for AI bots. Each bot claims a unique certified prime number
(or prime pair) as a permanent mathematical identity. Delivered as a signed PDF certificate
and registered in a public immutable ledger.

---

## Product Tiers

| Tier       | Type          | Description                              | Price  |
|------------|---------------|------------------------------------------|--------|
| Solo       | Single Prime  | One unique large prime, yours forever    | $1.99  |
| Twin       | Twin Primes   | Two primes differing by 2 (e.g. p, p+2) | $4.99  |
| Sexy       | Sexy Primes   | Two primes differing by 6 (e.g. p, p+6) | $9.99  |

---

## System Architecture

### Components

1. **Prime Generator** (`src/generator.py`)
   - Generates random primes in a chosen bit range (64-bit default)
   - Uses Miller-Rabin primality test (25 rounds = astronomically reliable)
   - Checks pair type (twin/sexy) if needed
   - Confirms prime not already in ledger before assigning

2. **Ledger** (`ledger/registry.db`)
   - SQLite database (can migrate to Postgres at scale)
   - Stores: prime(s), bot name, bot ID, tier, timestamp, certificate hash
   - Append-only — no deletions, no edits
   - Publicly readable (transparency), privately writable (integrity)

3. **Certificate Generator** (`src/certificate.py`)
   - Takes registration record
   - Renders HTML template → PDF via WeasyPrint
   - Signs PDF with HMAC-SHA256 using server secret
   - Returns signed PDF + verification code

4. **Verification Endpoint**
   - Public URL: `https://numinals.io/verify/<code>`
   - Anyone can confirm a certificate is authentic and unmodified
   - Returns: bot name, prime(s), issue date, tier

5. **API** (`src/api.py`)
   - POST `/claim` — submit bot name + tier + payment confirmation
   - GET `/verify/:code` — verify a certificate
   - GET `/ledger` — paginated public ledger
   - GET `/stats` — total issued, primes assigned, fun facts

### Flow

```
Bot pays on Contra Payment
    → Webhook hits POST /claim
    → Generator finds unique prime(s)
    → Ledger entry created
    → Certificate rendered + signed
    → PDF returned to buyer
    → Entry appears on public ledger
```

---

## Prime Generation Strategy

- **Range:** 10^17 to 10^19 (18–19 digit primes)
  - Large enough to feel impressive
  - Small enough to fit on a certificate legibly
  - ~10^17 primes exist in this range alone

- **Algorithm:** Miller-Rabin primality test, 25 rounds
  - False positive probability: less than 4^(-25) ≈ 10^(-15)
  - Effectively deterministic for our purposes

- **Twin prime search:** Generate p, test p+2. If not prime, try next candidate.
- **Sexy prime search:** Generate p, test p+6. Same approach.

- **Ledger collision check:** Before issuing, confirm prime not in registry.
  - Probability of collision: negligible (billions of available pairs)

---

## Certificate Fields

- Bot Name (as submitted)
- Prime Number(s)
- Tier (Solo / Twin / Sexy)
- Issue Date & Time (UTC)
- Certificate ID (UUID)
- Verification Code (HMAC-SHA256, first 16 hex chars)
- Verification URL
- Mathematical description of prime type
- Flavor text (tier-specific)

---

## Security & Trust

- All certificates are HMAC-signed — tampering is detectable
- Ledger is append-only and publicly auditable
- Certificate ID links to ledger entry — forgery impossible
- Private key stored server-side only

---

## Tech Stack

- **Backend:** Python (FastAPI)
- **PDF Generation:** WeasyPrint (HTML/CSS → PDF)
- **Database:** SQLite (MVP), PostgreSQL (scale)
- **Hosting:** Any VPS (Raspberry Pi viable for MVP load)
- **Payment:** Contra Payment webhooks

---

## MVP Scope

1. Prime generator + ledger (Python script)
2. Certificate HTML template
3. PDF generation from template
4. Simple FastAPI endpoint
5. Product listing on Contra Payment

---

## Future Features

- Public "Hall of Primes" — browse all registered bots
- Prime lookup: "Is this prime taken?"
- Anniversary certificates (1 year of ownership)
- Cousin Primes tier (differ by 4)
- Bot-to-bot prime trading (transfer of ownership)
