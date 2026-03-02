# Prime Registry

> Mathematical identity for the computational age.

A digital product that assigns bots unique certified prime numbers as permanent identity tokens.

## Product Tiers

| Tier | Type | Price |
|------|------|-------|
| Solo | Single prime | $1.99 |
| Twin | Twin primes (differ by 2) | $4.99 |
| Sexy | Sexy primes (differ by 6) | $9.99 |

## Quick Start

```bash
pip install jinja2 weasyprint fastapi uvicorn

# Generate a prime (CLI test)
python3 src/generator.py "MyBot" "twin"

# Generate a certificate PDF
python3 src/certificate.py "MyBot" "sexy"

# Run the API server
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

## Files

```
prime-registry/
├── src/
│   ├── generator.py      # Prime generation + ledger
│   ├── certificate.py    # PDF certificate renderer
│   ├── certificate.html  # Certificate HTML/CSS template
│   └── api.py            # FastAPI backend
├── ledger/
│   └── registry.db       # SQLite ledger (auto-created)
└── docs/
    ├── SPEC.md            # Full technical specification
    └── LISTING.md         # Product listing copy for Contra Payment
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/claim` | Claim a prime for a bot |
| GET | `/verify/{code}` | Verify a certificate |
| GET | `/certificate/{code}.pdf` | Download certificate PDF |
| GET | `/ledger` | Public registry browser |
| GET | `/stats` | Registry statistics |

## Live Test (generator)

```
Claiming twin prime for Quincy...

✅ Registration complete:
  prime_1: 9713092013072591177
  prime_2: 9713092013072591179
  cert_hash: c134db2641daaf96
  verify_url: https://primeregistry.io/verify/c134db2641daaf96
```
